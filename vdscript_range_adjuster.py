"""
User Guide for vdscript_range_adjuster.py
Purpose
This script is designed to adjust cut points in VirtualDub & VirtualDub2 script files (.vdscript) to ensure they align with legal frame boundaries, particularly useful when working with proxy videos for editing high-resolution footage. It guarantees that no frames are lost in the process, unlike most "stream copy" video editors.
# This script was tested and works with:
# - Python 3.12.5
# - VirtualDub 1.10.4 .vdscript files
# - VirtualDub2 (build 44282) .vdscript files
# - "FFmpeg" generated frame_log.txt files (the version in LosslessCut 3.63.0)

Features:

# - Adjusts start points to previous I-frames. If the start point is already on an I-frame, it is left untouched. 
    Alternatively, you can also adjust the start point to the "2nd" previous I-frame (the I-frame before the previous one). In that case, if the start point is already on an I-frame, it is instead adjusted to just the previous I-frame. This can be useful when working with x265 & other "open GOP" codecs, where cut-in points end up corrupted, & the video doesn't play right again until the next I-frame.
    In fact, you can go furter back in I-frames, but I don't see any need (so far) to go any further back than 2.

# - Adjusts endpoints to the next P or I-frame. If the endpoint is already on a P or I-frame, it is left untouched.
    Alternatively, you can also adjust the endpoint to the last P-frame before the next I-frame ("short_cut_mode = False"). In that case, if, e.g., the endpoint is already on the last P-frame before the next I-frame, it is left untouched.
    
# - Merges overlapping or close ranges (optional)

Prerequisites

    Python 3.x installed on your system
    Input .vdscript file from VirtualDub or VirtualDub2
    Frame log file (frame_log.txt) containing frame type information

Setup

    Prepare the frame_log.txt:
        Generate a frame_log.txt file with information on frame types (I, P, B) using ffmpeg. This can be easily achieved by running "frame_log_extractor.bat" (edit filename paths 1st!).
    Save the script as "vdscript_range_adjuster.py" in your working directory.
    Place your input .vdscript file and frame_log.txt in the same directory.

Configuration
At the bottom of the script, you'll find several configurable parameters:

frame_log_file = 'frame_log.txt'
input_vdscript = 'input.vdscript'
output_vdscript = 'output.vdscript'
i_frame_offset = 1
merge_ranges_option = True
min_gap_between_ranges = 100
short_cut_mode = True

Adjust these parameters as needed:

    frame_log_file: Name of your frame log file
    input_vdscript: Name of your input VirtualDub script file
    output_vdscript: Desired name for the output script file
    i_frame_offset: Number of I-frames to go back for start points (default: 1)
    merge_ranges_option: Set to True to enable merging of close ranges, False to disable
    min_gap_between_ranges: Minimum gap (in frames) to keep ranges separate when merging
    short_cut_mode: Set to True to enable moving endpoints to the next P or I-frame, False for "full GOP mode"

Usage

    Open a terminal or command prompt.
    Navigate to the directory containing the script and input files.
    Run the script:

    python vdscript_range_adjuster.py

    The script will process your input file and create an output file with adjusted cut points.

Output
The script generates a new .vdscript file with adjusted cut points. This file can be used directly in VirtualDub or VirtualDub2 (depending on which version created the vdscript file!), or converted to other formats like .cpf (Cuttermaran project files) or .llc (LosslessCut project files).
Tips for Optimal Use

    When editing proxy videos, place cut points freely without worrying about exact frame types.
    Use this script to adjust the cut points before applying them to your high-resolution footage.
    Experiment with the i_frame_offset value to find the best balance between accuracy and avoiding potential corruption from open GOP structures.
    If you notice any issues with playback at cut points, try increasing the i_frame_offset value.

Troubleshooting

    If the script fails to run, ensure you have Python 3.x installed and that all file paths are correct.
    If cut points seem incorrect, double-check your frame_log.txt file to ensure it matches your video file.
    For videos with unusual GOP structures, you may need to adjust the i_frame_offset or short_cut_mode settings.

Converting Output to Other Formats
After generating the adjusted .vdscript file, you can convert it to other formats:

    For Cuttermaran: Use "vdscript_to_cpf" to create a .cpf file.
    For LosslessCut: Use "vdscript_to_llc" to transform the .vdscript into a .llc file format.
    Both are available on my GitHub page!

This script provides a powerful solution for ensuring accurate, lossless cuts in your video editing workflow, especially when working with proxy videos for high-resolution content. By automating the adjustment of cut points to legal frame boundaries, it saves time and guarantees the integrity of your final edit.
"""
import os
import re

def read_frame_log(file_path):
    frame_types = {}
    with open(file_path, 'r') as f:
        for line in f:
            if 'Parsed_showinfo_0' in line:
                match = re.search(r'n:\s*(\d+).*type:(\w)', line)
                if match:
                    frame_num, frame_type = int(match.group(1)), match.group(2)
                    frame_types[frame_num] = frame_type
    return frame_types

def find_nth_previous_i_frame(frame_num, frame_types, n):
    i_frames_found = 0
    while frame_num >= 0:
        if frame_types.get(frame_num) == 'I':
            i_frames_found += 1
            if i_frames_found == n:
                return frame_num
        frame_num -= 1
    return 0  # Return 0 if we can't find enough I-frames

def find_last_p_frame_before_next_i(frame_num, frame_types):
    max_frame = max(frame_types.keys())
    last_p_frame = None
    while frame_num <= max_frame:
        if frame_types.get(frame_num) == 'I' and last_p_frame is not None:
            return last_p_frame
        if frame_types.get(frame_num) == 'P':
            last_p_frame = frame_num
        frame_num += 1
    return last_p_frame if last_p_frame is not None else max_frame

def adjust_range(start, length, frame_types, i_frame_offset, short_cut_mode):
    new_start = find_nth_previous_i_frame(start, frame_types, i_frame_offset)
    end = start + length - 1
    
    if short_cut_mode:
        new_end = find_next_p_or_i_frame(end, frame_types)
    else:
        new_end = find_last_p_frame_before_next_i(end, frame_types)
    
    new_length = new_end - new_start + 1
    return new_start, new_length

def find_next_p_or_i_frame(frame_num, frame_types):
    max_frame = max(frame_types.keys())
    if frame_types.get(frame_num) in ['I', 'P']:
        return frame_num  # Return the current frame if it's already I or P
    next_frame = frame_num + 1
    while next_frame <= max_frame:
        if frame_types.get(next_frame) in ['I', 'P']:
            return next_frame
        next_frame += 1
    return frame_num  # Return original frame if no next I or P frame found

def merge_ranges(ranges, min_gap):
    if not ranges:
        return []
    
    merged = [ranges[0]]
    for current in ranges[1:]:
        previous = merged[-1]
        if current[0] - (previous[0] + previous[1]) <= min_gap:
            merged[-1] = (previous[0], max(previous[0] + previous[1], current[0] + current[1]) - previous[0])
        else:
            merged.append(current)
    
    return merged

def process_vdscript(input_file, output_file, frame_types, i_frame_offset, merge_option, min_gap, short_cut_mode):
    ranges = []
    
    infile = open(input_file, 'r')
    input_lines = infile.readlines()
    infile.close()

    for line in input_lines:
        if line.startswith('VirtualDub.subset.AddRange'):
            match = re.search(r'AddRange\((\d+),(\d+)\)', line)
            if match:
                start, length = int(match.group(1)), int(match.group(2))
                new_start, new_length = adjust_range(start, length, frame_types, i_frame_offset, short_cut_mode)
                ranges.append((new_start, new_length))

    if merge_option:
        ranges = merge_ranges(ranges, min_gap)

    with open(output_file, 'w') as outfile:
        for line in input_lines:
            if not line.startswith('VirtualDub.subset.AddRange') and not line.startswith('VirtualDub.video.SetRange'):
                outfile.write(line)

        # Write the adjusted ranges first
        for start, length in ranges:
            outfile.write(f'VirtualDub.subset.AddRange({start},{length});\n')

        # Write the VirtualDub.video.SetRange() line last
        outfile.write('VirtualDub.video.SetRange();\n')

def batch_process_vdscripts(directory, i_frame_offset, merge_ranges_option, min_gap_between_ranges, short_cut_mode):
    for filename in os.listdir(directory):
        if filename.endswith('.vdscript'):
            input_vdscript = os.path.join(directory, filename)
            frame_log_file = os.path.join(directory, f"{os.path.splitext(filename)[0]}_frame_log.txt")
            output_vdscript = os.path.join(directory, f"{os.path.splitext(filename)[0]}_adjusted.vdscript")
            
            if os.path.exists(frame_log_file):
                frame_types = read_frame_log(frame_log_file)
                process_vdscript(input_vdscript, output_vdscript, frame_types, i_frame_offset, merge_ranges_option, min_gap_between_ranges, short_cut_mode)
                print(f"Processed: {filename}")
            else:
                print(f"Skipped: {filename} (No corresponding frame log file found)")

# Main execution
directory = '.'  # Current directory, change if needed
i_frame_offset = 1
merge_ranges_option = True
min_gap_between_ranges = 100
short_cut_mode = True

batch_process_vdscripts(directory, i_frame_offset, merge_ranges_option, min_gap_between_ranges, short_cut_mode)

print("Batch processing completed.")
