import os
import re
from pathlib import Path

def parse_showinfo_log(log_path):
    """
    Parses a showinfo log file to extract frame numbers and pts_time.
    Returns:
        - frame_to_pts: A dictionary mapping frame number (int) to pts_time (float).
        - last_pts_time: The pts_time of the very last frame found in the log.
    """
    frame_to_pts = {}
    last_pts_time = 0.0
    
    # Regex to capture frame number (n:) and pts_time
    frame_pattern = re.compile(r'n:\s*(\d+).*?pts_time:([\d.]+)')

    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = frame_pattern.search(line)
                if match:
                    frame_num = int(match.group(1))
                    pts_time = float(match.group(2))

                    frame_to_pts[frame_num] = pts_time
                    if pts_time > last_pts_time:
                        last_pts_time = pts_time

    except FileNotFoundError:
        print(f"Error: Showinfo log not found at '{log_path}'.")
        return None, None
    except Exception as e:
        print(f"Error parsing showinfo log '{log_path}': {e}")
        return None, None
    
    return frame_to_pts, last_pts_time

def main():
    print("--- ExactCut Video Tools: Adjusted Vdscript to Timecode Cutlist Generator ---")
    print("This script reads your '_adjusted.vdscript' files and FFmpeg showinfo logs.")
    print("It generates precise timecode-based cutlists for lossless FFmpeg cutting.")
    print("-----------------------------------------------------------------------------")

    script_dir = Path(__file__).parent
    print(f"Script is running from: '{script_dir}'")

    # --- 1. Get Frame Rate Input ---
    input_fps_str = input("Enter the EXACT frame rate (e.g., 23.976, 25, 29.97, 60) for your video(s): ")
    try:
        input_fps = float(input_fps_str)
        if input_fps <= 0:
            raise ValueError
    except ValueError:
        print("Error: Invalid frame rate. Please enter a positive number (e.g., 23.976). Exiting.")
        return

    # --- 2. Find _adjusted.vdscript files ---
    adjusted_vdscript_suffix = "_adjusted.vdscript" 
    all_files_in_dir = [f for f in script_dir.iterdir() if f.is_file()]
    adjusted_vdscripts = []

    print(f"Scanning '{script_dir}' for adjusted VirtualDub script files ending with '{adjusted_vdscript_suffix}'...")
    for f_path in all_files_in_dir:
        if str(f_path.name).endswith(adjusted_vdscript_suffix):
             adjusted_vdscripts.append(f_path)

    if not adjusted_vdscripts:
        print(f"No adjusted VirtualDub script files found ending with '{adjusted_vdscript_suffix}' in '{script_dir}'.")
        print("Please ensure your 'vdscript_range_adjuster.py' has created these files in this directory.")
        return

    print(f"Found {len(adjusted_vdscripts)} '{adjusted_vdscript_suffix}' file(s).")
    
    generated_cutlists_count = 0

    # --- 3. Process each adjusted vdscript file ---
    for vdscript_path in adjusted_vdscripts:
        print(f"\nProcessing '{vdscript_path.name}'...")
        
        # Derive the base video name (e.g., "my.movie.mkv")
        # from "my.movie.mkv_adjusted.vdscript"
        base_video_name = vdscript_path.name.replace(adjusted_vdscript_suffix, "")
        
        # Construct the expected frame log path (new naming convention)
        showinfo_log_path = script_dir / f"{base_video_name}_frame_log.txt"
        output_cutlist_path = script_dir / f"{base_video_name}.cutlist.txt"

        if not showinfo_log_path.is_file():
            print(f"Warning: Corresponding showinfo log '{showinfo_log_path.name}' not found for '{vdscript_path.name}'. Skipping.")
            continue

        frame_to_pts, total_duration_approx = parse_showinfo_log(showinfo_log_path)
        if frame_to_pts is None: # Parsing failed
            continue
        if not frame_to_pts:
            print(f"Warning: No frame data found in '{showinfo_log_path.name}'. Cannot get timecodes. Skipping.")
            continue

        # Parse original ranges from the adjusted vdscript
        # Regex to find lines like 'VirtualDub.subset.AddRange(START_FRAME, LENGTH);'
        vdscript_segment_pattern = re.compile(r'VirtualDub\.subset\.AddRange\((\d+),\s*(\d+)\);')
        adjusted_ranges = []
        try:
            with open(vdscript_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    match = vdscript_segment_pattern.search(line)
                    if match:
                        start_frame = int(match.group(1))
                        length = int(match.group(2))
                        adjusted_ranges.append((start_frame, length))
        except Exception as e:
            print(f"Error reading adjusted vdscript '{vdscript_path.name}': {e}. Skipping.")
            continue
            
        if not adjusted_ranges:
            print(f"No VirtualDub.subset.AddRange entries found in '{vdscript_path.name}'. Skipping.")
            continue

        # Generate timecode cutlist
        timecode_segments = []
        for i, (adj_start_frame, length) in enumerate(adjusted_ranges):
            start_pts_time = frame_to_pts.get(adj_start_frame)
            
            if start_pts_time is None:
                print(f"Warning: Could not find PTS for adjusted start frame {adj_start_frame} in '{showinfo_log_path.name}'. This indicates an issue with original adjustment or log. Skipping segment {i+1}.")
                continue
            
            # Calculate duration in seconds based on length and provided FPS
            duration_seconds = length / input_fps
            
            # Calculate the end time (exclusive for FFmpeg -to, but we'll use -t duration instead)
            # The .6f ensures enough precision for milliseconds
            end_pts_time_calculated = start_pts_time + duration_seconds
            
            # Store as (start_time, duration_seconds) for the next script to use -t
            timecode_segments.append(f"start_time={start_pts_time:.6f},duration={duration_seconds:.6f}") 
            print(f"  - Segment {i+1}: Frames {adj_start_frame} for length {length}. Start Time: {start_pts_time:.3f}s, Duration: {duration_seconds:.3f}s.")

        # Write timecode cutlist to file
        if timecode_segments:
            try:
                with open(output_cutlist_path, 'w') as f:
                    f.write(f"# fps={input_fps:.6f}\n")  # Write FPS at top of file
                    for line in timecode_segments:
                        f.write(line + "\n")
                print(f"Successfully generated timecode cutlist: '{output_cutlist_path.name}'")
                generated_cutlists_count += 1
            except Exception as e:
                print(f"Error writing cutlist '{output_cutlist_path.name}': {e}")
        else:
            print(f"No timecode segments generated for '{vdscript_path.name}'.")

    if generated_cutlists_count == 0:
        print("\nNo timecode cutlist files were generated. Please check warnings above.")
    else:
        print(f"\nFinished generating {generated_cutlists_count} timecode cutlist file(s).")
        print("Next, you'll use the FFmpeg cutter script to use these new cutlist files.")

if __name__ == "__main__":
    main()