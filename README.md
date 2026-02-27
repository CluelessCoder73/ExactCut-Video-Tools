# ExactCut Video Tools

**Achieve truly lossless, frame-accurate video cuts without losing a single frame!**

---

## The Problem with "Lossless" Video Editing

Traditional "lossless" cutting tools (like mkvmerge or FFmpeg stream-copy) are forced to cut at keyframes (I-frames). If you place a cut between keyframes, the tool *must* jump to the next available keyframe to avoid corrupting the video.

This leads to frustrating issues:

* **Lost Frames:** Segments begin *after* your intended start point.
* **Incomplete Endings:** Endpoints shift back in time or stutter.
* **Open GOP Corruption:** Modern codecs (like x265/HEVC) use "Open GOP" structures that cause visual artifacting at cut-in points.

## The ExactCut Solution

**ExactCut Video Tools** bypasses these limitations by intelligently combining **VirtualDub2**, **Python scripting**, **FFmpeg**, and **LosslessCut**.

By analyzing FFmpeg frame logs, our scripts automatically adjust your rough cuts to "legal frame boundaries" (I-frames and P-frames). This guarantees that your output segments retain every single desired frame, providing truly lossless cuts at both the start and end of each segment.

### Key Features

* **Zero Frame Loss:** Guarantees no frames are lost at the beginning or end of your cut segments.
* **Fully VFR Compatible:** Uses high-precision millisecond (ms) offsets, making it fully compatible with Variable Frame Rate (VFR) videos from smartphones and screen recorders.
* **Open GOP Handling:** `vdscript_range_adjuster.py` provides an option to roll back to the 2nd previous I-frame to prevent corruption in codecs like x265. NOTE: The cut-in points will be corrupted, but your chosen parts will not.
* **Proxy Editing Ready:** Define cuts effortlessly on lightweight proxy videos;  *(See `\ExactCut-Video-Tools\presets`)*.
* **All-in-One GUI:** Includes a built-in Cutlist Editor (only for fine-tuning), Frame-to-MS Calculator, and Project Cleanup Tool.

---

## Prerequisites

* **Python:** 3.13.7 or newer.
* **LosslessCut:** 3.64.0 or newer (for merging parts and providing FFmpeg).
* **VirtualDub2:** For creating your initial cutlists.
* **HandBrake:** For proxy video creation (optional but recommended).
* **FFmpeg:** Must be added to your system's PATH. *(See `\ExactCut-Video-Tools\docs\FFMPEG_NOOB_GUIDE.md`)*.

---

## The ExactCut Workflow (Step-by-Step)

### 1. Prepare Your Source Videos

For optimal frame accuracy, ensure your source videos are in **MKV** or **MP4** formats. If they are not, remux them using LosslessCut (Export options > Output container format). Group your videos into folders if necessary.

### 2. Create Proxy Videos (Recommended for higher-resolution videos)

Use HandBrake to create lower-resolution proxies to speed up editing in VirtualDub2. Use one of the custom presets provided with ExactCut Video Tools.

* *Crucial:* DO NOT save proxy videos to the same folder as your input source files!
* *Tip:* All filters are turned off in the presets. If your source video is interlaced, you will need to enable deinterlacing in HandBrake!

### 3. Generate Frame Logs

Copy the ExactCut scripts into your source video folder and run `frame_log_extractor.bat`.

* This automates FFmpeg to extract precise frame type (I, P, B) and index data for every video in the folder.


* *Note: This process may take a while depending on video length.*

### 4. Edit in VirtualDub2

Open your proxy video (or original video) in VirtualDub2.

* Use `HOME` and `END` to mark the start and end points of the selections you want to **delete**.
* Save the cutlist by going to `File > Save processing settings...` (`CTRL + S`).
* **Crucial:** You MUST check "Include selection and edit list" in the save dialog (VirtualDub2 will remember this setting).
* **Naming:** Save the file as `source_video_filename.extension.vdscript` (e.g., `myvideo.mp4.vdscript`).

### 5. Run the Automation Scripts

Run `run_python_scripts.bat`. This will automatically execute:

* **`vdscript_range_adjuster.py`**: Snaps your cuts to legal boundaries and creates `_adjusted.vdscript`.
* **`vdscript_info.py`**: Generates a before-and-after comparison of your cuts (e.g., `myvideo.mp4_info.txt`, `myvideo.mp4_adjusted_info.txt` etc).
* **`gop_analyzer.py`**: Checks for ultra-short GOPs that might cause frame loss. Read the "help" section in the script for more details.
* **`exactcut_vfr_detector.pyw`**: Flags any Variable Frame Rate (VFR) videos. Not important any more, I just left it there for informational purposes.
* **`vdscript_to_timecode_cutlist_generator.py`**: Converts the adjusted scripts into the final `.cutlist.txt` files.

### 6. Cut the Video

Open `exactcut_ffmpeg_cutter.pyw` and select your video folder.

* Adjust your **Start Offset** (The "Seek Nudge" to snap to the keyframe, usually ~133ms).
* Adjust your **End Offset** (The "Safety Buffer", usually 1000ms).
* Click **Start Cutting**. The tool will cleanly slice your videos without re-encoding the video stream.

### 7. Merge and Cleanup

* **Merge:** Open LosslessCut, go to `Tools > Merge/concatenate files`, select all your new video segments, and merge them together.
* **Cleanup:** Use the **🧹 Cleanup** button inside the ExactCut FFmpeg Cutter to automatically sweep all the temporary scripts, cutlists, and log files into a `delete` folder to keep your workspace tidy.

---

## Verifying That Source & Proxy Match

If you use Proxy videos, it is **critical** that the frame count of your proxy perfectly matches your source video. To verify:

1. Open your generated `_frame_log.txt`. Scroll to the last line of actual frame data and look for the `n:` index (e.g., `n:58357`).
2. Open your proxy video in VirtualDub2 and press `[End]` to jump to the last frame.
3. The display at the bottom should say `Frame 58358`.
4. **The Rule:** The VirtualDub2 frame count should always be exactly **+1** compared to the final frame log index (because VirtualDub2 counts the final "empty" frame). If these match, your proxy is perfectly synced!

---

## Advanced Configuration

You can fine-tune how the script adjusts boundaries by editing the parameters at the bottom of `vdscript_range_adjuster.py`:

* `i_frame_offset`: How many I-frames to roll back for start points (Set to `2` for Open GOP codecs like x265).
* `merge_ranges_option`: Enables merging of overlapping or very close ranges.
* `min_gap_between_ranges`: Minimum frame gap required to keep ranges separate.
* `short_cut_mode`: Adjusts endpoint behavior (True for shorter segments, False for full GOPs).

---
