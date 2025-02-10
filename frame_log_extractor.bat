@echo off
cd /d %~dp0
setlocal enabledelayedexpansion

rem Set the folder containing the videos
set "video_folder=%~dp0"

rem Set the path to FFmpeg
set "ffmpeg_path=C:\PortableApps\LosslessCut-win-x64\resources\ffmpeg.exe"

echo Processing videos in: %video_folder%

rem Loop through all video files in the folder
for %%F in ("%video_folder%\*.mp4" "%video_folder%\*.avi" "%video_folder%\*.mkv" "%video_folder%\*.mov" "%video_folder%\*.m4v" "%video_folder%\*.m2ts" "%video_folder%\*.mts" "%video_folder%\*.ts" "%video_folder%\*.wmv" "%video_folder%\*.asf" "%video_folder%\*.flv" "%video_folder%\*.webm" "%video_folder%\*.3gp" "%video_folder%\*.ogv" "%video_folder%\*.vob" "%video_folder%\*.mpg" "%video_folder%\*.mpeg" "%video_folder%\*.m2v") do (
    set "input_video=%%F"
    set "output_log=%video_folder%\%%~nxF_frame_log.txt"
    
    set "process_video=1"
    if exist "!output_log!" (
        choice /c yn /n /m "!output_log! already exists. Overwrite? [Y/N]"
        if errorlevel 2 (
            echo Skipping %%~nxF
            echo.
            set "process_video=0"
        )
    )
    
    if "!process_video!"=="1" (
        echo Processing video: !input_video!

        rem Run FFmpeg command to extract frame information        
        "!ffmpeg_path!" -i "!input_video!" -export_side_data +venc_params -vf showinfo -f null - > "!output_log!" 2>&1

        rem Check if FFmpeg command completed successfully        
        if !ERRORLEVEL!==0 (
            echo Operation completed successfully for: %%~nxF
        ) else (
            echo Operation failed for: %%~nxF
        )
    )
    
    echo.
)

echo All videos processed.
pause
