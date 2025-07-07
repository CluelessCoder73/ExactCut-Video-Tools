# vfr_detector.py
# Standalone script to detect VFR in all *_frame_log.txt files in the current directory

import os
import re

def detect_vfr_in_log(file_path):
    durations = set()
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if 'Parsed_showinfo_0' in line:
                    match = re.search(r'duration_time:([\d.]+)', line)
                    if match:
                        dur = round(float(match.group(1)), 6)
                        durations.add(dur)
        return len(durations) > 1, sorted(durations)
    except Exception as e:
        return False, [f"Error reading file: {e}"]

def main():
    current_dir = os.getcwd()
    log_files = [f for f in os.listdir(current_dir) if f.endswith('_frame_log.txt')]
    report_lines = []
    any_vfr = False

    for log_file in sorted(log_files):
        full_path = os.path.join(current_dir, log_file)
        is_vfr, result = detect_vfr_in_log(full_path)
        status = "VFR detected" if is_vfr else "Constant frame rate"
        if is_vfr:
            any_vfr = True
        report_lines.append(f"{log_file}: {status}")
        if isinstance(result, list):
            for dur in result:
                report_lines.append(f"    duration_time: {dur}")
        report_lines.append("")

    report_lines.append("# Summary")
    if any_vfr:
        report_lines.append("WARNING: One or more videos appear to use Variable Frame Rate (VFR).")
        report_lines.append("Ensure duration-based cutlists are accurate for these.")
    else:
        report_lines.append("Frame rate mode for all videos: Constant")

    with open("VFR_info.txt", 'w', encoding='utf-8') as out:
        out.write("\n".join(report_lines))

    print("VFR detection complete. Results written to VFR_info.txt")

if __name__ == "__main__":
    main()
