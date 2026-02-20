import os
import re
import subprocess
import threading
import time
import json
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Tested and works with:
# - Python 3.13.7
# - FFmpeg (the version in LosslessCut 3.68.0)

# --- Settings ---
CUTLIST_SUFFIX = ".cutlist.txt"
LOG_FILENAME_TEMPLATE = "ffmpeg_log-{timestamp}.log"
CONFIG_FILE = "exactcut_config.json"

# --- Helper Functions ---
def parse_timecode_cutlist(cutlist_path):
    segments = []
    pattern = re.compile(r'start_time=([\d.]+),duration=([\d.]+)')
    with open(cutlist_path, 'r') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                segments.append((float(match.group(1)), float(match.group(2))))
    return segments

def run_ffmpeg_command(command, log_file, stop_event):
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1, shell=True) as process:
        for line in process.stdout:
            log_file.write(line)
            log_file.flush()
            if stop_event.is_set():
                process.terminate()
                break
        process.wait()
        return process.returncode

# --- Tooltip Helper ---
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left', background="#ffffe0", relief='solid', borderwidth=1, font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

# --- Configuration Management ---
def load_config():
    config_path = Path(__file__).parent / CONFIG_FILE
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_config(config):
    config_path = Path(__file__).parent / CONFIG_FILE
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

# --- Main Application Class ---
class FFmpegCutterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ExactCut FFmpeg Cutter (MS Precision)")

        # Defaults (MS)
        self.start_offset_var = tk.IntVar(value=133)
        self.end_offset_var = tk.IntVar(value=1000)
        
        self.audio_mode_var = tk.StringVar(value="Copy")
        self.audio_bitrate_var = tk.StringVar(value="128")
        self.container_mode_var = tk.StringVar(value="Same as source")

        self.progress_var = tk.DoubleVar()
        self.time_remaining_var = tk.StringVar(value="")
        self.stop_event = threading.Event()

        self.selected_dir_var = tk.StringVar()
        self.load_last_directory()

        self.build_ui()
        self.add_top_buttons() # Changed from add_help_button

    def load_last_directory(self):
        config = load_config()
        last_dir = config.get("last_directory", str(Path(__file__).parent))
        if Path(last_dir).is_dir():
            self.selected_dir_var.set(last_dir)
        else:
            self.selected_dir_var.set(str(Path(__file__).parent))

    def save_last_directory(self, path):
        config = {"last_directory": path}
        save_config(config)

    def browse_directory(self):
        initial_dir = self.selected_dir_var.get() if Path(self.selected_dir_var.get()).is_dir() else str(Path(__file__).parent)
        chosen_dir = filedialog.askdirectory(initialdir=initial_dir, title="Select Folder Containing Video and Cutlist Files")
        if chosen_dir:
            self.selected_dir_var.set(chosen_dir)
            self.save_last_directory(chosen_dir)

    def build_ui(self):
        padding = {"padx": 5, "pady": 5}
        frame = ttk.Frame(self.root)
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Folder Selection
        ttk.Label(frame, text="Source Folder:").grid(row=0, column=0, sticky=tk.W, **padding)
        self.dir_entry = ttk.Entry(frame, textvariable=self.selected_dir_var, state="readonly", width=50)
        self.dir_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), **padding)
        
        browse_button = ttk.Button(frame, text="Browse", command=self.browse_directory)
        browse_button.grid(row=0, column=3, sticky=tk.W, **padding)

        # Offsets in Milliseconds
        ttk.Label(frame, text="Start Offset (ms):").grid(row=1, column=0, sticky=tk.W, **padding)
        self.start_entry = ttk.Entry(frame, textvariable=self.start_offset_var, width=6)
        self.start_entry.grid(row=1, column=1, sticky=tk.W, **padding)
        ToolTip(self.start_entry, "Safety buffer in milliseconds (e.g., 150 = 0.15s).")

        ttk.Label(frame, text="End Offset (ms):").grid(row=1, column=2, sticky=tk.W, **padding)
        self.end_entry = ttk.Entry(frame, textvariable=self.end_offset_var, width=6)
        self.end_entry.grid(row=1, column=3, sticky=tk.W, **padding)
        ToolTip(self.end_entry, "End buffer in milliseconds (e.g., 1000 = 1.0s).")

        # Audio Settings
        ttk.Label(frame, text="Audio Mode:").grid(row=2, column=0, sticky=tk.W, **padding)
        self.audio_menu = ttk.Combobox(frame, textvariable=self.audio_mode_var, values=["Copy", "AAC", "MP3", "WAV"], state="readonly", width=10)
        self.audio_menu.grid(row=2, column=1, sticky=tk.W, **padding)
        self.audio_menu.bind("<<ComboboxSelected>>", self.on_audio_mode_change)

        self.bitrate_label = ttk.Label(frame, text="Bitrate (kbps):")
        self.bitrate_label.grid(row=2, column=2, sticky=tk.W, **padding)

        self.bitrate_menu = ttk.Combobox(frame, textvariable=self.audio_bitrate_var, values=["128", "160", "192"], state="readonly", width=6)
        self.bitrate_menu.grid(row=2, column=3, sticky=tk.W, **padding)

        # Container Settings
        ttk.Label(frame, text="Output Container:").grid(row=3, column=0, sticky=tk.W, **padding)
        self.container_menu = ttk.Combobox(frame, textvariable=self.container_mode_var, values=["Same as source", "MP4", "MOV", "MKV"], state="readonly", width=15)
        self.container_menu.grid(row=3, column=1, columnspan=3, sticky=tk.W, **padding)
        self.container_menu.bind("<<ComboboxSelected>>", self.on_container_mode_change)

        # Buttons
        ttk.Button(frame, text="Start Cutting", command=self.start_cutting).grid(row=4, column=0, pady=10)
        ttk.Button(frame, text="Cancel", command=self.cancel_processing).grid(row=4, column=1, pady=10)

        # Progress
        ttk.Progressbar(frame, variable=self.progress_var, maximum=100).grid(row=5, column=0, columnspan=4, sticky="we", **padding)
        ttk.Label(frame, textvariable=self.time_remaining_var).grid(row=6, column=0, columnspan=4, sticky=tk.W, **padding)

        self.on_audio_mode_change()

    def on_audio_mode_change(self, *args):
        self.toggle_bitrate_visibility()
        self.toggle_container_for_wav()

    def on_container_mode_change(self, *args):
        pass

    def toggle_bitrate_visibility(self):
        mode = self.audio_mode_var.get().lower()
        if mode in ["copy", "wav"]:
            self.bitrate_label.grid_remove()
            self.bitrate_menu.grid_remove()
        else:
            self.bitrate_label.grid()
            self.bitrate_menu.grid()

    def toggle_container_for_wav(self):
        if self.audio_mode_var.get() == "WAV":
            if self.container_mode_var.get() != "MKV":
                self.container_mode_var.set("MKV")
            self.container_menu.config(state="disabled")
        else:
            self.container_menu.config(state="readonly")

    def cancel_processing(self):
        self.stop_event.set()

    def start_cutting(self):
        threading.Thread(target=self.process_cutlists).start()

    def process_cutlists(self):
        source_dir = Path(self.selected_dir_var.get())
        if not source_dir.is_dir():
            messagebox.showerror("Error", "Invalid source folder.")
            return

        cutlist_files = [f for f in source_dir.iterdir() if f.name.endswith(CUTLIST_SUFFIX)]
        if not cutlist_files:
            messagebox.showerror("Error", f"No '{CUTLIST_SUFFIX}' files found.")
            return

        timestamp = datetime.now().strftime("%y-%m-%d_%H-%M-%S")
        log_file_path = source_dir / LOG_FILENAME_TEMPLATE.format(timestamp=timestamp)
        
        total_segments = 0
        for cutlist_file in cutlist_files:
            segments = parse_timecode_cutlist(cutlist_file)
            total_segments += len(segments)

        if total_segments == 0:
            messagebox.showinfo("Info", "No valid segments found.")
            return

        self.progress_var.set(0)
        self.time_remaining_var.set("")
        processed_segments = 0
        start_time = time.time()

        with open(log_file_path, "w", encoding="utf-8") as log_file:
            for cutlist_path in cutlist_files:
                if self.stop_event.is_set(): break

                input_file_name = cutlist_path.name.replace(CUTLIST_SUFFIX, "")
                input_file = source_dir / input_file_name
                
                if not input_file.exists():
                    log_file.write(f"Missing input file: {input_file}\n")
                    continue

                segments = parse_timecode_cutlist(cutlist_path)
                
                time_offset_start = self.start_offset_var.get() / 1000.0
                time_offset_end = self.end_offset_var.get() / 1000.0

                output_dir = source_dir / input_file.stem
                output_dir.mkdir(parents=True, exist_ok=True)

                output_container = self.container_mode_var.get()
                ext = input_file.suffix if output_container == "Same as source" else f".{output_container.lower()}"
                
                audio_mode = self.audio_mode_var.get().lower()
                if audio_mode == "copy": audio_flag = "-c:a copy"
                elif audio_mode == "wav": audio_flag = "-c:a pcm_s16le"
                else: audio_flag = f"-c:a {audio_mode} -b:a {self.audio_bitrate_var.get()}k"

                for i, (start_ts, duration) in enumerate(segments):
                    if self.stop_event.is_set(): break

                    adj_start = start_ts + time_offset_start
                    adj_end = start_ts + duration + time_offset_end
                    adj_duration = adj_end - adj_start

                    output_file = output_dir / f"{input_file.stem}_part_{i+1:03d}{ext}"
                    cmd = (
                        f"ffmpeg -ss {adj_start:.6f} -i \"{input_file}\" -t {adj_duration:.6f} "
                        f"-c:v copy {audio_flag} -avoid_negative_ts make_zero \"{output_file}\""
                    )
                    
                    log_file.write(f"Seg {i+1}: {cmd}\n")
                    run_ffmpeg_command(cmd, log_file, self.stop_event)
                    
                    processed_segments += 1
                    self.progress_var.set((processed_segments / total_segments) * 100)
                    
                    elapsed = time.time() - start_time
                    if processed_segments > 0:
                        rate = elapsed / processed_segments
                        remaining = (total_segments - processed_segments) * rate
                        self.time_remaining_var.set(f"Remaining: {int(remaining)}s")

        self.time_remaining_var.set("Done.")
        if not self.stop_event.is_set():
            messagebox.showinfo("Completed", f"Processed {processed_segments} segments.\nLog: {log_file_path.name}")
        self.stop_event.clear()

    # --- NEW: Top Buttons (Help + Calculator) ---
    def add_top_buttons(self):
        # Frame to hold buttons at the top right
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(anchor="ne", padx=10, pady=5)
        
        calc_button = ttk.Button(btn_frame, text="🧮 Calculator", command=self.open_calculator)
        calc_button.pack(side="left", padx=5)

        help_button = ttk.Button(btn_frame, text="? Help", command=self.show_help)
        help_button.pack(side="left")

    # --- NEW: Calculator Logic ---
    def open_calculator(self):
        calc_win = tk.Toplevel(self.root)
        calc_win.title("Frame to MS Calculator")
        calc_win.geometry("260x220")
        
        # Center the window
        x = self.root.winfo_x() + 50
        y = self.root.winfo_y() + 50
        calc_win.geometry(f"+{x}+{y}")

        ttk.Label(calc_win, text="Video FPS:").pack(pady=(10,0))
        fps_entry = ttk.Entry(calc_win, width=10, justify="center")
        fps_entry.pack(pady=2)
        fps_entry.insert(0, "23.976") # Default

        ttk.Label(calc_win, text="Frames to Add:").pack(pady=(5,0))
        frames_entry = ttk.Entry(calc_win, width=10, justify="center")
        frames_entry.pack(pady=2)
        frames_entry.insert(0, "4") # Default

        result_var = tk.StringVar(value="---")
        ttk.Label(calc_win, textvariable=result_var, font=("Segoe UI", 12, "bold"), foreground="#007acc").pack(pady=10)

        def calculate():
            try:
                fps = float(fps_entry.get())
                frames = float(frames_entry.get())
                if fps <= 0: raise ValueError
                ms = (1000.0 / fps) * frames
                result_var.set(f"{int(round(ms))} ms")
            except ValueError:
                result_var.set("Error")

        ttk.Button(calc_win, text="Calculate", command=calculate).pack(pady=5)
        
        # Buttons to apply result to main window
        btn_frame = ttk.Frame(calc_win)
        btn_frame.pack(pady=5)

        def apply_start():
            val = result_var.get().replace(" ms", "")
            if val.isdigit():
                self.start_offset_var.set(int(val))

        def apply_end():
            val = result_var.get().replace(" ms", "")
            if val.isdigit():
                self.end_offset_var.set(int(val))

        ttk.Button(btn_frame, text="Set Start", command=apply_start, width=8).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Set End", command=apply_end, width=8).pack(side="left", padx=2)

    def show_help(self):
        msg = """ExactCut FFmpeg Cutter (MS Precision Edition)
-------------------------------------------------------------
HOW TO USE:
1. Ensure your folder contains video files and corresponding .cutlist.txt files.
2. Select the folder above.
3. Adjust your Millisecond Offsets.
4. Choose Audio/Container settings and click 'Start Cutting'.

-------------------------------------------------------------
UNDERSTANDING OFFSETS (MILLISECONDS):
This tool uses TIME (ms) for maximum precision. 1000 ms = 1 Second.

START OFFSET (The "Seek Nudge"):
- This is NOT a buffer; it pushes the seek point slightly forward.
- Since your cutlists are keyframe-aligned, this 'nudge' ensures 
  FFmpeg snaps to the correct keyframe rather than the previous one.
- Recommended: 100ms to 200ms. (0ms will cause approx 10s of unwanted video in many of the output segments).

END OFFSET (The "Safety Buffer"):
- This adds extra duration to the end of the segment.
- Use this to ensure a scene isn't cut too abruptly.
- Recommended: 1000ms (1 second).

-------------------------------------------------------------
FRAME RATE MS CHEAT SHEET (For 4 Frames):
To calculate a specific number of frames, use the CALCULATOR 
button or the approximate values below:

FRAME RATE (FPS)      1 FRAME DURATION      4 FRAMES (Approx)
-------------------------------------------------------------
  23.976 fps   ---->    41.7 ms            167 ms
  24.000 fps   ---->    41.7 ms            167 ms
  25.000 fps   ---->    40.0 ms            160 ms
  29.970 fps   ---->    33.4 ms            133 ms
  30.000 fps   ---->    33.3 ms            133 ms
  50.000 fps   ---->    20.0 ms             80 ms
  59.940 fps   ---->    16.7 ms             67 ms
  60.000 fps   ---->    16.7 ms             67 ms

Example: 
To add a 4-frame seek nudge for a 60fps video:
4 * 16.7 = ~67 ms. Enter '67' in the Start Offset box.

-------------------------------------------------------------
Audio Modes:
- Copy: Losslessly copies the audio stream. No re-encoding. Bitrate not applicable.
- AAC / MP3: Re-encodes audio to the selected lossy format at a specified bitrate.
- WAV: Re-encodes audio to uncompressed WAV (PCM). Bitrate not applicable.
  *Note: When WAV audio is selected, the output container will automatically be set to MKV,
  as WAV is most reliably supported in the MKV container.*

Configuration:
The last selected folder is automatically saved and loaded.
Other default values can still be changed by editing this file. Look for:

    self.start_offset_var = tk.IntVar(value=133)
    self.end_offset_var = tk.IntVar(value=1000)
    self.audio_mode_var = tk.StringVar(value="Copy")
    self.audio_bitrate_var = tk.StringVar(value="128")
    self.container_mode_var = tk.StringVar(value="Same as source")
"""
        help_win = tk.Toplevel(self.root)
        help_win.title("ExactCut Help")
        help_win.geometry("520x600")
        help_win.transient(self.root) # Keeps help window on top of main app
        
        text_area = tk.Text(help_win, wrap="word", padx=10, pady=10, font=("Consolas", 9))
        text_area.insert("1.0", msg)
        text_area.config(state="disabled") 
        
        scrollbar = ttk.Scrollbar(help_win, command=text_area.yview)
        text_area.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        text_area.pack(side="left", fill="both", expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = FFmpegCutterApp(root)
    root.mainloop()