# FFmpeg for Beginners: A Quick Start Guide

Welcome to the powerful world of FFmpeg! While it might seem intimidating at first, FFmpeg is an essential tool for almost any video-related task, from converting formats to extracting information. This guide will help you get started with the basics you need for the ExactCut Video Tools workflow.

---

## What is FFmpeg?

At its core, FFmpeg is a free, open-source command-line program that can handle almost all multimedia formats. It can convert between formats, extract audio, create video, fix corrupted files, and much more. For our purposes, we'll focus on its ability to inspect video files, change their container format losslessly, and combine/process video and audio streams.

---

## 1. Getting FFmpeg

First, you need the FFmpeg executable files.

1.  **Download FFmpeg:**
    * Go to the official FFmpeg website: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
    * Under the "Get packages & executable files" section, click on the Windows icon.
    * You'll typically want a "release build" version. Links are usually provided by third-party builders (e.g., Gyan or BtbN). Choose a `.zip` file (e.g., `ffmpeg-release-full.zip`).
2.  **Extract FFmpeg:**
    * Unzip the downloaded file. You'll find a folder inside (e.g., `ffmpeg-N.x.x-essentials_build`).
    * Inside that, navigate to the `bin` folder. This `bin` folder contains `ffmpeg.exe`, `ffprobe.exe`, and `ffplay.exe`.
3.  **Place FFmpeg:**
    * It's best to put this `bin` folder in a permanent, easy-to-remember location, like `C:\ffmpeg\bin`. This makes it easier to manage future updates and add it to your system's PATH (next step).

---

## 2. Adding FFmpeg to Your System's PATH (Making it Easy to Use)

"PATH" is a system variable that tells your computer where to look for executable programs. By adding FFmpeg's `bin` folder to your PATH, you can run `ffmpeg` commands directly from any folder in your Command Prompt, without having to type its full path every time.

There are two main ways to do this on Windows:

### 2.1. For Your User Account (Standard Windows Account)

This method only makes FFmpeg accessible when you are logged into *your specific Windows user account*. No administrator privileges are required.

1.  **Search for "Environment Variables":**
    * Press the `Windows Key + S` to open the search bar.
    * Type `environment variables` and select "Edit environment variables for your account" (or "Edit the system environment variables" and then click "Environment Variables..." if that's the only option).
2.  **Edit User Variables:**
    * In the "Environment Variables" window, look at the top section labeled "User variables for [Your Username]".
    * Find a variable named `Path` (if it exists).
        * **If `Path` exists:** Select it and click "Edit...".
        * **If `Path` does NOT exist:** Click "New...", type `Path` as the "Variable name", and then proceed.
3.  **Add FFmpeg Path:**
    * In the "Edit environment variable" window:
        * Click "New" and paste the full path to your FFmpeg `bin` folder (e.g., `C:\ffmpeg\bin`).
        * Click "OK" on all open windows to save the changes.

### 2.2. For All Users (Administrator Windows Account)

This method makes FFmpeg accessible to *all* users on your computer. This requires administrator privileges.

1.  **Search for "Environment Variables":**
    * Press the `Windows Key + S` to open the search bar.
    * Type `environment variables` and select "Edit the system environment variables". You might be prompted for administrator permission.
2.  **Edit System Variables:**
    * In the "System Properties" window, click the "Environment Variables..." button at the bottom.
    * In the "Environment Variables" window, look at the bottom section labeled "System variables".
    * Find the `Path` variable, select it, and click "Edit...".
3.  **Add FFmpeg Path:**
    * In the "Edit environment variable" window:
        * Click "New" and paste the full path to your FFmpeg `bin` folder (e.g., `C:\ffmpeg\bin`).
        * Click "OK" on all open windows to save the changes.

### 2.3. Verify the Installation

After adding FFmpeg to your PATH, open a **NEW** Command Prompt window (existing ones won't see the changes).

* Type `ffmpeg -version` and press Enter.
* If you see a lot of text detailing FFmpeg's version and build configuration, it means it's installed correctly and accessible from your PATH!
* If you get an error like "ffmpeg is not recognized...", double-check your steps.

---

## 3. Opening the Command Prompt in a Specific Folder

This is a super handy trick to quickly open a Command Prompt window that's already in the folder where your video files are located.

1.  **Navigate to your folder:** Open File Explorer and browse to the folder containing the video files you want to work with.
2.  **Click in the Address Bar:** Click once in the address bar at the top of the File Explorer window (where it shows the folder path, e.g., `This PC > Videos > My Project`). The path should become highlighted.
3.  **Type "cmd" and Enter:** Type `cmd` into the address bar and press `Enter`.

A Command Prompt window will open, and its current directory will automatically be set to the folder you were in in File Explorer. This saves you from having to use `cd` commands.

---

## 4. Basic FFmpeg Command: Changing Container (Remuxing Losslessly)

One of the most common tasks with FFmpeg is changing a video's container format without re-encoding the video or audio streams. This is called **remuxing** and it's super fast and lossless (it doesn't degrade quality). This is useful if, for example, your video is in an MKV file but your editing software or player prefers MP4.

### The Command Structure:

```bash
ffmpeg -i "input_video.mkv" -c copy "output_video.mp4"
```

### Explanation:

* `ffmpeg`: The command to run FFmpeg.
* `-i "input_video.mkv"`:
    * `-i` stands for "input".
    * `"input_video.mkv"`: This is the **full path and filename of your original video file**.
        * **What to change:** Replace `"input_video.mkv"` with the actual name/path of the file you want to remux. Remember to use double quotes if the path or filename contains spaces.
* `-c copy`:
    * `-c` stands for "codec".
    * `copy` tells FFmpeg to **copy the existing video and audio streams exactly as they are** from the input file to the output file **without re-encoding them**. This is what makes the process fast and lossless.
* `"output_video.mp4"`:
    * This is the **full path and desired filename for your new MP4 file**.
        * **What to change:** Replace `"output_video.mp4"` with the name/path you want for your new file. You can change the extension (`.mp4`, `.mkv`, `.mov`, etc.) to choose the desired container.

### Example:

Let's say you have a file named `My_Travel_Video.mkv` in your `C:\Users\YourName\Videos` folder, and you want to convert it to an MP4 file named `My_Travel_Video.mp4` in the same folder.

1.  Open Command Prompt in `C:\Users\YourName\Videos` (using the trick from Section 3).
2.  Type the following command:
    ```bash
    ffmpeg -i "My_Travel_Video.mkv" -c copy "My_Travel_Video.mp4"
    ```
3.  Press Enter. FFmpeg will quickly create the new MP4 file.

---

## 5. More Common FFmpeg Tasks

FFmpeg can do much more than just change containers. Here are a couple of very useful scenarios:

### 5.1. Muxing Separate Video and Audio Files Together

Sometimes you might have a video stream in one file (e.g., `video_only.mp4`) and its corresponding audio stream in a separate file (e.g., `audio_track.wav` or `audio_track.mp3`). You can use FFmpeg to combine these into a single video file.

#### The Command Structure:

```bash
ffmpeg -i "video_only.mp4" -i "audio_track.mp3" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 "combined_video.mp4"
```

#### Explanation:

* `-i "video_only.mp4"`: The **first input file**, which is your video-only file. FFmpeg assigns input files an index starting from `0`. So, this video file is input `0`.
* `-i "audio_track.mp3"`: The **second input file**, your audio file. This is input `1`.
* `-c:v copy`:
    * `-c:v` specifies the codec for the **video stream**.
    * `copy` tells FFmpeg to **copy the video stream** from the input without re-encoding.
* `-c:a aac`:
    * `-c:a` specifies the codec for the **audio stream**.
    * `aac` tells FFmpeg to **encode the audio to AAC**. This is often necessary because not all audio formats (like MP3) are directly compatible with all video containers (like MP4). If your audio is already AAC, you could try `-c:a copy` for a lossless copy.
* `-map 0:v:0`: This is a crucial "mapping" option:
    * `-map`: Tells FFmpeg which streams from which inputs to include in the output.
    * `0`: Refers to the **first input file** (our `video_only.mp4`).
    * `v`: Specifies that we want a **video stream**.
    * `0`: Specifies the **first video stream** found in input `0`.
* `-map 1:a:0`: Another mapping option:
    * `1`: Refers to the **second input file** (our `audio_track.mp3`).
    * `a`: Specifies that we want an **audio stream**.
    * `0`: Specifies the **first audio stream** found in input `1`.
* `"combined_video.mp4"`: The **output file** name and path.

#### What to change:

* Replace `"video_only.mp4"` with the actual path and name of your video input.
* Replace `"audio_track.mp3"` with the actual path and name of your audio input.
* Replace `"combined_video.mp4"` with your desired output filename and path.
* **Optional:** If you know your audio codec is already compatible with the output container (e.g., AAC audio into an MP4 container), you can change `-c:a aac` to `-c:a copy` for faster processing.

### 5.2. Stream Copying Video, Transcoding Audio (with Specific Settings)

This is a common scenario where you want to keep the video quality exactly the same (stream copy) but reduce the audio file size or change its codec by re-encoding (transcoding) it with specific parameters.

#### The Command Structure:

```bash
ffmpeg -i "input_video.mp4" -c:v copy -c:a aac -b:a 128k "output_video_with_new_audio.mp4"
```

#### Explanation:

* `ffmpeg -i "input_video.mp4"`: Specifies your input video file.
* `-c:v copy`: This tells FFmpeg to **copy the video stream** directly, without any re-encoding. This means no quality loss for the video and faster processing.
* `-c:a aac`: This tells FFmpeg to **re-encode the audio stream using the AAC codec**. AAC is a widely supported and efficient audio codec, commonly used in MP4 files.
* `-b:a 128k`:
    * `-b:a` specifies the **bitrate for the audio stream**.
    * `128k` sets the audio bitrate to **128 kilobits per second**. This is a common bitrate for good quality stereo audio that keeps file sizes manageable. Higher bitrates (e.g., `192k`, `256k`) mean better quality but larger files. Lower bitrates (e.g., `64k`) mean smaller files but potentially noticeable quality degradation.
* `"output_video_with_new_audio.mp4"`: The **output file** name and path.

#### What to change:

* Replace `"input_video.mp4"` with the actual path and name of your input file.
* Replace `"output_video_with_new_audio.mp4"` with your desired output filename and path.
* **Optional:** Adjust `128k` to your desired audio bitrate. Experiment to find a balance between quality and file size that suits your needs.
