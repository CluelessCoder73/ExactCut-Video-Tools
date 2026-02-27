r"""
ExactCut VFR Detector (exactcut_vfr_detector.pyw)

This script scans FFmpeg *_frame_log.txt files for Variable Frame Rate (VFR), using forgiving parameters to reduce false positives.
# Tested and works with:
# - Python 3.13.7
# - "FFmpeg" generated frame log files (the version in LosslessCut 3.68.0)

**Purpose:**
This script scans all `*_frame_log.txt` files in the chosen directory to detect whether any videos were encoded using **Variable Frame Rate (VFR)**. It also flags files with **suspiciously small frame duration differences**, which are often falsely reported as VFR by tools like MediaInfo.

It now distinguishes between "Healthy VFR" (a few unique frame rates) and "Suspicious Timestamps" (extreme jitter), allowing you to fix broken files before cutting.
"""
import os
import re
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading
import sys
import argparse

def vfr_detector_forgiving(
    log_file_path,
    ignore_initial_frames,
    ignore_zero_duration,
    duration_tolerance,
    suspicious_threshold=20
):
    """
    Scans a single _frame_log.txt file to detect VFR, with forgiving settings.
    Includes a tolerance for grouping similar frame durations and a threshold 
    to detect extreme jitter (Suspicious Timestamps).
    """
    unique_grouped_durations = []
    log_pattern = re.compile(r"n:(\d+)\s+.*?duration_time:([0-9.]+)")

    try:
        with open(log_file_path, 'r') as f:
            for line in f:
                match = log_pattern.search(line)
                if match:
                    frame_number = int(match.group(1))
                    duration_time = float(match.group(2))

                    if frame_number < ignore_initial_frames:
                        continue

                    if ignore_zero_duration and duration_time == 0.0:
                        continue

                    found_group = False
                    for i, existing_avg_duration in enumerate(unique_grouped_durations):
                        if abs(duration_time - existing_avg_duration) < duration_tolerance:
                            found_group = True
                            break
                    
                    if not found_group:
                        unique_grouped_durations.append(duration_time)

    except Exception as e:
        return "ERROR", []

    # Determine status based on the number of unique groups
    unique_count = len(unique_grouped_durations)
    if unique_count <= 1:
        status = "CFR"
    elif unique_count <= suspicious_threshold:
        status = "VFR_HEALTHY"
    else:
        status = "VFR_SUSPICIOUS"

    return status, unique_grouped_durations

# Function for batch mode operation
def run_detection_and_save_to_file(folder_path, output_filename="VFR_info.txt",
                                   ignore_initial_frames=50, ignore_zero_duration=True,
                                   duration_tolerance=0.001):
    """
    Performs VFR detection for all _frame_log.txt files in a given folder
    and saves the results to a specified text file.
    """
    log_files = [f for f in os.listdir(folder_path) if f.endswith('_frame_log.txt')]

    output_lines = []
    vfr_videos_detected = False
    suspicious_videos_detected = False

    output_lines.append("--- ExactCut VFR Detector Report ---\n")
    output_lines.append(f"Scanning directory: {folder_path}\n")
    output_lines.append(f"Scanning with forgiving settings:\n")
    output_lines.append(f"  - Ignore first {ignore_initial_frames} frames: {'Yes' if ignore_initial_frames > 0 else 'No'}\n")
    output_lines.append(f"  - Ignore 0.0 duration frames: {'Yes' if ignore_zero_duration else 'No'}\n")
    output_lines.append(f"  - Duration tolerance: {duration_tolerance} seconds\n\n")

    if not log_files:
        output_lines.append("No *_frame_log.txt files found in the specified directory.\n")
    else:
        for log_file in log_files:
            full_log_path = os.path.join(folder_path, log_file)
            status, durations = vfr_detector_forgiving(
                full_log_path,
                ignore_initial_frames,
                ignore_zero_duration,
                duration_tolerance
            )

            output_lines.append(f"{log_file}:\n")
            
            if status == "CFR":
                output_lines.append("  Status: CFR (or VFR ignored)\n")
            elif status == "VFR_HEALTHY":
                output_lines.append("  Status: VFR NOTED (Healthy Variable Frame Rate)\n")
                vfr_videos_detected = True
            elif status == "VFR_SUSPICIOUS":
                output_lines.append("  Status: SUSPICIOUS TIMESTAMPS (Extreme Jitter Detected!)\n")
                suspicious_videos_detected = True
            else:
                output_lines.append("  Status: Error reading file.\n")

            output_lines.append(f"  Unique Durations Found ({len(durations)} groups): \n")
            if durations:
                for d in sorted(list(durations)):
                    output_lines.append(f"    - {d}\n")
            else:
                output_lines.append("    No valid durations found after filtering.\n")
            output_lines.append("-" * 40 + "\n\n")

    output_lines.append("\n# Summary\n")
    
    # Priority 1: Suspicious Timestamps
    if suspicious_videos_detected:
        output_lines.append("ALERT: SUSPICIOUS TIMESTAMPS DETECTED!\n")
        output_lines.append("One or more videos exhibit extreme frame duration jitter (>10 unique durations).\n")
        output_lines.append("It is highly recommended to remux these specific videos using the '-video_track_timescale 90k' FFmpeg command before cutting to prevent frame loss.\n")
    # Priority 2: Healthy VFR
    elif vfr_videos_detected:
        output_lines.append("VFR NOTED: Variable Frame Rate was detected in one or more files.\n")
    # Priority 3: CFR
    else:
        output_lines.append("All videos appear to use Constant Frame Rate (CFR) based on forgiving detection.\n")

    output_lines.append("\n--- Report End ---\n")

    try:
        output_file_path = os.path.join(folder_path, output_filename)
        with open(output_file_path, 'w') as f:
            f.write("".join(output_lines))
        print(f"VFR detection report saved to: {output_file_path}")
    except Exception as e:
        print(f"Error saving VFR report to file: {e}")


class VFRDetectorApp:
    def __init__(self, master):
        self.master = master
        master.title("ExactCut VFR Detector")
        master.geometry("800x700")
        master.configure(bg="#2c3e50")

        self.master.option_add("*Font", "Inter 10")

        # --- Parameters Frame ---
        self.params_frame = tk.LabelFrame(master, text="Detection Parameters", padx=15, pady=15, bg="#34495e", fg="white", bd=2, relief="groove")
        self.params_frame.pack(pady=15, padx=20, fill="x")

        tk.Label(self.params_frame, text="Ignore First N Frames:", bg="#34495e", fg="white").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.initial_frames_var = tk.IntVar(value=50)
        self.initial_frames_entry = tk.Spinbox(self.params_frame, from_=0, to_=1000, textvariable=self.initial_frames_var, width=8, bg="#ecf0f1", fg="#2c3e50", bd=1, relief="flat")
        self.initial_frames_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(self.params_frame, text="Ignore 0.0 Duration Frames:", bg="#34495e", fg="white").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.ignore_zero_duration_var = tk.BooleanVar(value=True)
        self.ignore_zero_duration_check = tk.Checkbutton(self.params_frame, variable=self.ignore_zero_duration_var, bg="#34495e", fg="white", selectcolor="#34495e", activebackground="#34495e", activeforeground="white")
        self.ignore_zero_duration_check.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        tk.Label(self.params_frame, text="Duration Tolerance (seconds):", bg="#34495e", fg="white").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.duration_tolerance_var = tk.DoubleVar(value=0.001)
        self.duration_tolerance_entry = tk.Entry(self.params_frame, textvariable=self.duration_tolerance_var, width=12, bg="#ecf0f1", fg="#2c3e50", bd=1, relief="flat")
        self.duration_tolerance_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        self.params_frame.grid_columnconfigure(1, weight=1)

        # --- Folder Selection Frame ---
        self.folder_frame = tk.LabelFrame(master, text="Select Folder", padx=15, pady=15, bg="#34495e", fg="white", bd=2, relief="groove")
        self.folder_frame.pack(pady=10, padx=20, fill="x")

        self.folder_path_var = tk.StringVar(value="No folder selected")
        self.folder_label = tk.Label(self.folder_frame, textvariable=self.folder_path_var, bg="#ecf0f1", fg="#2c3e50", padx=10, pady=8, relief="solid", bd=1, anchor="w")
        self.folder_label.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.browse_button = tk.Button(self.folder_frame, text="Browse for Folder", command=self.browse_folder,
                                       bg="#27ae60", fg="white", activebackground="#2ecc71", activeforeground="white",
                                       relief="raised", bd=2, padx=10, pady=5, cursor="hand2")
        self.browse_button.pack(side="right")

        # --- Action Buttons Frame ---
        self.action_frame = tk.Frame(master, bg="#2c3e50")
        self.action_frame.pack(pady=10, padx=20, fill="x")

        self.run_button = tk.Button(self.action_frame, text="Run VFR Detection", command=self.start_detection_thread,
                                    bg="#3498db", fg="white", activebackground="#2980b9", activeforeground="white",
                                    relief="raised", bd=2, padx=15, pady=8, cursor="hand2")
        self.run_button.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.save_button = tk.Button(self.action_frame, text="Save Output to File", command=self.save_output,
                                     bg="#9b59b6", fg="white", activebackground="#8e44ad", activeforeground="white",
                                     relief="raised", bd=2, padx=15, pady=8, cursor="hand2")
        self.save_button.pack(side="right", expand=True, fill="x", padx=(5, 0))

        # --- Output Text Area ---
        self.output_text = scrolledtext.ScrolledText(master, wrap=tk.WORD, bg="#ecf0f1", fg="#2c3e50", bd=2, relief="sunken", padx=10, pady=10)
        self.output_text.pack(pady=15, padx=20, fill="both", expand=True)

        self.current_folder = ""

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.current_folder = folder_selected
            self.folder_path_var.set(folder_selected)
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, f"Selected folder: {self.current_folder}\nReady to run detection.\n")

    def start_detection_thread(self):
        if not self.current_folder:
            messagebox.showwarning("No Folder Selected", "Please select a folder containing _frame_log.txt files first.")
            return

        try:
            tolerance_val = float(self.duration_tolerance_var.get())
            if tolerance_val < 0:
                raise ValueError("Tolerance cannot be negative.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Duration Tolerance must be a non-negative number.")
            return

        self.run_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        self.browse_button.config(state=tk.DISABLED)
        self.initial_frames_entry.config(state=tk.DISABLED)
        self.ignore_zero_duration_check.config(state=tk.DISABLED)
        self.duration_tolerance_entry.config(state=tk.DISABLED)

        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, "--- Running VFR Detection (Please wait, this may take a moment) ---\n\n")

        self.detection_thread = threading.Thread(target=self._run_detection_threaded_gui)
        self.detection_thread.start()

    def _run_detection_threaded_gui(self):
        log_files = [f for f in os.listdir(self.current_folder) if f.endswith('_frame_log.txt')]

        output_lines_for_gui = []
        vfr_videos_detected = False
        suspicious_videos_detected = False

        if not log_files:
            output_lines_for_gui.append("No *_frame_log.txt files found in the selected directory.\n")
            output_lines_for_gui.append("\n--- Detection Complete ---\n")
        else:
            initial_frames = self.initial_frames_var.get()
            ignore_zero_duration = self.ignore_zero_duration_var.get()
            duration_tolerance = self.duration_tolerance_var.get()

            output_lines_for_gui.append(f"Scanning with forgiving settings:\n")
            output_lines_for_gui.append(f"  - Ignore first {initial_frames} frames: {'Yes' if initial_frames > 0 else 'No'}\n")
            output_lines_for_gui.append(f"  - Ignore 0.0 duration frames: {'Yes' if ignore_zero_duration else 'No'}\n")
            output_lines_for_gui.append(f"  - Duration tolerance: {duration_tolerance} seconds\n\n")
            
            for log_file in log_files:
                full_log_path = os.path.join(self.current_folder, log_file)
                status, durations = vfr_detector_forgiving(
                    full_log_path,
                    initial_frames,
                    ignore_zero_duration,
                    duration_tolerance
                )

                output_lines_for_gui.append(f"{log_file}:\n")
                
                if status == "CFR":
                    output_lines_for_gui.append("  Status: CFR (or VFR ignored)\n")
                elif status == "VFR_HEALTHY":
                    output_lines_for_gui.append("  Status: VFR NOTED (Healthy Variable Frame Rate)\n")
                    vfr_videos_detected = True
                elif status == "VFR_SUSPICIOUS":
                    output_lines_for_gui.append("  Status: SUSPICIOUS TIMESTAMPS (Extreme Jitter Detected!)\n")
                    suspicious_videos_detected = True
                else:
                    output_lines_for_gui.append("  Status: Error reading file.\n")

                output_lines_for_gui.append(f"  Unique Durations Found ({len(durations)} groups): \n")
                if durations:
                    for d in sorted(list(durations)): 
                        output_lines_for_gui.append(f"    - {d}\n")
                else:
                    output_lines_for_gui.append("    No valid durations found after filtering.\n")
                output_lines_for_gui.append("-" * 40 + "\n\n")

            output_lines_for_gui.append("\n# Summary\n")
            
            if suspicious_videos_detected:
                output_lines_for_gui.append("ALERT: SUSPICIOUS TIMESTAMPS DETECTED!\n")
                output_lines_for_gui.append("One or more videos exhibit extreme frame duration jitter (>10 unique durations).\n")
                output_lines_for_gui.append("It is highly recommended to remux these specific videos using the '-video_track_timescale 90k' FFmpeg command before cutting to prevent frame loss.\n")
            elif vfr_videos_detected:
                output_lines_for_gui.append("VFR NOTED: Variable Frame Rate was detected in one or more files.\n")
            else:
                output_lines_for_gui.append("All videos appear to use Constant Frame Rate (CFR) based on forgiving detection.\n")

            output_lines_for_gui.append("\n--- Detection Complete ---\n")

        self.master.after(0, self._update_gui_after_detection, "".join(output_lines_for_gui))

    def _update_gui_after_detection(self, output_text_content):
        self.output_text.insert(tk.END, output_text_content)
        self.output_text.see(tk.END)

        self.run_button.config(state=tk.NORMAL)
        self.save_button.config(state=tk.NORMAL)
        self.browse_button.config(state=tk.NORMAL)
        self.initial_frames_entry.config(state=tk.NORMAL)
        self.ignore_zero_duration_check.config(state=tk.NORMAL)
        self.duration_tolerance_entry.config(state=tk.NORMAL) 

        messagebox.showinfo("Detection Complete", "VFR detection process finished!")

    def save_output(self):
        if not self.output_text.get(1.0, tk.END).strip():
            messagebox.showwarning("No Output", "There is no output to save yet.\nPlease run detection first.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save VFR Detection Report"
        )
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(self.output_text.get(1.0, tk.END))
                messagebox.showinfo("Save Successful", f"Output saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save output: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ExactCut VFR Detector")
    parser.add_argument('--batch-mode', action='store_true',
                        help='Run in batch mode (non-GUI) and save output to VFR_info.txt.')
    parser.add_argument('--path', type=str,
                        help='Path to the folder containing _frame_log.txt files (required in batch mode).')
    parser.add_argument('--ignore-initial-frames', type=int, default=50,
                        help='Number of initial frames to ignore (batch mode only).')
    parser.add_argument('--ignore-zero-duration', type=bool, default=True,
                        help='Whether to ignore 0.0 duration frames (batch mode only).')
    parser.add_argument('--duration-tolerance', type=float, default=0.001,
                        help='Tolerance for grouping similar frame durations (batch mode only).')
    args = parser.parse_args()

    if args.batch_mode:
        if not args.path:
            print("Error: --path argument is required in batch mode.")
            sys.exit(1)
        if not os.path.isdir(args.path):
            print(f"Error: Provided path '{args.path}' is not a valid directory.")
            sys.exit(1)
        
        run_detection_and_save_to_file(args.path, 
                                       ignore_initial_frames=args.ignore_initial_frames,
                                       ignore_zero_duration=args.ignore_zero_duration,
                                       duration_tolerance=args.duration_tolerance)
    else:
        root = tk.Tk()
        app = VFRDetectorApp(root)
        root.mainloop()