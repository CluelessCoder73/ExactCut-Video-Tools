rem This Windows batch file was tested and works with:
rem - FFmpeg (the version in LosslessCut 3.63.0)
@echo off
set input_video="C:\New folder\test.mp4"
set output_log="C:\New folder\frame_log.txt"

echo Processing video: %input_video%

rem Run FFmpeg command to extract frame information
"C:\PortableApps\LosslessCut-win-x64\resources\ffmpeg.exe" -i %input_video% -export_side_data +venc_params -vf showinfo -f null - > %output_log% 2>&1

rem Check if FFmpeg command completed successfully
if %ERRORLEVEL%==0 (
    echo Operation completed successfully.
) else (
    echo Operation failed.
)

pause
