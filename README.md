# vdscript_range_adjuster
This script is designed to adjust cut points in VirtualDub &amp; VirtualDub2 script files (.vdscript) to ensure they align with legal frame boundaries.
It is particularly useful when working with proxy videos for editing high-resolution footage. It guarantees that no frames are lost in the process, unlike most "stream copy" video editors.
This script was tested and works with:
- Python 3.12.5
- VirtualDub 1.10.4 .vdscript files
- VirtualDub2 (build 44282) .vdscript files
- "FFmpeg" generated frame_log.txt files (the version in LosslessCut 3.63.0)

Features:

- Adjusts start points to previous I-frames. If the start point is already on an I-frame, it is left untouched. 
    Alternatively, you can also adjust the start point to the "2nd" previous I-frame (the I-frame before the previous one). In that case, if the start point is already on an I-frame, it is instead adjusted to just the previous I-frame. This can be useful when working with x265 & other "open GOP" codecs, where cut-in points end up corrupted, & the video doesn't play right again until the next I-frame.
    In fact, you can go furter back in I-frames, but I don't see any need (so far) to go any further back than 2.

- Adjusts endpoints to the next P or I-frame. If the endpoint is already on a P or I-frame, it is left untouched.
    Alternatively, you can also adjust the endpoint to the last P-frame before the next I-frame ("short_cut_mode = False"). In that case, if, e.g., the endpoint is already on the last P-frame before the next I-frame, it is left untouched.
    
- Merges overlapping or close ranges (optional)

Prerequisites

    Python 3.x installed on your system
    Input .vdscript file from VirtualDub or VirtualDub2
    Frame log file (frame_log.txt) containing frame type information

Setup

    Prepare the frame_log.txt:
        Generate a frame_log.txt file with information on frame types (I, P, B) using ffmpeg. This can be easily achieved by running "frame_log_extractor.bat" (edit filename paths 1st!).
    Save the script as "vdscript_range_adjuster_v1.4.1.py" in your working directory.
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

    python vdscript_range_adjuster_v1.4.1.py

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