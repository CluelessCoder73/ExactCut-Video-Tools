import os
import re
from pathlib import Path

def parse_timecode_cutlist(cutlist_path):
    """Parses a timecode cutlist file and returns a list of (start_time, duration) tuples."""
    segments = []
    # Regex to find lines like 'start_time=X.Y,duration=A.B'
    segment_pattern = re.compile(r'start_time=([\d.]+),duration=([\d.]+)')

    try:
        with open(cutlist_path, 'r') as f:
            for line in f:
                match = segment_pattern.search(line)
                if match:
                    start_time = float(match.group(1))
                    duration = float(match.group(2))
                    segments.append((start_time, duration))
    except FileNotFoundError:
        print(f"Error: Cutlist file not found at '{cutlist_path}'. Please ensure the path is correct.")
    except Exception as e:
        print(f"Error parsing cutlist '{cutlist_path}': {e}")
    return segments

def main():
    print("--- ExactCut Video Tools: Timecode Cutlist to FFmpeg Cutter ---")
    print("This script reads timecode cutlist files and generates FFmpeg commands.")
    print("It produces separate output files for each segment, organized into subfolders.")
    print("-----------------------------------------------------------------")

    script_dir = Path(__file__).parent 
    print(f"Script is running from: '{script_dir}'")
    
    # --- 0. Get user inputs for offsets and frame rate ---
    while True:
        try:
            framerate_str = input("Enter the EXACT frame rate (e.g., 23.976, 25, 29.97, 60) for your video(s) to calculate frame offsets: ")
            framerate = float(framerate_str)
            if framerate <= 0:
                raise ValueError
            break
        except ValueError:
            print("Invalid frame rate. Please enter a positive number (e.g., 23.976).")

    while True:
        try:
            start_frame_offset_str = input("Enter the number of frames to shift the START of each segment forward by (e.g., 0, 5, 10): ")
            start_frame_offset = int(start_frame_offset_str)
            if start_frame_offset < 0:
                raise ValueError
            break
        except ValueError:
            print("Invalid input. Please enter a non-negative integer for the start frame offset.")

    while True:
        try:
            end_frame_offset_str = input("Enter the number of frames to shift the END of each segment forward by (e.g., 0, 5, 10): ")
            end_frame_offset = int(end_frame_offset_str)
            if end_frame_offset < 0:
                raise ValueError
            break
        except ValueError:
            print("Invalid input. Please enter a non-negative integer for the end frame offset.")
            
    time_offset_start = start_frame_offset / framerate
    time_offset_end = end_frame_offset / framerate
    print(f"Calculated start time offset: {time_offset_start:.4f}s, end time offset: {time_offset_end:.4f}s")

    # --- 1. Find .cutlist.txt files ---
    cutlist_suffix = ".cutlist.txt"
    all_files_in_dir = [f for f in script_dir.iterdir() if f.is_file()]
    cutlist_files = []

    print(f"Scanning '{script_dir}' for timecode cutlist files ending with '{cutlist_suffix}'...")
    for f_path in all_files_in_dir:
        if str(f_path.name).endswith(cutlist_suffix):
            cutlist_files.append(f_path)

    if not cutlist_files:
        print(f"No cutlist files found ending with '{cutlist_suffix}' in '{script_dir}'.")
        print("Please ensure you've run 'vdscript_to_timecode_cutlist_generator.py' first.")
        return

    print(f"Found {len(cutlist_files)} '{cutlist_suffix}' file(s).")
    
    all_ffmpeg_commands = []
    output_info_messages = []

    # --- 2. Process each cutlist file ---
    for cutlist_path in cutlist_files:
        print(f"\nProcessing '{cutlist_path.name}'...")
        
        # Derive original video filename (e.g., "my.movie.mkv")
        # from "my.movie.mkv.cutlist.txt"
        original_video_full_name = cutlist_path.name.replace(cutlist_suffix, "")
        input_video_file = script_dir / original_video_full_name

        # Verify the corresponding video file exists
        if not input_video_file.is_file():
            print(f"Warning: Corresponding video file '{input_video_file.name}' not found for '{cutlist_path.name}'. Skipping this cutlist.")
            print(f"  (Expected path: '{input_video_file}')")
            continue

        segments = parse_timecode_cutlist(cutlist_path)
        if not segments:
            print(f"No valid segments found in '{cutlist_path.name}'. Skipping.")
            continue

        # Create output subfolder for this video
        output_folder_name = input_video_file.stem 
        output_subfolder = script_dir / output_folder_name
        output_subfolder.mkdir(parents=True, exist_ok=True) # Create if it doesn't exist

        # Generate FFmpeg commands for this video's segments
        for i, (original_start_time, original_duration) in enumerate(segments):
            
            # Apply offsets
            adjusted_start_time = original_start_time + time_offset_start
            old_end_time = original_start_time + original_duration
            adjusted_end_time = old_end_time + time_offset_end
            adjusted_duration = adjusted_end_time - adjusted_start_time

            # Ensure duration is not negative (though unlikely with forward shifts)
            if adjusted_duration < 0:
                print(f"Warning: Calculated negative duration for segment {i+1}. Skipping.")
                continue

            output_segment_filename = f"{input_video_file.stem}_part_{i+1:03d}{input_video_file.suffix}"
            output_segment_path = output_subfolder / output_segment_filename
            
            # Reverting FFmpeg command to playable version: -ss before -i, keep -avoid_negative_ts make_zero
            command = (
                f'ffmpeg -ss {adjusted_start_time:.6f} -i "{input_video_file}" '
                f'-t {adjusted_duration:.6f} -c copy -avoid_negative_ts make_zero '
                f'"{output_segment_path}" || true' 
            )
            all_ffmpeg_commands.append(command)
            output_info_messages.append(f"  - Generated command for '{input_video_file.name}': segment {i+1} (start {adjusted_start_time:.3f}s, duration {adjusted_duration:.3f}s) -> saved to '{output_segment_path.relative_to(script_dir)}'")

    # --- 3. Write all commands to a single .bat file ---
    if not all_ffmpeg_commands:
        print("No FFmpeg commands were generated for any video. Nothing to do.")
        return

    output_batch_file = script_dir / "run_ffmpeg_cuts.bat"
    try:
        with open(output_batch_file, 'w') as f:
            f.write("@echo off\n")
            f.write("rem FFmpeg cutting commands generated by ExactCut Video Tools\n")
            f.write("rem These commands perform lossless stream copies (-c copy).\n")
            f.write("rem Ensure ffmpeg.exe is in your system PATH or specify its full path (e.g., 'C:\\ffmpeg\\bin\\ffmpeg.exe').\n")
            f.write("rem Note: '|| true' is used to allow the batch file to continue if FFmpeg reports non-fatal errors during stream copy.\n")
            f.write("rem Note: '-ss' is placed BEFORE '-i' for maximum playability, and '-avoid_negative_ts make_zero' is used for timestamp robustness.\n")
            f.write("rem Note: Start and End frame offsets were applied based on user input.\n\n") 
            f.write("echo Starting FFmpeg cut operations...\n\n")
            
            for msg in output_info_messages:
                f.write(f"echo {msg}\n")
            f.write("\n")

            for cmd in all_ffmpeg_commands:
                f.write(cmd + "\n")
                f.write("\n") 

            f.write("\necho All FFmpeg cutting operations completed successfully.\n")
            f.write("pause\n")
        print(f"\nSuccessfully generated FFmpeg cutting commands to: '{output_batch_file}'")
        print("To perform the cuts, simply run this batch file from Command Prompt.")
        print("Each cut segment will be placed in a subfolder named after the original video (e.g., 'my.movie/').")
    except Exception as e:
        print(f"Error writing batch file: {e}")

if __name__ == "__main__":
    main()