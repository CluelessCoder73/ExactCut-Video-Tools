"""
User Guide for vdscript_range_adjuster.py
Purpose
This script is designed to adjust cut points in VirtualDub & VirtualDub2 script files (.vdscript) to ensure they align with legal frame boundaries, particularly useful when working with proxy videos for editing high-resolution footage. It guarantees that no frames are lost in the process, unlike most "stream copy" video editors. No need for aligning cut points with keyframes etc, because this script does all that for you automatically! After generating the adjusted .vdscript file, you can convert it to a "Cuttermaran" project file, or an "MKVToolNix GUI" cutlist via "vdscript_to_mkvtoolnix.py" (included). For Cuttermaran, "vdscript_to_cpf" is available at https://github.com/CluelessCoder73/vdscript_to_cpf
This script now works in batch mode!
# Tested and works with:
# - Python 3.13.2
# - VirtualDub 1.10.4 .vdscript files
# - VirtualDub2 (build 44282) .vdscript files
# - "FFmpeg" generated frame log files (the version in LosslessCut 3.65.0)

Features:

# - Adjusts start points to previous I-frames. If the start point is already on an I-frame, it is left untouched. 
    Alternatively, you can also adjust the start point to the "2nd" previous I-frame (the I-frame before the previous one). In that case, if the start point is already on an I-frame, it is instead adjusted to just the previous I-frame. Can be useful when working with x265 & other "open GOP" codecs, where cut-in points end up corrupted, & the video doesn't play right again until the next I-frame.
    In fact, you can go furter back in I-frames, but I don't see any need (so far) to go any further back than 2.

	# - Adjusts endpoints to the last P-frame before the next I-frame. If the endpoint is already on the last P-frame before the next I-frame, it is left untouched.
    Alternatively, you can adjust the endpoints to just the next P or I-frame ("short_cut_mode = True"). In that case, if, e.g., the endpoint is already on a P or I-frame, it is left untouched.
    
# - Merges overlapping or close ranges (optional)

Prerequisites

    Python 3.x installed on your system
    Input .vdscript file(s) from VirtualDub or VirtualDub2 (sourcevideofilename.vdscript)
    Frame log file (sourcevideofilename_frame_log.txt) containing frame type information

Configuration
At the bottom of the script, you'll find several configurable parameters:

directory = '.'
i_frame_offset = 1
merge_ranges_option = True
min_gap_between_ranges = 100
short_cut_mode = False

Adjust these parameters as needed:

    directory: Defaults to current directory, change if needed
    i_frame_offset: Number of I-frames to go back for start points (default: 1)
    merge_ranges_option: Set to True to enable merging of close ranges, False to disable
    min_gap_between_ranges: Minimum gap (in frames) to keep ranges separate when merging
    short_cut_mode: Set to True to enable moving endpoints to the next P or I-frame, False for "full GOP mode"

Output
The script generates new .vdscript files with the adjusted cut points. These files can then be used directly in VirtualDub or VirtualDub2 (depending on which version created the original vdscript files!), or converted to other formats like .cpf (Cuttermaran project files) or "MKVToolNix GUI" cutlists.
Tips for Optimal Use

    When editing proxy videos, place cut points freely without worrying about exact frame types.
    Use this script to adjust the cut points before applying them to your high-resolution footage.
    Experiment with the i_frame_offset value to find the best balance between accuracy and avoiding potential corruption from open GOP structures.
    If you notice any issues with playback at cut points, try increasing the i_frame_offset value.

Troubleshooting

    If the script fails to run, ensure you have Python 3.x installed.
    If cut points seem incorrect, double-check your frame log to ensure it matches your video file.
    For videos with unusual GOP structures, you may need to adjust the i_frame_offset.

Converting Output to Other Formats
After generating the adjusted .vdscript file, you can convert it to other formats:

    For Cuttermaran: Use "vdscript_to_cpf" to create a .cpf file.
    For LosslessCut: Use "vdscript_to_llc". WARNING: not frame-accurate!
    For MKVToolNix GUI: Use "vdscript_to_mkvtoolnix.py" (included).
    All are available at https://github.com/CluelessCoder73?tab=repositories

This script provides a powerful solution for ensuring accurate, lossless cuts in your video editing workflow, especially when working with proxy videos for high-resolution content. By automating the adjustment of cut points to legal frame boundaries, it saves time and guarantees the integrity of your final edit.

###########################################################
#######How to edit a 4K video using the proxy method#######

Here's my guide on editing a 4K video in VirtualDub2, & saving the final export with MKVToolNix GUI. Because this method uses proxy videos, it does not require a high-end PC! NOTE: If your proxy videos are lagging in VirtualDub2, you will need to reduce the max resolution for the proxy presets!
Software required:
HandBrake
VirtualDub2
MKVToolNix GUI

Step 1:
Make sure your videos are MP4. If they are not, remux them to that format (LosslessCut can do this). This step is necessary for frame accuracy. The only exceptions to this rule are MPEG-1/2 (in which case you should be using "vdscript_to_cpf"), & DivX/XviD AVI files (in which case you should be using VirtualDub itself). For codecs which are not supported by the MP4 format, you can try MKV, but just be aware that you may lose frames. The number is small, but it goes against the very premise behind the creation of these scripts: "Cut as close to the wanted ranges as possible without losing ANY frames!".

Step 2:
NOTE: This step is only necessary if you plan on using "vdscript_info.py"!
Put all your source videos into folders according to their frame rates (e.g., 23.976, 25 etc). For the sake of simplicity, for the rest of this guide, I will only refer to one folder, because the method for all folders is the same.

Step 3:
Create proxy versions of your videos using HandBrake: Use one of the provided custom presets. You may want to raise the "Constant Quality" values, because they are all set at "RF 16". The default "RF 22", or higher will be good enough for most. You may also want to lower the "Resolution Limit", which is set at "720p HD". NOTE: All filters are turned off, so if your video is e.g. interlaced, you will need to enable deinterlacing! DO NOT save to the same folder as your input files!

Step 4:
Open "frame_log_extractor.bat" in a text editor, & specify the path to "ffmpeg.exe". You can now save the modified version of it for future use. Now copy the following scripts into your "source videos" folder:

frame_log_extractor.bat
vdscript_info.py (optional)
vdscript_range_adjuster.py
vdscript_to_mkvtoolnix.py

Step 5:
Run "frame_log_extractor.bat". Be patient, it will take a long time. It will process every video it finds in the folder. Each frame log file will have the same name as its corresponding video (including extension), with "_frame_log.txt" appended.

Step 6:
Edit your proxy videos with VirtualDub2. You can use 32 or 64 bit, the output vdscript is identical. But for performance, I always use the 64 bit version. You will notice that these proxy versions are really easy to work with - you can scan at high speed through the videos by using SHIFT+LEFT & SHIFT+RIGHT, & you can go even faster by using ALT+LEFT & PGDOWN. Save your work in VirtualDub2 by using CTRL+S to save processing settings. MAKE SURE to check "Include selection and edit list", Otherwise your cuts will NOT be saved!!! Once you do that, it will remain so for future sessions. When editing is complete, the vdscript must be saved as "source video filename" + ".vdscript". So, if your source video is called "whatever.mp4", your final saved vdscript should be called "whatever.mp4.vdscript".

Step 7:
Run "vdscript_range_adjuster.py". It will process every vdscript (which has a corresponding frame log file), & the outputted files will have "_adjusted.vdscript" appended.

Step 8:
Run vdscript_info.py (optional) for a detailed "before & after" comparison. This tool can also be useful for verifying that the final output has the correct number of frames.

Step 9:
Execute the following:

python vdscript_to_mkvtoolnix.py --merge

Omit " --merge" for non-concatenated parts instead (can be useful for analysing each individual part, to determine if frames have been lost or not). Hint: "vdscript_to_mkvtoolnix.py" only processes files with "_adjusted.vdscript" appended, & it outputs a single file called "batch_cutlist.txt".

Step 10:
Open MKVToolNix GUI. Add your MP4 video file (NOT the proxy!). Go to "Output" tab. Under "Splitting", select "By parts based on frame/field numbers". Paste the cutlist string (without quotes/filename) into the input field. Start multiplexing. After the operation is complete, you can mux it to a different container if desired. NOTE: The output may have a few extra frames compared to the input. If you want the EXACT number of frames as the input, you will need to disable the audio in MKVToolNix GUI, & process the audio separately (the audio will need to be re-encoded). This can be achieved by opening the original MP4 video in VirtualDub2, load the "_adjusted" vdscript, choose audio "Full processing mode", & save it as wav. You can then compress it using Audacity or any other audio conversion program. Then mux the "video only" MKV & audio into your desired format.

###########################################################
###########################################################

VERY IMPORTANT! - DO NOT get your original videos & proxy videos mixed up!!

VERIFYING THAT THE SOURCE & PROXY MATCH:
Open your "whatevervideo_frame_log.txt", & go to the 2nd last line (the last line of actual text); Somewhere in this line, it will say, e.g. "n:58357".
Now, open your proxy video in VirtualDub2, & hit the [End] key. This will bring you to the last frame of the video. The display at the bottom should say, e.g. "Frame 58358". That is the total number of frames in your proxy video, & SHOULD be +1 (in comparison to that last frame reported in the frame log), because in VirtualDub2, the last frame is always an "empty" frame.
DO NOT compare the proxy with the actual source video itself! The frame counts will often match, but NOT ALWAYS! The important thing (in terms of frame accuracy) is that your frame logs & proxy videos match.
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
i_frame_offset = 1  # Increase this value to go further back in I-frames
merge_ranges_option = True  # Set to False to disable merging
min_gap_between_ranges = 100  # Minimum gap between ranges (in frames)
short_cut_mode = False  # Set to False for "full GOP mode"

batch_process_vdscripts(directory, i_frame_offset, merge_ranges_option, min_gap_between_ranges, short_cut_mode)

print("Batch processing completed.")
