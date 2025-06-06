"""
User Guide for vdscript_to_mkvtoolnix.py
# Tested and works with:
# - Python 3.13.2
# - VirtualDub2 (build 44282) .vdscript files
# - MKVToolNix GUI v91.0 ("Signs") 64-bit

Features

    Processes all *_adjusted.vdscript files in current directory

    Generates single batch_cutlist.txt file

    Optional merge mode with + prefixes

    Maintains original file names in output

Requirements

    Python 3.x

    VirtualDub/VirtualDub2 generated *_adjusted.vdscript files

Usage

    Place script and *_adjusted.vdscript files in same directory

    Run command prompt in directory

    Execute one of:

    # Basic mode (separate parts)
    python vdscript_to_mkvtoolnix.py

    # Merge mode (concatenated parts)
    python vdscript_to_mkvtoolnix.py --merge

Output Format

Example batch_cutlist.txt:

"video1_adjusted.vdscript"
0-249,750-1249,1500-1766

"video2_adjusted.vdscript"
500-1249,1750-1999,3000-3499

With merge enabled:

"video1_adjusted.vdscript"
0-249,+750-1249,+1500-1766

"video2_adjusted.vdscript"
500-1249,+1750-1999,+3000-3499

Using with MKVToolNix GUI

    Open MKVToolNix GUI

    Add your video file

    Go to "Output" tab

    Under "Splitting":

        Select "By parts based on frame/field numbers"

        Paste the cutlist string (without quotes/filename) into the input field

    Start multiplexing

Notes

    The script ignores non-matching files

    Empty ranges are skipped

    Frame numbers are 0-based

    Merge mode adds + to create single output file with concatenated segments
"""
import os
import re
import argparse

def parse_vdscript(file_path):
    ranges = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('VirtualDub.subset.AddRange'):
                match = re.search(r'AddRange\((\d+),(\d+)\)', line)
                if match:
                    start = int(match.group(1))
                    length = int(match.group(2))
                    end = start + length - 1  # Inclusive end frame
                    ranges.append((start, end))
    return ranges

def format_cutlist(ranges, merge=False):
    if not ranges:
        return ""
        
    if merge:
        # First range without +, others with +
        return ",".join([f"{r[0]}-{r[1]}" if i == 0 else f"+{r[0]}-{r[1]}" 
                       for i, r in enumerate(ranges)])
    else:
        return ",".join([f"{r[0]}-{r[1]}" for r in ranges])

def batch_process_vdscripts(directory, output_file, merge):
    with open(output_file, 'w') as outfile:
        for filename in os.listdir(directory):
            if filename.endswith('_adjusted.vdscript'):
                file_path = os.path.join(directory, filename)
                ranges = parse_vdscript(file_path)
                cutlist = format_cutlist(ranges, merge)
                
                outfile.write(f'"{filename}"\n')
                outfile.write(f"{cutlist}\n\n")

def main():
    parser = argparse.ArgumentParser(description='Batch convert vdscript files to MKVToolNix cutlists')
    parser.add_argument('--merge', action='store_true',
                       help='Enable merge mode with + prefixes')
    args = parser.parse_args()

    directory = '.'  # Current directory
    output_file = 'batch_cutlist.txt'
    
    batch_process_vdscripts(directory, output_file, args.merge)
    print(f"Batch cutlist generated: {output_file}")

if __name__ == "__main__":
    main()
