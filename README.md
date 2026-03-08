# ExactCut Video Tools: A Lossless, VFR-Aware Cutlist Pipeline

ExactCut is a suite of Python and Batch scripts designed to bridge the gap between visually editing video via proxy files and performing frame-accurate, lossless cuts using FFmpeg.

This workflow guarantees that no frames are lost, prevents desync issues common with Variable Frame Rate (VFR) footage, and automatically snaps your edits to safe I-frame boundaries.

---

## 📂 Directory Setup

Before you begin, your working folder must be prepared correctly. The scripts look for specific files in the same directory to function.

**Your folder must contain:**

1. **Source Video(s):** The original files.
2. **The Entire Scripts Folder:** The contents of `\ExactCut-Video-Tools\scripts` must be copied here.
* **Crucial:** For "Open GOP" codecs (like x265), you must set "i_frame_offset" to "2" in `vdscript_range_adjuster.py`.
3. **Correctly Named `.vdscript` Files:** Once you finish editing, your VirtualDub2 scripts must follow this strict format:
`[Source_Video_Name].[Original_Extension].vdscript`

> **Example:** > If your source is `Vacation.mp4`, your script **must** be named `Vacation.mp4.vdscript`.

---

## 🛠️ The Workflow Pipeline

### Phase 1: Preparation & Editing

> **⚠️ PRO-TIP: Organize by Framerate!** > We highly recommend placing videos with different framerates into separate folders. The ExactCut FFmpeg Cutter uses a default "Seek Nudge" of 133ms.
> * **At 30 fps:** 133ms is ~4 frames (Minimum GOP needed: 5).
> * **At 60 fps:** 133ms is ~8 frames (Minimum GOP needed: 9).
> 
> 

1. **Extract Frame Logs (`1_Verify_and_Log.bat`):** Extracts precise `_frame_log.txt` files for every video. This is your "ground truth" for VFR timestamps.
2. **Generate Proxy Videos (for HD/4K etc):** Import the provided `.json` presets.
* **High Power (720p):** For modern desktops.
* **Low Power (400p):** Optimized for older/budget PCs using the `ultrafast` baseline profile.


3. **Edit in VirtualDub2:** Load your proxy (or the original if you skipped proxy creation), and make your cuts.
* **NOTE: VirtualDub2 is endpoint exclusive — meaning that the frame you end the selection on is NOT included in the selection!
* **Save Your Cutlist:** Once your editing is complete, go to `File > Save processing settings...` (`CTRL + S`).
* **Crucial:** MAKE SURE to check "Include selection and edit list" in the save dialog. Otherwise, your cuts will NOT be saved! VirtualDub2 will remember this setting for future sessions.
* **Naming Convention:** The vdscript must be saved with the format `source_video_filename.extension.vdscript`. So, if your source video is called `whatever.mp4`, your final saved vdscript should be called `whatever.mp4.vdscript`.

### Phase 2: Analysis & Conversion

Run **`2_Analyze_and_Prepare.bat`**. This automated script handles:

* **Adjustment:** Snaps cut points to legal I-frames.
* **VFR Info:** Generates a human-readable `_info.txt` summary.
* **GOP Analysis:** Checks if the starting GOP of each cut is long enough for the FFmpeg "Seek Nudge."
* **VFR Detector:** Scans for severe timing anomalies in the source.
* **Cutlist Generation:** Produces the final timecode list for the Cutter.

### Phase 3: Cut the Video into Individual Segments

Open `exactcut_ffmpeg_cutter.pyw`, load your source folder, and click **Start Cutting**. All the parts will be saved to subfolders (same names as source videos).

### Phase 4: Merge

Open LosslessCut, go to Tools > Merge/concatenate files, browse for desired folder, select all the parts, then merge. Repeat this process until all the parts in each subfolder have been merged - & that's it - FINITO!
* **Cleanup:** Use the **🧹 Cleanup** button inside the ExactCut FFmpeg Cutter to automatically sweep all the temporary scripts, cutlists, and log files into a `delete` folder to keep your workspace tidy.

---

## ✅ User Best Practices

To ensure maximum file stability and compatibility with all media players after cutting:

* **The 5-Second Rule:** Aim for a minimum of 5 seconds between each segment. Cuts placed too close together can occasionally cause playback "hiccups" in certain hardware decoders.
* **Verification:** Always keep your `_frame_log.txt` files until you have verified the final output. They are the only way to pinpoint the exact keyframe positions used by the scripts.

---

## 🔍 Troubleshooting & Safety

### "Smallest starting GOP" is too small?

If `gop_analyzer.py` reports a GOP size smaller than your framerate's requirement, use the **Editor** feature in **ExactCut FFmpeg Cutter GUI** to fix it:

#### Scenario 1: Use "1. Expand Start Earlier"

If there is plenty of room between segments, push the **Start Time** of the offending segment back by **1 second**.

1. Reference your `_frame_log.txt` to find a safe I-frame at least 1 second earlier.
2. Choose the line #, enter "1" in the "Seconds" field and click **Apply Expansion**.

#### Scenario 2: Use "2. Bridge Gap"

If pushing the start time back violates the **5-second rule** or causes an overlap:

1. Select the offending segment and the one preceding it.
2. Click **Apply Bridge**. This merges them into one continuous cut, bypassing the GOP issue entirely.

### Missing Frame Logs or Scripts Skipping Files?

* **Check Names:** Ensure your `.vdscript` includes the original extension (e.g., `.mp4.vdscript`).
* **Missing Logs:** Run `1_Verify_and_Log.bat` again to ensure the `_frame_log.txt` was created.

---

## ⚙️ Requirements

* **Python 3.x**
* **LosslessCut
* **FFmpeg** (Standalone or via LosslessCut)
* **VirtualDub2** (build 44282 or similar)
* **HandBrake** (For proxy generation)

---
