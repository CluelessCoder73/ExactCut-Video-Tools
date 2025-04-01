import re
import os

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

def generate_mkvmerge_command(ranges, input_file, output_file):
    # Update this path to your mkvmerge executable!
    mkvmerge_path = r'"C:\PortableApps\mkvtoolnix\mkvmerge.exe"'
    
    # Create frame-based split string
    split_string = ",".join([f"{start}-{end}" for start, end in ranges])
    
    # Generate mkvmerge command
    command = f'{mkvmerge_path} --split parts-frames:{split_string} -o "{output_file}" "{input_file}"'
    return command

# Main execution
vdscript_file = 'input_adjusted.vdscript'  # Your vdscript file
input_video = 'input.mkv'                 # Input video file
output_video = 'output.mkv'               # Output file name

# Parse vdscript and generate command
ranges = parse_vdscript(vdscript_file)
command = generate_mkvmerge_command(ranges, input_video, output_video)

# Print and execute the command
print("Generated command:")
print(command)
os.system(command)
