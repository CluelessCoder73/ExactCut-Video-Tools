r"""
ExactCut VFR Detector (exactcut_vfr_detector.pyw)

This script scans FFmpeg *_frame_log.txt files for Variable Frame Rate (VFR), using forgiving parameters to reduce false positives.
# Tested and works with:
# - Python 3.13.2
# - "FFmpeg" generated frame log files (the version in LosslessCut 3.64.0)

**Purpose:**
This script scans all `*_frame_log.txt` files in the chosen directory to detect whether any videos were encoded using **Variable Frame Rate (VFR)**. It also flags files with **suspiciously small frame duration differences**, which are often falsely reported as VFR by tools like MediaInfo.

The script operates in two modes:
1. GUI Mode (Interactive)

Interactive GUI for VFR detection.
How to Run:

    Double-click exactcut_vfr_detector.pyw.

GUI Elements:

    Detection Parameters:

        Ignore First N Frames: (Default: 50). Skips initial frames to avoid false VFR from zero-duration logs.

        Ignore 0.0 Duration Frames: (Default: checked). Ignores frames with 0.0 duration_time.

        Duration Tolerance (seconds): (Default: 0.00005). Treats durations as identical if their absolute difference is below this value, preventing false VFR from minor rounding errors. (0.00005s is robust for common FPS).

    Select Folder:

        Browse for Folder: Select directory containing *_frame_log.txt files.

    Action Buttons:

        Run VFR Detection: Scans files in selected folder; displays results.

        Save Output to File: Saves output to a .txt file.

    Output Text Area: Displays detection progress, status, and unique frame durations (filtered/grouped).

2. Batch Mode (Command-Line)

Automated mode for batch scripts; runs silently, saves report to file.
How to Run:

    Run from command prompt/batch file:

    python exactcut_vfr_detector.pyw --batch-mode --path "C:\path\to\your\log\files"

        --batch-mode: Non-GUI execution.

        --path: Mandatory directory for log files.

Optional Batch Mode Arguments:

    Override defaults:

        --ignore-initial-frames <number> (Default: 50)

        --ignore-zero-duration <True/False> (Default: True)

        --duration-tolerance <float> (Default: 0.00005)

Batch Mode Behavior:

    No GUI.

    Defaults: Parameters default as above if not specified.

    Output: Report automatically saves to VFR_info.txt in the --path directory. Minimal console output.

Output Report (VFR_info.txt or GUI Output)

Report details per *_frame_log.txt file:

    File Name

    Status: "VFR detected" or "CFR (or VFR ignored)" (based on forgiving settings/grouping).

    Unique Durations Found: Distinct duration_time values after filtering/grouping. Single unique duration means CFR.

    Summary: Final VFR flag indication.

Prerequisites:

    Python 3.x.

    *_frame_log.txt files (from FFmpeg showinfo).
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
    duration_tolerance # New parameter for forgiving duration differences
):
    """
    Scans a single _frame_log.txt file to detect VFR, with forgiving settings.
    Includes a tolerance for grouping similar frame durations.

    Args:
        log_file_path (str): Path to the _frame_log.txt file.
        ignore_initial_frames (int): Number of initial frames to ignore when checking for VFR.
        ignore_zero_duration (bool): If True, ignores frames with duration_time of 0.0.
        duration_tolerance (float): The maximum difference between two durations for them
                                    to be considered the same (e.g., 0.00005 for 50 microseconds).

    Returns:
        tuple: (bool, list) - (True if VFR detected after applying forgiving settings,
                               list of unique duration values found after grouping)
    """
    # We will store representative durations here.
    # Each element will be the average of a group of similar durations.
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

                    # --- New logic for grouping similar durations ---
                    found_group = False
                    for i, existing_avg_duration in enumerate(unique_grouped_durations):
                        if abs(duration_time - existing_avg_duration) < duration_tolerance:
                            # If the current duration is within tolerance of an existing group,
                            # update the average of that group. This is a simplified approach
                            # but effective for VFR detection.
                            # A more robust approach would track all members of the group
                            # and re-calculate the average, but for just checking uniqueness,
                            # this simple update or just marking as found is sufficient.
                            # For simplicity and performance, we'll just mark it as found.
                            found_group = True
                            break
                    
                    if not found_group:
                        # If it doesn't fit into any existing group, add it as a new unique duration
                        unique_grouped_durations.append(duration_time)
                    # --- End new logic ---

    except Exception as e:
        # Return False and an empty list if there's an error
        return False, []

    # VFR is detected if, after grouping, there's more than one unique duration
    is_vfr = len(unique_grouped_durations) > 1
    return is_vfr, unique_grouped_durations

# Function for batch mode operation
def run_detection_and_save_to_file(folder_path, output_filename="VFR_info.txt",
                                   ignore_initial_frames=50, ignore_zero_duration=True,
                                   duration_tolerance=0.00005): # New default for batch mode
    """
    Performs VFR detection for all _frame_log.txt files in a given folder
    and saves the results to a specified text file.
    Designed for non-GUI (batch) usage.
    """
    log_files = [f for f in os.listdir(folder_path) if f.endswith('_frame_log.txt')]

    output_lines = []
    vfr_videos_detected = False

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
            is_vfr, durations = vfr_detector_forgiving( # Pass new tolerance parameter
                full_log_path,
                ignore_initial_frames,
                ignore_zero_duration,
                duration_tolerance # Pass the tolerance
            )

            output_lines.append(f"{log_file}:\n")
            output_lines.append(f"  Status: {'VFR detected' if is_vfr else 'CFR (or VFR ignored)'}\n")
            output_lines.append("  Unique Durations Found (after filtering and grouping):\n")
            if durations:
                # Sort the durations for consistent output, even though they are "representatives"
                for d in sorted(list(durations)):
                    output_lines.append(f"    - {d}\n")
            else:
                output_lines.append("    No valid durations found after filtering.\n")
            output_lines.append("-" * 40 + "\n\n")

            if is_vfr:
                vfr_videos_detected = True

    output_lines.append("\n# Summary\n")
    if vfr_videos_detected:
        output_lines.append("WARNING: One or more videos appear to use Variable Frame Rate (VFR) even after applying forgiving detection.\n")
        output_lines.append("Ensure duration-based cutlists are accurate for these.\n")
    else:
        output_lines.append("All videos appear to use Constant Frame Rate (CFR) based on forgiving detection.\n")
        output_lines.append("No VFR issues detected that should impact duration-based cutlists.\n")

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

        # New GUI element for duration tolerance
        tk.Label(self.params_frame, text="Duration Tolerance (seconds):", bg="#34495e", fg="white").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.duration_tolerance_var = tk.DoubleVar(value=0.00005) # Default tolerance
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

        # Validate duration tolerance input
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
        self.duration_tolerance_entry.config(state=tk.DISABLED) # Disable new entry

        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, "--- Running VFR Detection (Please wait, this may take a moment) ---\n\n")

        self.detection_thread = threading.Thread(target=self._run_detection_threaded_gui)
        self.detection_thread.start()

    def _run_detection_threaded_gui(self):
        log_files = [f for f in os.listdir(self.current_folder) if f.endswith('_frame_log.txt')]

        output_lines_for_gui = []
        vfr_videos_detected = False

        if not log_files:
            output_lines_for_gui.append("No *_frame_log.txt files found in the selected directory.\n")
            output_lines_for_gui.append("\n--- Detection Complete ---\n")
        else:
            initial_frames = self.initial_frames_var.get()
            ignore_zero_duration = self.ignore_zero_duration_var.get()
            duration_tolerance = self.duration_tolerance_var.get() # Get tolerance from GUI

            output_lines_for_gui.append(f"Scanning with forgiving settings:\n")
            output_lines_for_gui.append(f"  - Ignore first {initial_frames} frames: {'Yes' if initial_frames > 0 else 'No'}\n")
            output_lines_for_gui.append(f"  - Ignore 0.0 duration frames: {'Yes' if ignore_zero_duration else 'No'}\n")
            output_lines_for_gui.append(f"  - Duration tolerance: {duration_tolerance} seconds\n\n") # Add to GUI output
            
            for log_file in log_files:
                full_log_path = os.path.join(self.current_folder, log_file)
                is_vfr, durations = vfr_detector_forgiving(
                    full_log_path,
                    initial_frames,
                    ignore_zero_duration,
                    duration_tolerance # Pass tolerance to the detector
                )

                output_lines_for_gui.append(f"{log_file}:\n")
                output_lines_for_gui.append(f"  Status: {'VFR detected' if is_vfr else 'CFR (or VFR ignored)'}\n")
                output_lines_for_gui.append("  Unique Durations Found (after filtering and grouping):\n")
                if durations:
                    for d in sorted(list(durations)): # Sort for consistent output
                        output_lines_for_gui.append(f"    - {d}\n")
                else:
                    output_lines_for_gui.append("    No valid durations found after filtering.\n")
                output_lines_for_gui.append("-" * 40 + "\n\n")

                if is_vfr:
                    vfr_videos_detected = True

            output_lines_for_gui.append("\n# Summary\n")
            if vfr_videos_detected:
                output_lines_for_gui.append("WARNING: One or more videos appear to use Variable Frame Rate (VFR) even after applying forgiving detection.\n")
                output_lines_for_gui.append("Ensure duration-based cutlists are accurate for these.\n")
            else:
                output_lines_for_gui.append("All videos appear to use Constant Frame Rate (CFR) based on forgiving detection.\n")
                output_lines_for_gui.append("No VFR issues detected that should impact duration-based cutlists.\n")

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
        self.duration_tolerance_entry.config(state=tk.NORMAL) # Re-enable new entry

        messagebox.showinfo("Detection Complete", "VFR detection process finished!")

    def save_output(self):
        if not self.output_text.get(1.0, tk.END).strip():
            messagebox.showwarning("No Output", "There is no output to save yet. Please run detection first.")
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
    parser.add_argument('--duration-tolerance', type=float, default=0.00005,
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

