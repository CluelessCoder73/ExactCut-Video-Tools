import os
import re

# ----------------------------------------------------------------------
# Script: vdscript_info.py
# Description:
# This script converts VirtualDub or VirtualDub2 .vdscript files into a 
# simple text file containing all the timecodes for the wanted parts, 
# followed by the frame numbers (start - end), followed by the length 
# in time, then frames. On the 3rd last line, we have "Total Length" in 
# time, then frames, & on the 2nd last line, we have fps. This can be 
# useful if you forget whether you input the correct frame rate or not.
# NOW WORKS IN BATCH MODE!!!
# This script was tested and works with:
# - Python 3.13.2
# - VirtualDub 1.10.4 .vdscript files
# - VirtualDub2 (build 44282) .vdscript files
#
# Usage:
# 1. Place this script in a folder containing 1 or more vdscript files.
#    WARNING: They must ALL have the same frame rate! Create separate 
#    folders if they don't (e.g., "23.976", "25"), & copy this script 
#    to each one.
# 2. Run the script.
# 3. Enter the correct frame rate when asked.
# 4. A text file will be created for each vdscript, with the same name, 
#    but with "_info.txt" appended.
#
# Example:
# VirtualDub.subset.AddRange(446,444);
# VirtualDub.subset.AddRange(1397,194);
#
# Will end up looking like this:
# 00:00:18.601 - 00:00:37.078 (Frames 446 - 889)     Length: 00:00:18.518 (444 frames)
# 00:00:58.266 - 00:01:06.316 (Frames 1397 - 1590)   Length: 00:00:08.091 (194 frames)
# --------------------------------------------------------------------------------
# Total Length: 00:00:26.609 (638 frames)
# fps = 23.976
#
#-----------------------------------------------------------------------

def timecode(frame, fps):
    """
    Convert a frame number to a timecode string (HH:MM:SS.mmm) based on the given FPS.
    """
    total_seconds = frame / fps
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int((total_seconds % 1) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"

def process_vdscript(file_path, fps):
    """
    Process a .vdscript file, extract frame range selections, and convert them into
timecodes with frame counts. Save the output as a corresponding _info.txt file.
    """
    output_file = file_path.replace(".vdscript", "_info.txt")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    selections = []
    total_frames = 0
    pattern = re.compile(r"VirtualDub\.subset\.AddRange\((\d+),(\d+)\);")
    
    for line in lines:
        match = pattern.search(line)
        if match:
            start_frame = int(match.group(1))
            length = int(match.group(2))
            end_frame = start_frame + length - 1  # Convert to endpoint-inclusive
            selections.append((start_frame, end_frame, length))
            total_frames += length
    
    # Determine the max width for frame range text for alignment
    max_frames_text_length = max(len(f"(Frames {s[0]} - {s[1]})") for s in selections)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for start, end, length in selections:
            start_tc = timecode(start, fps)
            end_tc = timecode(end, fps)
            length_tc = timecode(length, fps)
            frames_text = f"(Frames {start} - {end})"
            f.write(f"{start_tc} - {end_tc} {frames_text:<{max_frames_text_length}}   Length: {length_tc} ({length} frames)\n")
        
        # Add total length information
        f.write("-" * 80 + "\n")
        total_length_tc = timecode(total_frames, fps)
        f.write(f"Total Length: {total_length_tc} ({total_frames} frames)\n")
        f.write(f"fps = {fps}\n")

def main():
    """
    Main function to process all .vdscript files in the current directory.
    Prompts user for FPS input and displays a warning before proceeding.
    """
    folder = os.getcwd()
    vdscript_files = [f for f in os.listdir(folder) if f.endswith(".vdscript")]
    
    if not vdscript_files:
        print("No .vdscript files found in the folder.")
        return
    
    # Ask the user for the frame rate (FPS)
    fps = float(input("Enter the frame rate (fps): "))
    input("WARNING: Are you sure that all frame rates match? (Press Enter to continue, or Ctrl+C to cancel)")
    
    for file in vdscript_files:
        print(f"Processing {file}...")
        process_vdscript(os.path.join(folder, file), fps)
    
    print("Batch processing complete! Output files have '_info.txt' suffix.")

if __name__ == "__main__":
    main()
