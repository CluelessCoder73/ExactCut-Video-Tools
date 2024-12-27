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

def adjust_range(start, length, frame_types, i_frame_offset):
    new_start = find_nth_previous_i_frame(start, frame_types, i_frame_offset)
    end = start + length - 1
    new_end = find_last_p_frame_before_next_i(end, frame_types)
    
    if new_end is None:
        new_end = end
    
    new_length = new_end - new_start + 1
    return new_start, new_length

def process_vdscript(input_file, output_file, frame_types, i_frame_offset):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            if line.startswith('VirtualDub.subset.AddRange'):
                match = re.search(r'AddRange\((\d+),(\d+)\)', line)
                if match:
                    start, length = int(match.group(1)), int(match.group(2))
                    new_start, new_length = adjust_range(start, length, frame_types, i_frame_offset)
                    new_line = f'VirtualDub.subset.AddRange({new_start},{new_length});\n'
                    outfile.write(new_line)
                else:
                    outfile.write(line)
            else:
                outfile.write(line)

# Main execution
frame_log_file = 'frame_log.txt'
input_vdscript = 'input.vdscript'
output_vdscript = 'output.vdscript'
i_frame_offset = 1  # Change this value to go further back in I-frames

frame_types = read_frame_log(frame_log_file)
process_vdscript(input_vdscript, output_vdscript, frame_types, i_frame_offset)

print("Conversion completed. Check output.vdscript for the result.")
