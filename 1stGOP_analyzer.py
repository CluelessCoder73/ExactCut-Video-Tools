"""
User Guide for 1stGOP_analyzer.py
Purpose
This script analyzes VirtualDub script files (.vdscript) to determine the size of the starting GOP (Group of Pictures) for each range. It's particularly useful for users who are converting VirtualDub scripts to LosslessCut project files (.llc) and need to ensure frame-accurate cuts without losing the first GOP of any segment.
# This script was tested and works with:
# - Python 3.13.2
# - VirtualDub 1.10.4 .vdscript files
# - VirtualDub2 (build 44282) .vdscript files
# - "FFmpeg" generated frame_log.txt files (the version in LosslessCut 3.63.0)

Features

    Reads frame information from a frame log file
    Analyzes ranges in a VirtualDub script file
    Calculates the size of the starting GOP for each range
    Identifies the smallest starting GOP across all ranges

Prerequisites

    Python 3.x installed on your system
    Input .vdscript file (typically output from vdscript_range_adjuster.py)
    Frame log file (frame_log.txt) containing frame type information

Setup

    Save the script as "1stGOP_analyzer.py" in your working directory.
    Place your input .vdscript file and frame_log.txt in the same directory. Note: The frame_log.txt should already have been created before the "vdscript_range_adjuster.py" stage!

Configuration
At the bottom of the script, you'll find the following configurable parameters:

frame_log_file = 'frame_log.txt'
input_vdscript = 'input.vdscript'
output_file = 'gop_info.txt'

Adjust these parameters as needed:

    frame_log_file: Name of your frame log file
    input_vdscript: Name of your input VirtualDub script file
    output_file: Desired name for the output information file

Usage

    Open a terminal or command prompt.
    Navigate to the directory containing the script and input files.
    Run the script:

    python 1stGOP_analyzer.py

    The script will process your input file and create an output file (default: gop_info.txt) with GOP size information.

Output
The script generates a text file (default: gop_info.txt) containing:

    Starting GOP size for each range in the input script
    A separator line
    The smallest starting GOP size across all ranges

Example output:

250
250
100
---------------------------------------
Smallest starting GOP: 100 frames

How to Use the Results

    The "Smallest starting GOP" value indicates the minimum number of frames you can safely shift your segments forward in LosslessCut without risking the loss of the first GOP in any segment.
    When adjusting your segments in LosslessCut, ensure that you don't shift any segment forward by more than this number of frames.
    This approach allows you to fine-tune your cuts for frame accuracy while maintaining the integrity of each segment's starting GOP.

Tips for Optimal Use

    Always run this script on the output from vdscript_range_adjuster.py to ensure you're working with adjusted, legal cut points.
    If you notice unusually small GOP sizes, it might indicate potential issues with your source video or cut points. In such cases, you may want to review your original edits or the source material.
    Keep in mind that different video codecs and encoding settings can result in varying GOP sizes. Always analyze each project individually for the best results.

Troubleshooting

    If the script fails to run, ensure you have Python 3.x installed and that all file paths are correct.
    If the output seems incorrect, double-check your frame_log.txt file to ensure it matches your video file.
    For videos with unusual GOP structures, you may need to manually verify the results against the actual video file.

This script, used in conjunction with vdscript_range_adjuster.py, provides a powerful solution for ensuring accurate, lossless cuts when working with LosslessCut, especially for high-resolution content edited using proxy videos. This user guide should provide a comprehensive overview of how to use the 1stGOP_analyzer.py script and how to interpret its results in the context of your workflow with LosslessCut. It explains the purpose, setup, usage, and interpretation of results, which should help users effectively utilize this tool in their video editing process.
"""
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

def write_gop_info_to_file(gop_sizes, output_file):
    if gop_sizes:
        with open(output_file, 'w') as outfile:
            for size in gop_sizes:
                outfile.write(f"{size}\n")
            outfile.write("---------------------------------------\n")
            outfile.write(f"Smallest starting GOP: {min(gop_sizes)} frames\n")
    else:
        with open(output_file, 'w') as outfile:
            outfile.write("No ranges available.\n")

# Main execution
frame_log_file = 'frame_log.txt'
input_vdscript = 'output_adjusted_i1_m100_scm.vdscript'
output_file = 'gop_info.txt'

frame_types = read_frame_log(frame_log_file)
gop_sizes = calculate_gop_sizes(input_vdscript, frame_types)
write_gop_info_to_file(gop_sizes, output_file)

print("GOP information has been written to gop_info.txt")
