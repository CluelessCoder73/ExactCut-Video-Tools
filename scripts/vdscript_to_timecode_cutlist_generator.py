import os
import re
from pathlib import Path

# --- ExactCut Video Tools: VFR-Aware Cutlist Generator ---
# Updated to support Variable Frame Rate (VFR) by calculating 
# exact durations from frame timestamps rather than a fixed FPS.
# Tested and works with:
# - Python 3.13.7
# - VirtualDub2 (build 44282) .vdscript files
# - "FFmpeg" generated frame log files (the version in LosslessCut 3.68.0)

def parse_showinfo_log(log_path):
    """
    Parses a showinfo log file to extract frame numbers and pts_time.
    Returns:
        - frame_to_pts: A dictionary mapping frame number (int) to pts_time (float).
        - sorted_frames: A sorted list of all frame numbers found (for easy navigation).
    """
    frame_to_pts = {}
    
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
                    
    except FileNotFoundError:
        print(f"Error: Showinfo log not found at '{log_path}'.")
        return None, None
    except Exception as e:
        print(f"Error parsing showinfo log '{log_path}': {e}")
        return None, None
    
    if not frame_to_pts:
        return {}, []

    # create a sorted list of keys to help us find the 'max' frame later
    sorted_frames = sorted(frame_to_pts.keys())
    
    return frame_to_pts, sorted_frames

def main():
    print("--- ExactCut Video Tools: VFR-Aware Cutlist Generator ---")
    print("This script reads your '_adjusted.vdscript' files and FFmpeg showinfo logs.")
    print("It calculates durations based on REAL timestamps (VFR Supported).")
    print("-----------------------------------------------------------------------------")

    script_dir = Path(__file__).parent
    print(f"Script is running from: '{script_dir}'")

    # --- 1. (REMOVED) Manual Frame Rate Input ---
    # We no longer ask for FPS. We calculate it dynamically per segment.

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
        base_video_name = vdscript_path.name.replace(adjusted_vdscript_suffix, "")
        
        # Construct the expected frame log path
        showinfo_log_path = script_dir / f"{base_video_name}_frame_log.txt"
        output_cutlist_path = script_dir / f"{base_video_name}.cutlist.txt"

        if not showinfo_log_path.is_file():
            print(f"Warning: Corresponding showinfo log '{showinfo_log_path.name}' not found for '{vdscript_path.name}'. Skipping.")
            continue

        frame_to_pts, sorted_frames = parse_showinfo_log(showinfo_log_path)
        
        if frame_to_pts is None: # Parsing failed
            continue
        if not frame_to_pts:
            print(f"Warning: No frame data found in '{showinfo_log_path.name}'. Cannot get timecodes. Skipping.")
            continue

        # Parse original ranges from the adjusted vdscript
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
                print(f"Warning: Could not find PTS for start frame {adj_start_frame}. Skipping segment {i+1}.")
                continue
            
            # --- VFR CALCULATION LOGIC ---
            # To get the exact duration, we find the timestamp of the frame *after* our segment ends
            # and subtract the start time.
            
            end_frame_idx = adj_start_frame + length
            end_pts_time = frame_to_pts.get(end_frame_idx)

            if end_pts_time is not None:
                # Perfect scenario: We have the timestamp for the frame immediately following the cut.
                duration_seconds = end_pts_time - start_pts_time
            else:
                # Edge Case: The cut goes to the very end of the video (or beyond logged frames).
                # We need to estimate the duration of the final frames based on the last known frame duration.
                last_known_frame = sorted_frames[-1]
                
                # Calculate duration of the last known frame (Pts[Last] - Pts[Last-1])
                if len(sorted_frames) > 1:
                    last_frame_dur = frame_to_pts[last_known_frame] - frame_to_pts[sorted_frames[-2]]
                else:
                    last_frame_dur = 0.04 # Fallback to approx 25fps if only 1 frame exists (unlikely)

                # Estimate the end time
                # If we are missing N frames, we add N * last_frame_dur
                missing_frames_count = end_frame_idx - last_known_frame
                
                # However, usually end_frame_idx is just (last_known + 1)
                # So we take the last known PTS and add the duration of that last frame.
                estimated_end_pts = frame_to_pts[last_known_frame] + (last_frame_dur * missing_frames_count)
                
                duration_seconds = estimated_end_pts - start_pts_time

            # Store as (start_time, duration_seconds)
            timecode_segments.append(f"start_time={start_pts_time:.6f},duration={duration_seconds:.6f}") 
            print(f"  - Segment {i+1}: Frames {adj_start_frame} to {adj_start_frame+length}. Duration: {duration_seconds:.3f}s (VFR calc).")

        # Write timecode cutlist to file
        if timecode_segments:
            try:
                with open(output_cutlist_path, 'w') as f:
                    # We write a dummy fps header just in case other tools look for it, but set it to 0 or 'VFR'
                    f.write(f"# fps=VFR_CALCULATED\n") 
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
        print("Next, you'll use ExactCut FFmpeg Cutter to use these new cutlist files.")

if __name__ == "__main__":
    main()