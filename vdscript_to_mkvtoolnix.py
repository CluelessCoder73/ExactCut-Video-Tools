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
