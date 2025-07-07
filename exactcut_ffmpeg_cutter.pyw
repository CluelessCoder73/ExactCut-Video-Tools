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

# --- Settings ---
CUTLIST_SUFFIX = ".cutlist.txt"
LOG_FILENAME_TEMPLATE = "ffmpeg_log-{timestamp}.log"
CONFIG_FILE = "exactcut_config.json" # New: Configuration file

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

def extract_fps(cutlist_path):
    with open(cutlist_path, 'r') as f:
        first_line = f.readline()
        match = re.match(r"#\s*fps\s*=\s*([\d.]+)", first_line)
        if match:
            return float(match.group(1))
    raise ValueError("FPS not found in cutlist header")

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
    """Loads configuration from the JSON file."""
    config_path = Path(__file__).parent / CONFIG_FILE
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {} # Return empty if file is corrupt
    return {}

def save_config(config):
    """Saves configuration to the JSON file."""
    config_path = Path(__file__).parent / CONFIG_FILE
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

# --- Main Application Class ---
import webbrowser
class FFmpegCutterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ExactCut FFmpeg Cutter")

        self.start_offset_var = tk.IntVar(value=1)
        self.end_offset_var = tk.IntVar(value=0)
        self.audio_mode_var = tk.StringVar(value="Copy")
        self.audio_bitrate_var = tk.StringVar(value="128")
        self.container_mode_var = tk.StringVar(value="Same as source")

        self.progress_var = tk.DoubleVar()
        self.time_remaining_var = tk.StringVar(value="")
        self.stop_event = threading.Event()

        # New: Directory selection variable
        self.selected_dir_var = tk.StringVar()
        self.load_last_directory() # Load last directory on startup

        self.build_ui()
        self.add_help_button()

    def load_last_directory(self):
        config = load_config()
        last_dir = config.get("last_directory", str(Path(__file__).parent))
        if Path(last_dir).is_dir():
            self.selected_dir_var.set(last_dir)
        else:
            self.selected_dir_var.set(str(Path(__file__).parent)) # Default to script directory if last_dir is invalid

    def save_last_directory(self, path):
        config = {"last_directory": path}
        save_config(config)

    def browse_directory(self):
        initial_dir = self.selected_dir_var.get() if Path(self.selected_dir_var.get()).is_dir() else str(Path(__file__).parent)
        chosen_dir = filedialog.askdirectory(initialdir=initial_dir, title="Select Folder Containing Video and Cutlist Files")
        if chosen_dir:
            self.selected_dir_var.set(chosen_dir)
            self.save_last_directory(chosen_dir) # Save the newly selected directory

    def build_ui(self):
        padding = {"padx": 5, "pady": 5}

        frame = ttk.Frame(self.root)
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # New: Directory Selection UI
        ttk.Label(frame, text="Source Folder:").grid(row=0, column=0, sticky=tk.W, **padding)
        self.dir_entry = ttk.Entry(frame, textvariable=self.selected_dir_var, state="readonly", width=50)
        self.dir_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), **padding)
        ToolTip(self.dir_entry, "The folder where cutlist and video files are located.")
        
        browse_button = ttk.Button(frame, text="Browse", command=self.browse_directory)
        browse_button.grid(row=0, column=3, sticky=tk.W, **padding)
        ToolTip(browse_button, "Select the folder containing your video and cutlist files.")


        ttk.Label(frame, text="Start Frame Offset:").grid(row=1, column=0, sticky=tk.W, **padding)
        start_entry = ttk.Entry(frame, textvariable=self.start_offset_var, width=6)
        start_entry.grid(row=1, column=1, sticky=tk.W, **padding)
        ToolTip(start_entry, "Shift the start of each segment forward by this many frames.")

        ttk.Label(frame, text="End Frame Offset:").grid(row=1, column=2, sticky=tk.W, **padding)
        end_entry = ttk.Entry(frame, textvariable=self.end_offset_var, width=6)
        end_entry.grid(row=1, column=3, sticky=tk.W, **padding)
        ToolTip(end_entry, "Shift the end of each segment forward by this many frames.")

        ttk.Label(frame, text="Audio Mode:").grid(row=2, column=0, sticky=tk.W, **padding)
        audio_menu = ttk.Combobox(frame, textvariable=self.audio_mode_var, values=["Copy", "AAC", "MP3"], state="readonly", width=10)
        audio_menu.grid(row=2, column=1, sticky=tk.W, **padding)
        audio_menu.bind("<<ComboboxSelected>>", self.toggle_bitrate_visibility)
        ToolTip(audio_menu, "Choose whether to copy audio (lossless) or re-encode.")

        self.bitrate_label = ttk.Label(frame, text="Bitrate (kbps):")
        self.bitrate_label.grid(row=2, column=2, sticky=tk.W, **padding)

        self.bitrate_menu = ttk.Combobox(frame, textvariable=self.audio_bitrate_var, values=["128", "160", "192"], state="readonly", width=6)
        self.bitrate_menu.grid(row=2, column=3, sticky=tk.W, **padding)
        ToolTip(self.bitrate_menu, "Choose the bitrate to use if re-encoding audio.")

        ttk.Label(frame, text="Output Container:").grid(row=3, column=0, sticky=tk.W, **padding)
        container_menu = ttk.Combobox(frame, textvariable=self.container_mode_var, values=["Same as source", "MP4", "MOV", "MKV"], state="readonly", width=15)
        container_menu.grid(row=3, column=1, columnspan=3, sticky=tk.W, **padding)
        ToolTip(container_menu, "Choose the output file format (container type).")

        ttk.Button(frame, text="Start Cutting", command=self.start_cutting).grid(row=4, column=0, pady=10)
        ttk.Button(frame, text="Cancel", command=self.cancel_processing).grid(row=4, column=1, pady=10)

        ttk.Progressbar(frame, variable=self.progress_var, maximum=100).grid(row=5, column=0, columnspan=4, sticky="we", **padding)
        ttk.Label(frame, textvariable=self.time_remaining_var).grid(row=6, column=0, columnspan=4, sticky=tk.W, **padding)

        self.toggle_bitrate_visibility()

    def toggle_bitrate_visibility(self, *args):
        mode = self.audio_mode_var.get().lower()
        if mode == "copy":
            self.bitrate_label.grid_remove()
            self.bitrate_menu.grid_remove()
        else:
            self.bitrate_label.grid()
            self.bitrate_menu.grid()

    def cancel_processing(self):
        self.stop_event.set()

    def start_cutting(self):
        threading.Thread(target=self.process_cutlists).start()

    def process_cutlists(self):
        # Use the selected directory instead of script_dir
        source_dir = Path(self.selected_dir_var.get())
        if not source_dir.is_dir():
            messagebox.showerror("Invalid Folder", "Please select a valid source folder.")
            return

        cutlist_files = [f for f in source_dir.iterdir() if f.name.endswith(CUTLIST_SUFFIX)]
        if not cutlist_files:
            messagebox.showerror("No Cutlists Found", f"No files ending with '{CUTLIST_SUFFIX}' found in {source_dir}.")
            return

        timestamp = datetime.now().strftime("%y-%m-%d_%H-%M-%S")
        log_file_path = source_dir / LOG_FILENAME_TEMPLATE.format(timestamp=timestamp) # Log file in source dir
        total_segments = 0
        for cutlist_file in cutlist_files:
            segments = parse_timecode_cutlist(cutlist_file)
            total_segments += len(segments)

        if total_segments == 0:
            messagebox.showinfo("No Segments", "No valid segments found in any cutlist.")
            return

        self.progress_var.set(0)
        self.time_remaining_var.set("")
        processed_segments = 0
        start_time = time.time()

        with open(log_file_path, "w", encoding="utf-8") as log_file:
            for cutlist_path in cutlist_files:
                if self.stop_event.is_set():
                    break

                try:
                    framerate = extract_fps(cutlist_path)
                except Exception as e:
                    log_file.write(f"Error reading FPS from {cutlist_path.name}: {e}\n")
                    continue

                input_file_name = cutlist_path.name.replace(CUTLIST_SUFFIX, "")
                input_file = source_dir / input_file_name # Input file in source dir
                if not input_file.exists():
                    log_file.write(f"Missing input file for cutlist {cutlist_path.name}: {input_file}\n")
                    continue

                segments = parse_timecode_cutlist(cutlist_path)
                time_offset_start = self.start_offset_var.get() / framerate
                time_offset_end = self.end_offset_var.get() / framerate

                output_dir = source_dir / input_file.stem # Output directory is now a subfolder of source_dir
                output_dir.mkdir(parents=True, exist_ok=True)

                ext = input_file.suffix if self.container_mode_var.get() == "Same as source" else f".{self.container_mode_var.get().lower()}"
                audio_flag = "-c:a copy" if self.audio_mode_var.get() == "Copy" else f"-c:a {self.audio_mode_var.get().lower()} -b:a {self.audio_bitrate_var.get()}k"

                for i, (start_time_orig, duration_orig) in enumerate(segments):
                    if self.stop_event.is_set():
                        break

                    start_time_adj = start_time_orig + time_offset_start
                    end_time_adj = start_time_orig + duration_orig + time_offset_end
                    duration_adj = end_time_adj - start_time_adj

                    output_file = output_dir / f"{input_file.stem}_part_{i+1:03d}{ext}"
                    cmd = (
                        f"ffmpeg -ss {start_time_adj:.6f} -i \"{input_file}\" -t {duration_adj:.6f} -c:v copy {audio_flag} -avoid_negative_ts make_zero \"{output_file}\""
                    )
                    log_file.write(f"Running: {cmd}\n")

                    return_code = run_ffmpeg_command(cmd, log_file, self.stop_event)
                    log_file.write(f"Exit code: {return_code}\n\n")

                    processed_segments += 1
                    self.progress_var.set((processed_segments / total_segments) * 100)

                    elapsed = time.time() - start_time
                    if processed_segments > 0: # Avoid division by zero
                        rate = elapsed / processed_segments
                        remaining = (total_segments - processed_segments) * rate
                        self.time_remaining_var.set(f"Estimated time remaining: {int(remaining)} sec")
                    else:
                        self.time_remaining_var.set("Calculating...")


        self.time_remaining_var.set("Done.")
        if self.stop_event.is_set():
            messagebox.showinfo("Cancelled", "Processing was cancelled.")
        else:
            messagebox.showinfo("Completed", f"All segments processed. Log saved to:\n{log_file_path}")
        self.stop_event.clear()

    def add_help_button(self):
        help_button = ttk.Button(self.root, text="? Help", command=self.show_help)
        help_button.pack(anchor="ne", padx=10, pady=5)

    def show_help(self):
        help_text = """ExactCut FFmpeg Cutter Help

This tool performs FFmpeg segment cutting based on cutlist files.

How It Works:
- This app now allows you to select a folder containing your *.cutlist.txt files.
- Each cutlist must be generated by `vdscript_to_timecode_cutlist_generator.py`
  which parses VirtualDub .vdscript files and a frame log.
- This app matches each cutlist with its corresponding video file (e.g. myvideo.mkv)
  within the *selected folder*.
- Segments are cut using precise timecodes, and output to a subfolder
  (e.g. /selected_folder/myvideo/) within the *selected folder*.
- All FFmpeg output is saved to a single timestamped log file in the *selected folder*.

Configuration:
The last selected folder is automatically saved and loaded.
Other default values can still be changed by editing this file. Look for:

    self.start_offset_var = tk.IntVar(value=1)
    self.end_offset_var = tk.IntVar(value=0)
    self.audio_mode_var = tk.StringVar(value='Copy')
    self.audio_bitrate_var = tk.StringVar(value='128')
    self.container_mode_var = tk.StringVar(value='Same as source')

Tip:
Use Copy mode to preserve audio. Only adjust bitrate if you’re re-encoding.

Enjoy frame-accurate cutting!"""
        messagebox.showinfo("Help - FFmpeg Cutter", help_text)

# --- Run the Application ---
if __name__ == "__main__":
    root = tk.Tk()
    app = FFmpegCutterApp(root)
    root.mainloop()