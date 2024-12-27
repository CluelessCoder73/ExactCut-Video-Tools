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
    
    if new_end is None:
        new_end = end
    
    new_length = new_end - new_start + 1
    return new_start, new_length

def find_next_p_or_i_frame(frame_num, frame_types):
    max_frame = max(frame_types.keys())
    next_frame = frame_num + 1
    while next_frame <= max_frame:
        if frame_types.get(next_frame) in ['I', 'P']:
            return next_frame
        next_frame += 1
    return None

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

# Main execution
frame_log_file = 'frame_log.txt'
input_vdscript = 'input.vdscript'
output_vdscript = 'output.vdscript'
i_frame_offset = 1  # Change this value to go further back in I-frames
merge_ranges_option = True  # Set to False to disable merging
min_gap_between_ranges = 100  # Minimum gap between ranges (in frames)
short_cut_mode = True  # Set to True to enable shortcut mode for endpoint adjustment

frame_types = read_frame_log(frame_log_file)
process_vdscript(input_vdscript, output_vdscript, frame_types, i_frame_offset, merge_ranges_option, min_gap_between_ranges, short_cut_mode)

print("Conversion completed. Check output.vdscript for the result.")
