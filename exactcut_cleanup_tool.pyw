import tkinter as tk
from tkinter import filedialog, messagebox
import os
import shutil

# Tested and works with:
# - Python 3.13.2

# --- File patterns and script names ---
CORRESPONDING_EXTENSIONS = [
    '.cutlist.txt', '_adjusted.vdscript', '_adjusted_info.txt', '_info.txt'
]
EXTRA_FILES = ['gop_info.txt', 'VFR_info.txt']
SCRIPTS_LIST = [
    'exactcut_vfr_detector.pyw', 'frame_log_extractor.bat',
    'gop_analyzer.py', 'run_python_scripts.bat',
    'vdscript_info.py', 'vdscript_range_adjuster.py',
    'vdscript_to_timecode_cutlist_generator.py'
]
ORIGINALS_EXT = ['.vdscript', '_frame_log.txt']

def move_files(base_folder, files_to_move):
    delete_folder = os.path.join(base_folder, 'delete')
    os.makedirs(delete_folder, exist_ok=True)
    for file_path in files_to_move:
        if os.path.exists(file_path):
            try:
                shutil.move(file_path, delete_folder)
            except Exception as e:
                print(f"Error moving {file_path}: {e}")

def get_video_files(folder):
    exts = ('.mp4', '.mkv', '.mov', '.avi', '.ts', '.wmv')
    return [f for f in os.listdir(folder) if f.lower().endswith(exts)]

def collect_corresponding_files(folder, video_files):
    files = []
    for video in video_files:
        base = os.path.join(folder, video)
        for ext in CORRESPONDING_EXTENSIONS:
            f = base + ext
            if os.path.exists(f):
                files.append(f)
    for name in EXTRA_FILES:
        f = os.path.join(folder, name)
        if os.path.exists(f): files.append(f)
    return files

def collect_scripts(folder):
    files = []
    for name in SCRIPTS_LIST:
        f = os.path.join(folder, name)
        if os.path.exists(f): files.append(f)
    return files

def collect_originals(folder, video_files):
    files = []
    for video in video_files:
        base = os.path.join(folder, video)
        for ext in ORIGINALS_EXT:
            f = base + ext
            if os.path.exists(f): files.append(f)
    return files

# --- Tkinter App ---
class CleanupApp:
    def __init__(self, master):
        self.master = master
        master.title("ExactCut Cleanup Tool")  # Set the GUI title bar

        self.folder = tk.StringVar()
        self.remove_scripts = tk.BooleanVar()
        self.remove_originals = tk.BooleanVar()

        # Folder selection
        tk.Label(master, text="Select folder:").pack(anchor="w")
        frame = tk.Frame(master)
        frame.pack(fill="x")
        tk.Entry(frame, textvariable=self.folder, width=50).pack(side="left", expand=1, fill="x")
        tk.Button(frame, text="Browse", command=self.browse_folder).pack(side="right")

        # Checkbox options
        tk.Checkbutton(master, text="Remove scripts", variable=self.remove_scripts).pack(anchor="w")
        tk.Checkbutton(master, text="Remove original vdscripts & frame logs",
                       variable=self.remove_originals).pack(anchor="w")

        # Action buttons
        button_frame = tk.Frame(master)
        button_frame.pack(pady=12, fill="x")
        tk.Button(button_frame, text="Run Cleanup", command=self.cleanup).pack(side="left")
        tk.Button(button_frame, text="Help", command=self.show_help).pack(side="right")  # <--- Help Button

        tk.Label(master, text="(Created for your workflow)", fg="gray").pack(side="bottom")
    
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder.set(folder)

    def cleanup(self):
        folder = self.folder.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder.")
            return

        video_files = get_video_files(folder)
        files_to_move = collect_corresponding_files(folder, video_files)

        # Scripts
        if self.remove_scripts.get():
            files_to_move += collect_scripts(folder)

        # Originals
        if self.remove_originals.get():
            originals = collect_originals(folder, video_files)
            if originals:
                ans = messagebox.askyesno(
                    "Warning",
                    "This will move the original vdscripts and frame logs to the 'delete' folder.\n\n"
                    "These files may take a long time to recreate. Are you sure you want to continue?"
                )
                if ans:
                    files_to_move += originals
                else:
                    # Do not proceed with originals
                    pass

        if files_to_move:
            move_files(folder, files_to_move)
            messagebox.showinfo("Cleanup", "Cleanup complete.")
        else:
            messagebox.showinfo("Cleanup", "No files to move.")

    def show_help(self):  # <--- Help function
        help_text = (
            "ExactCut Cleanup Tool — Help\n\n"
            "This tool helps you declutter folders containing video projects created using scripts from the ExactCut-Video-Tools suite.\n\n"
            "Default behaviour:\n"
            "- Moves any temporary or output files that are generated next to your video files (like .cutlist.txt, _info.txt, etc) into a new 'delete' subfolder.\n"
            "- Also moves gop_info.txt and VFR_info.txt if found.\n"
            "- Original video files (.mp4, .mkv, etc) are never moved by default.\n\n"
            '"Remove scripts" checkbox:\n'
            "- If checked, moves helper/automation scripts into 'delete'.\n\n"
            '"Remove original vdscripts & frame logs" checkbox:\n'
            "- If checked, moves original .vdscript files and frame logs into 'delete'.\n"
            "WARNING: These originals can take DAYS to re-create!\n"
            "Always make sure you have backed up anything important.\n\n"
            "Usage:\n"
            "1. Select your folder with the Browse button.\n"
            "2. Choose options as needed.\n"
            "3. Click Run Cleanup.\n"
            "4. Review files in the delete subfolder before deleting permanently.\n\n"
            "See the scripts folder and README.md in the ExactCut-Video-Tools GitHub repo for details."
        )
        messagebox.showinfo("Help — ExactCut Cleanup Tool", help_text)

if __name__ == '__main__':
    root = tk.Tk()
    app = CleanupApp(root)
    root.mainloop()
