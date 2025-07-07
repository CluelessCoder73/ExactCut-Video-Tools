import os
import re
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

def parse_timecode_cutlist(cutlist_path):
    segments = []
    segment_pattern = re.compile(r'start_time=([\d.]+),duration=([\d.]+)')
    with open(cutlist_path, 'r') as f:
        for line in f:
            match = segment_pattern.search(line)
            if match:
                start_time = float(match.group(1))
                duration = float(match.group(2))
                segments.append((start_time, duration))
    return segments

def generate_ffmpeg_batch(start_frame_offset, end_frame_offset, audio_mode, audio_bitrate, container_choice):
    script_dir = Path(__file__).parent
    cutlist_suffix = ".cutlist.txt"
    cutlist_files = [f for f in script_dir.iterdir() if f.is_file() and f.name.endswith(cutlist_suffix)]

    if not cutlist_files:
        messagebox.showwarning("No Cutlists Found", f"No files ending in {cutlist_suffix} were found.")
        return

    all_ffmpeg_commands = []
    output_info_messages = []

    for cutlist_path in cutlist_files:
        try:
            with open(cutlist_path, 'r') as f:
                first_line = f.readline()
                fps_match = re.match(r"#\s*fps\s*=\s*([\d.]+)", first_line)
                if not fps_match:
                    raise ValueError
                framerate = float(fps_match.group(1))
        except Exception:
            print(f"Could not read FPS from '{cutlist_path.name}'. Skipping.")
            continue

        time_offset_start = start_frame_offset / framerate
        time_offset_end = end_frame_offset / framerate

        original_video_name = cutlist_path.name.replace(cutlist_suffix, "")
        input_video_file = script_dir / original_video_name
        if not input_video_file.exists():
            print(f"Video file '{original_video_name}' not found. Skipping.")
            continue

        segments = parse_timecode_cutlist(cutlist_path)
        if not segments:
            print(f"No valid segments found in '{cutlist_path.name}'. Skipping.")
            continue

        output_folder = script_dir / input_video_file.stem
        output_folder.mkdir(exist_ok=True)

        for idx, (start_time, duration) in enumerate(segments):
            adjusted_start = start_time + time_offset_start
            adjusted_end = start_time + duration + time_offset_end
            adjusted_duration = adjusted_end - adjusted_start
            if adjusted_duration <= 0:
                continue

            ext = input_video_file.suffix if container_choice == "Same as source" else f".{container_choice.lower()}"
            output_filename = f"{input_video_file.stem}_part_{idx+1:03d}{ext}"
            output_path = output_folder / output_filename

            audio_params = "-c:a copy" if audio_mode == "Copy" else f"-c:a {audio_mode} -b:a {audio_bitrate}k"
            cmd = (
                f'ffmpeg -ss {adjusted_start:.6f} -i "{input_video_file}" '
                f'-t {adjusted_duration:.6f} -c:v copy {audio_params} -avoid_negative_ts make_zero '
                f'"{output_path}" || true'
            )

            all_ffmpeg_commands.append(cmd)
            output_info_messages.append(
                f"  - {output_filename}: start {adjusted_start:.3f}s, duration {adjusted_duration:.3f}s"
            )

    if all_ffmpeg_commands:
        batch_file = script_dir / "run_ffmpeg_cuts.bat"
        with open(batch_file, 'w') as f:
            f.write("@echo off\n")
            f.write("echo Starting FFmpeg cuts...\n\n")
            for msg in output_info_messages:
                f.write(f"echo {msg}\n")
            f.write("\n")
            for cmd in all_ffmpeg_commands:
                f.write(cmd + "\n\n")
            f.write("echo All cuts completed.\npause\n")

        messagebox.showinfo("Success", f"Batch file saved:\n{batch_file.name}")
    else:
        messagebox.showwarning("No Commands Generated", "No FFmpeg commands were generated.")

def launch_gui():
    root = tk.Tk()
    root.title("FFmpeg Cutlist Generator")

    tk.Label(root, text="Start Frame Offset:").pack()
    entry_start = tk.Entry(root)
    entry_start.insert(0, "1")
    entry_start.pack()

    tk.Label(root, text="End Frame Offset:").pack()
    entry_end = tk.Entry(root)
    entry_end.insert(0, "0")
    entry_end.pack()

    tk.Label(root, text="Audio Mode:").pack()
    audio_mode = tk.StringVar(value="Copy")
    audio_menu = ttk.Combobox(root, textvariable=audio_mode, values=["Copy", "aac", "mp3"], state="readonly")
    audio_menu.pack()

    tk.Label(root, text="Audio Bitrate (kbps):").pack()
    bitrate = tk.StringVar(value="128")
    bitrate_menu = ttk.Combobox(root, textvariable=bitrate, values=["128", "160", "192"], state="readonly")
    bitrate_menu.pack()

    tk.Label(root, text="Output Container:").pack()
    container = tk.StringVar(value="Same as source")
    container_menu = ttk.Combobox(root, textvariable=container, values=["Same as source", "mp4", "mkv", "mov"], state="readonly")
    container_menu.pack()

    def on_generate():
        try:
            start_offset = int(entry_start.get())
            end_offset = int(entry_end.get())
            audio = audio_mode.get()
            br = bitrate.get()
            fmt = container.get()
            generate_ffmpeg_batch(start_offset, end_offset, audio, br, fmt)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    tk.Button(root, text="Generate FFmpeg Cutlist", command=on_generate).pack(pady=10)
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
