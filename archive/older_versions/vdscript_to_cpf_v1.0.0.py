import re
import os

# ----------------------------------------------------------------------
# Script: vdscript_to_cpf_v1.0.0.py
# Description:
# This script converts VirtualDub or VirtualDub2 .vdscript files into 
# Cuttermaran .cpf project files. It is designed to help users quickly 
# create Cuttermaran project files from existing VirtualDub cuts.
# 
# Features:
# - Convert VirtualDub (.vdscript) cuts into Cuttermaran (.cpf) format.
# - Automatically handles multiple cut segments.
#
# Usage:
# 1. Place this script in the same directory as your .vdscript file or specify 
#    the full path to your .vdscript file in the vdscript_filepath variable.
# 2. Edit the script parameters in the "Usage example" section:
#    - `vdscript_filepath`: Path to your .vdscript file.
#    - `cpf_filepath`: Desired path for the output .cpf file.
#    - `video_filepath`: Path to the video file used in Cuttermaran.
#    - `audio_filepath`: Path to the audio file used in Cuttermaran.
# 3. Run the script.
#
# Version History:
# v1.0.0 - Initial script with basic conversion functionality.
# ----------------------------------------------------------------------

# Function to parse the .vdscript file and extract cut ranges
def parse_vdscript(filepath):
    """
    Parses the .vdscript file to extract cut ranges.

    Args:
        filepath (str): Path to the .vdscript file.

    Returns:
        list: A list of dictionaries representing cut segments with start and end frames.
    """
    cut_segments = []

    with open(filepath, 'r') as file:
        lines = file.readlines()
    
    # Regex to match VirtualDub subset lines (e.g., VirtualDub.subset.AddRange(412,208);)
    subset_pattern = re.compile(r'VirtualDub\.subset\.AddRange\((\d+),(\d+)\);')

    for line in lines:
        match = subset_pattern.match(line)
        if match:
            start_frame = int(match.group(1))
            frame_count = int(match.group(2))
            end_frame = start_frame + frame_count

            # Append the segment to the list
            cut_segments.append({
                "StartPosition": start_frame,
                "EndPosition": end_frame
            })

    return cut_segments

# Function to write the Cuttermaran .cpf file
def write_cpf_file(output_filepath, video_filepath, audio_filepath, cut_segments):
    """
    Writes the cut segments to a Cuttermaran .cpf file.

    Args:
        output_filepath (str): Path to save the .cpf file.
        video_filepath (str): Path to the video file used in Cuttermaran.
        audio_filepath (str): Path to the audio file used in Cuttermaran.
        cut_segments (list): List of dictionaries representing cut segments.
    """
    if os.path.exists(output_filepath):
        print(f"Error: The file {output_filepath} already exists. Please choose a different filename or remove the existing file.")
        return
    
    with open(output_filepath, 'w') as file:
        file.write('<?xml version="1.0" standalone="yes"?>\n')
        file.write('<StateData xmlns="http://cuttermaran.kickme.to/StateData.xsd">\n')
        file.write(f'  <usedVideoFiles FileID="0" FileName="{video_filepath}" />\n')
        file.write(f'  <usedAudioFiles FileID="1" FileName="{audio_filepath}" StartDelay="0" />\n')

        for segment in cut_segments:
            file.write(f'  <CutElements refVideoFile="0" StartPosition="{segment["StartPosition"]}" EndPosition="{segment["EndPosition"]}">\n')
            file.write(f'    <cutAudioFiles refAudioFile="1" />\n')
            file.write('  </CutElements>\n')
        
        file.write('  <CurrentFiles refVideoFiles="0">\n')
        file.write('    <currentAudioFiles refAudioFiles="1" />\n')
        file.write('  </CurrentFiles>\n')
        file.write('</StateData>\n')
    
    print(f"Cuttermaran project file saved as {output_filepath}")

# Main function to perform the conversion
def convert_vdscript_to_cpf(vdscript_filepath, cpf_filepath, video_filepath, audio_filepath):
    """
    Main function to convert a .vdscript file to a .cpf file for Cuttermaran.

    Args:
        vdscript_filepath (str): Path to the .vdscript file.
        cpf_filepath (str): Path to save the .cpf file.
        video_filepath (str): Path to the video file used in Cuttermaran.
        audio_filepath (str): Path to the audio file used in Cuttermaran.
    """
    cut_segments = parse_vdscript(vdscript_filepath)
    write_cpf_file(cpf_filepath, video_filepath, audio_filepath, cut_segments)

# Usage example - EDIT THESE VALUES
if __name__ == "__main__":
    vdscript_filepath = r"C:\New folder\test.vdscript"  # Path to the .vdscript file
    cpf_filepath = r"C:\New folder\output.cpf"  # Path to save the .cpf file
    video_filepath = r"C:\New folder\test.m2v"  # Path to the video file used in Cuttermaran
    audio_filepath = r"C:\New folder\test.mp2"  # Path to the audio file used in Cuttermaran
    
    convert_vdscript_to_cpf(vdscript_filepath, cpf_filepath, video_filepath, audio_filepath)

