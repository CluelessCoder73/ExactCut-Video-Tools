import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from pathlib import Path

# VffEdit Master Orchestrator

class VffEditApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VffEdit (ExactCut Orchestrator)")
        self.root.geometry("1000x700")
        
        self.target_folder = tk.StringVar(value="No folder selected")
        self.i_frame_offset_var = tk.IntVar(value=1)
        self.min_gap_var = tk.IntVar(value=150)
        self.enable_cpf_var = tk.BooleanVar(value=False)
        
        self.scripts_dir = Path(__file__).parent / "scripts"
        
        self.build_ui()

    def build_ui(self):
        # --- TOP PANEL: Folder Selection ---
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text="Project Folder:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        ttk.Entry(top_frame, textvariable=self.target_folder, state="readonly", width=60).pack(side=tk.LEFT, padx=10)
        ttk.Button(top_frame, text="Browse...", command=self.browse_folder).pack(side=tk.LEFT)
        ttk.Button(top_frame, text="Refresh Status", command=self.update_status).pack(side=tk.LEFT, padx=10)

        # --- MAIN SPLIT ---
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # --- LEFT PANEL: Workflow & Settings ---
        left_frame = ttk.Frame(paned, width=300)
        paned.add(left_frame, weight=1)
        
        # Settings
        settings_group = ttk.LabelFrame(left_frame, text="Settings", padding=10)
        settings_group.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(settings_group, text="I-Frame Offset:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(settings_group, from_=0, to=5, textvariable=self.i_frame_offset_var, width=5).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(settings_group, text="Min Gap (frames):").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(settings_group, textvariable=self.min_gap_var, width=8).grid(row=1, column=1, sticky=tk.W)
        
        ttk.Checkbutton(settings_group, text="Enable CPF Export (Cuttermaran)", variable=self.enable_cpf_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(5,0))

        # Workflow Buttons
        workflow_group = ttk.LabelFrame(left_frame, text="Workflow Pipeline", padding=10)
        workflow_group.pack(fill=tk.BOTH, expand=True)
        
        btn_opts = {"fill": tk.X, "pady": 5, "ipady": 5}
        
        ttk.Button(workflow_group, text="Step 1: Extract Frame Logs", command=self.run_step_1).pack(**btn_opts)
        ttk.Button(workflow_group, text="Step 2: Check VFR Health", command=self.run_vfr_detector).pack(**btn_opts)
        
        ttk.Separator(workflow_group, orient='horizontal').pack(fill=tk.X, pady=10)
        
        ttk.Button(workflow_group, text="Edit Phase: VirtualDub2 Info", command=self.show_vd2_info).pack(**btn_opts)
        
        ttk.Separator(workflow_group, orient='horizontal').pack(fill=tk.X, pady=10)
        
        ttk.Button(workflow_group, text="Step 3: Analyze & Adjust Cutlists", command=self.run_step_3).pack(**btn_opts)
        ttk.Button(workflow_group, text="Step 4: Launch FFmpeg Cutter", command=self.run_step_4).pack(**btn_opts)

        # --- RIGHT PANEL: Status & Console ---
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=3)
        
        # Status Dashboard
        status_group = ttk.LabelFrame(right_frame, text="Project Status", padding=10)
        status_group.pack(fill=tk.X, pady=(0, 10))
        
        self.status_text = tk.Text(status_group, height=4, font=("Consolas", 9), bg="#f0f0f0", relief="flat")
        self.status_text.pack(fill=tk.BOTH)
        
        # Console Log
        console_group = ttk.LabelFrame(right_frame, text="Console Output", padding=10)
        console_group.pack(fill=tk.BOTH, expand=True)
        
        self.console = scrolledtext.ScrolledText(console_group, font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4")
        self.console.pack(fill=tk.BOTH, expand=True)

        self.log("VffEdit Initialized. Please select a project folder.")

    # --- UI Helpers ---
    def log(self, message):
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.target_folder.set(folder)
            self.update_status()

    def update_status(self):
        folder = self.target_folder.get()
        if not os.path.isdir(folder):
            return
            
        p = Path(folder)
        videos = [f for f in p.iterdir() if f.suffix.lower() in ['.mp4', '.m4v', '.mkv', '.mov', '.avi', '.mpv', '.m1v', '.m2v']]
        logs = list(p.glob("*_frame_log.txt"))
        vdscripts = list(p.glob("*.vdscript"))
        adjusted = list(p.glob("*_adjusted.vdscript"))
        
        self.status_text.config(state="normal")
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, f"Found {len(videos)} Video Files\n")
        self.status_text.insert(tk.END, f"Found {len(logs)} Frame Logs\n")
        self.status_text.insert(tk.END, f"Found {len(vdscripts)} Original VDScripts\n")
        self.status_text.insert(tk.END, f"Found {len(adjusted)} Adjusted Cutlists\n")
        self.status_text.config(state="disabled")

    def show_vd2_info(self):
        msg = (
            "VirtualDub2 Editing Phase\n\n"
            "1. Open your video (or proxy) in VirtualDub2.\n"
            "2. Make your cuts freely.\n"
            "3. Go to File > Save processing settings... (CTRL + S)\n"
            "4. Ensure 'Include selection and edit list' is CHECKED.\n"
            "5. Save in your project folder as exactly: [VideoName].[Ext].vdscript\n"
            "   (Example: vacation.mp4.vdscript)"
        )
        messagebox.showinfo("VirtualDub2 Instructions", msg)

    # --- Subprocess Runner ---
    def run_script_threaded(self, command, cwd):
        def worker():
            self.log(f"\n--- Running: {' '.join(command)} ---")
            try:
                process = subprocess.Popen(
                    command, 
                    cwd=cwd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, 
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                for line in process.stdout:
                    self.console.insert(tk.END, line)
                    self.console.see(tk.END)
                process.wait()
                self.log("--- Process Completed ---")
                self.root.after(0, self.update_status)
            except Exception as e:
                self.log(f"ERROR: {e}")
        
        threading.Thread(target=worker, daemon=True).start()

    # --- Workflow Steps ---
    def run_step_1(self):
        folder = self.target_folder.get()
        if not os.path.isdir(folder):
            messagebox.showerror("Error", "Select a folder first.")
            return

        # Replaces 1_Log_and_Verify.bat by safely running FFmpeg internally
        def extract_logs():
            self.log("\n--- Starting Frame Log Extraction ---")
            p = Path(folder)
            videos = [f for f in p.iterdir() if f.suffix.lower() in ['.mp4', '.m4v', '.mkv', '.mov', '.avi', '.mpv', '.m1v', '.m2v']]
            
            for vid in videos:
                log_path = p / f"{vid.name}_frame_log.txt"
                if log_path.exists():
                    self.log(f"[Skipping] Log already exists: {log_path.name}")
                    continue
                
                self.log(f"Processing: {vid.name} (This may take a moment...)")
                cmd = f'ffmpeg -i "{vid}" -vf showinfo -f null -'
                
                try:
                    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                    with open(log_path, 'w', encoding='utf-8') as log_file:
                        for line in process.stderr:
                            if "n:" in line.lower():
                                log_file.write(line)
                    self.log(f"[OK] Finished: {vid.name}")
                except Exception as e:
                    self.log(f"Error processing {vid.name}: {e}")
            
            self.log("--- Frame Log Extraction Complete ---")
            self.root.after(0, self.update_status)

        threading.Thread(target=extract_logs, daemon=True).start()

    def run_vfr_detector(self):
        folder = self.target_folder.get()
        if not os.path.isdir(folder): return
        script_path = self.scripts_dir / "exactcut_vfr_detector.pyw"
        
        # We launch the GUI version of the VFR detector so the user gets the popup
        subprocess.Popen([sys.executable, str(script_path)], cwd=folder)
        self.log("\nLaunched VFR Detector.")

    def run_step_3(self):
        folder = self.target_folder.get()
        if not os.path.isdir(folder): return
        
        # Sequence of scripts to run
        def run_analysis_pipeline():
            # 1. Adjust Ranges (passing GUI variables via argparse!)
            script_adjuster = self.scripts_dir / "vdscript_range_adjuster.py"
            self.run_script_threaded([
                sys.executable, str(script_adjuster), 
                "--dir", folder, 
                "--offset", str(self.i_frame_offset_var.get()), 
                "--mingap", str(self.min_gap_var.get())
            ], folder)
            
            # Note: In a real app we'd wait for thread completion, but for simplicity here we rely on the rapid execution. 
            # To be perfectly safe, let's just run them sequentially blocking in a single thread.
            
        def sequential_worker():
            self.log("\n=== Starting Step 3: Analysis Pipeline ===")
            cmds = [
                ([sys.executable, str(self.scripts_dir / "vdscript_range_adjuster.py"), "--dir", folder, "--offset", str(self.i_frame_offset_var.get()), "--mingap", str(self.min_gap_var.get())], "Range Adjuster"),
                ([sys.executable, str(self.scripts_dir / "gop_analyzer.py")], "GOP Analyzer"),
                ([sys.executable, str(self.scripts_dir / "vdscript_vfr_info.py")], "VFR Info Generator"),
                ([sys.executable, str(self.scripts_dir / "vdscript_to_timecode_cutlist_generator.py")], "Cutlist Generator")
            ]
            
            if self.enable_cpf_var.get():
                cmds.append(([sys.executable, str(self.scripts_dir / "vdscript_to_cpf.py")], "CPF Generator"))

            for cmd, name in cmds:
                self.log(f"\n--- Running: {name} ---")
                try:
                    proc = subprocess.run(cmd, cwd=folder, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                    if proc.stdout: self.log(proc.stdout)
                    if proc.stderr: self.log(proc.stderr)
                except Exception as e:
                    self.log(f"Error running {name}: {e}")
            
            self.log("=== Step 3 Complete ===")
            self.root.after(0, self.update_status)

        threading.Thread(target=sequential_worker, daemon=True).start()

    def run_step_4(self):
        script_path = self.scripts_dir / "exactcut_ffmpeg_cutter.pyw"
        if not script_path.exists():
            self.log("Error: Cutter script not found.")
            return
            
        # Launch Cutter GUI standalone
        subprocess.Popen([sys.executable, str(script_path)])
        self.log("\nLaunched ExactCut FFmpeg Cutter.")

if __name__ == "__main__":
    root = tk.Tk()
    app = VffEditApp(root)
    root.mainloop()