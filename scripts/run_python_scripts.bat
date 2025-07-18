@echo off
REM Batch file to automate Python scripts for ExactCut Video Tools.
REM This file should be placed in the same folder as the Python scripts and input files.

REM --- 1. Get Frame Rate from User ---
set /p "frame_rate=Enter the frame rate (e.g., 23.976, 25, 29.97, 60) for your video(s): "
echo.

REM --- 2. Run vdscript_range_adjuster.py ---
echo Running vdscript_range_adjuster.py...
python vdscript_range_adjuster.py
echo.

REM --- 3. Run vdscript_info.py ---
echo Running vdscript_info.py...
REM Pass the stored frame rate directly to vdscript_info.py using echo
echo %frame_rate%| python vdscript_info.py
echo.

REM --- 4. Run gop_analyzer.py ---
echo Running gop_analyzer.py...
python gop_analyzer.py
echo.

REM --- 5. Run exactcut_vfr_detector.pyw (now in batch mode) ---
echo Running exactcut_vfr_detector.pyw in batch mode...
REM The --path argument tells the script where to find the _frame_log.txt files.
REM %CD% expands to the current directory where the batch file is run.
python exactcut_vfr_detector.pyw --batch-mode --path "%CD%"
echo.

REM --- 6. Run vdscript_to_timecode_cutlist_generator.py ---
echo Running vdscript_to_timecode_cutlist_generator.py...
REM Pass the stored frame rate directly to vdscript_to_timecode_cutlist_generator.py using echo
echo %frame_rate%| python vdscript_to_timecode_cutlist_generator.py
echo.

echo All Python scripts have been executed.
pause
