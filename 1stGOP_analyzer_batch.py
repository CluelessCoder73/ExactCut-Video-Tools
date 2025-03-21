"""
User Guide for 1stGOP_analyzer_batch.py
Purpose
This script analyzes multiple VirtualDub script files (.vdscript) to determine the size of the starting GOP (Group of Pictures) for each range. It's particularly useful for users who are converting VirtualDub scripts to LosslessCut project files (.llc) and need to ensure frame-accurate cuts without losing the first GOP of any segment.
# This script was tested and works with:
# - Python 3.13.2
# - VirtualDub2 (build 44282) .vdscript files
# - "FFmpeg" generated frame log files (the version in LosslessCut 3.64.0)

Features

    Reads frame information from frame log files
    Analyzes ranges in corresponding VirtualDub script files (must have the same name, but with "_adjusted.vdscript" appended instead of "_frame_log.txt")
    Calculates the size of the starting GOP for each range
    Identifies the smallest starting GOP across all ranges
    Repeats this process for every "_adjusted.vdscript"
    Gives final "Smallest starting GOP in all vdscripts" result
        

Prerequisites

    Python 3.x installed on your system
    Input .vdscript file(s) (output from vdscript_range_adjuster.py)
    Frame log file(s) (videofilename_frame_log.txt) containing frame type information

Setup

    Save the script as "1stGOP_analyzer_batch.py" in your working directory.
    Place your input vdscript files and matching frame log files in the same directory.

Usage

    Open a terminal or command prompt.
    Navigate to the directory containing the script and input files.
    Run the script:

    python 1stGOP_analyzer_batch.py

    The script will process your input files and create an output file (default: gop_info.txt) with GOP size information for all vdscripts which end with "_adjusted.vdscript", & the overall shortest at the very bottom.

Example output:

Name: "video1.mp4_adjusted.vdscript"
250
250

Smallest starting GOP: 250 frames
---------------------------------

Name: "video2.mp4_adjusted.vdscript"
138
200
17

Smallest starting GOP: 17 frames
---------------------------------

--------------------------------------------------
--------------------------------------------------
Smallest starting GOP in all vdscripts: 17 frames ("video2.mp4_adjusted.vdscript")

How to Use the Results

    The "Smallest starting GOP" value indicates the minimum number of frames you can safely shift your segments forward in LosslessCut without risking the loss of the first GOP in any segment.
    When adjusting your segments in LosslessCut, ensure that you don't shift any segment forward by more than this number of frames.
    This approach allows you to fine-tune your cuts for frame accuracy while maintaining the integrity of each segment's starting GOP.

Tip for Optimal Use

    Always run this script on the output from vdscript_range_adjuster.py to ensure you're working with adjusted, legal cut points.

Troubleshooting

    If the script fails to run, ensure you have Python 3.x installed.
    If the output seems incorrect, double-check your frame log file to ensure it matches your video file.

This script, used in conjunction with vdscript_range_adjuster.py, provides a powerful solution for ensuring accurate, lossless cuts when working with LosslessCut, especially for high-resolution content edited using proxy videos.
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

def find_next_i_frame(start_frame, end_frame, frame_types):
    for frame in range(start_frame + 1, end_frame + 1):
        if frame_types.get(frame) == 'I':
            return frame
    return None

def calculate_gop_sizes(vdscript_file, frame_types):
    gop_sizes = []
    with open(vdscript_file, 'r') as f:
        for line in f:
            if line.startswith('VirtualDub.subset.AddRange'):
                match = re.search(r'AddRange\((\d+),(\d+)\)', line)
                if match:
                    start_frame = int(match.group(1))
                    range_length = int(match.group(2))
                    end_frame = start_frame + range_length - 1
                    next_i_frame = find_next_i_frame(start_frame, end_frame, frame_types)
                    if next_i_frame:
                        gop_size = next_i_frame - start_frame
                    else:
                        gop_size = range_length
                    gop_sizes.append(gop_size)
    return gop_sizes

def batch_process_vdscripts(directory, output_file):
    all_results = []
    smallest_overall = None
    smallest_file = None
    
    with open(output_file, 'w') as outfile:
        for filename in os.listdir(directory):
            if filename.endswith('_adjusted.vdscript'):
                base_name = filename.replace('_adjusted.vdscript', '')
                frame_log_file = os.path.join(directory, f"{base_name}_frame_log.txt")
                vdscript_file = os.path.join(directory, filename)
                
                if os.path.exists(frame_log_file):
                    frame_types = read_frame_log(frame_log_file)
                    gop_sizes = calculate_gop_sizes(vdscript_file, frame_types)
                    
                    if gop_sizes:
                        # Write the vdscript name and GOP sizes
                        outfile.write(f"Name: \"{filename}\"\n")
                        for size in gop_sizes:
                            outfile.write(f"{size}\n")
                        
                        # Calculate and write the smallest GOP size for this vdscript
                        smallest = min(gop_sizes)
                        outfile.write(f"\nSmallest starting GOP: {smallest} frames\n")
                        outfile.write("---------------------------------\n\n")
                        
                        # Track the overall smallest GOP size
                        if smallest_overall is None or smallest < smallest_overall:
                            smallest_overall = smallest
                            smallest_file = filename
                else:
                    print(f"Skipped: {filename} (No corresponding frame log file found)")
        
        # Write the overall smallest GOP size at the end
        if smallest_overall is not None:
            outfile.write("--------------------------------------------------\n")
            outfile.write("--------------------------------------------------\n")
            outfile.write(f"Smallest starting GOP in all vdscripts: {smallest_overall} frames (\"{smallest_file}\")\n")

# Main execution
directory = '.'  # Current directory, change if needed
output_file = 'gop_info.txt'

batch_process_vdscripts(directory, output_file)

print("Batch processing completed. Results written to gop_info.txt")
