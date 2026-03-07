@echo off
setlocal enabledelayedexpansion
title Stage 1: Verify and Log (ExactCut)

rem --- SMART FFMPEG DETECTION ---
where ffmpeg >nul 2>nul
if %errorlevel% equ 0 (
    set "ffmpeg_path=ffmpeg"
) else if exist "%~dp0ffmpeg.exe" (
    set "ffmpeg_path=%~dp0ffmpeg.exe"
) else (
    set "ffmpeg_path=C:\PortableApps\LosslessCut-win-x64\resources\ffmpeg.exe"
)

echo ======================================================
echo STEP 1: EXTRACTING FRAME LOGS (Filtered)
echo Using: !ffmpeg_path!
echo ======================================================

for %%F in ("%~dp0*.mp4" "%~dp0*.avi" "%~dp0*.mkv" "%~dp0*.mov" "%~dp0*.m4v" "%~dp0*.m2ts" "%~dp0*.mts" "%~dp0*.ts" "%~dp0*.wmv" "%~dp0*.asf" "%~dp0*.flv" "%~dp0*.webm" "%~dp0*.3gp" "%~dp0*.ogv" "%~dp0*.vob" "%~dp0*.mpg" "%~dp0*.mpeg" "%~dp0*.m2v") do (
    set "target_log=%%~nxF_frame_log.txt"
    if not exist "!target_log!" (
        echo [>] Extracting filtered log for: %%~nxF
        "!ffmpeg_path!" -i "%%F" -vf showinfo -f null - 2>&1 | findstr /i "n:" > "!target_log!"
    ) else (
        echo [!] Skipping %%~nxF (Log already exists)
    )
)

echo.
echo ======================================================
echo STEP 2: LAUNCHING VFR HEALTH CHECK
echo ======================================================
if exist "%~dp0exactcut_vfr_detector.pyw" (
    start "" "pythonw.exe" "%~dp0exactcut_vfr_detector.pyw"
) else (
    echo [ERROR] exactcut_vfr_detector.pyw not found!
)

echo.
echo DONE: Logs extracted using original filtered format. 
echo CHECK the VFR Detector window now for health status.
pause