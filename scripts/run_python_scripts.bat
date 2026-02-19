@echo off
REM Batch file to automate Python scripts for ExactCut Video Tools.
REM This file should be placed in the same folder as the Python scripts and input files.

setlocal
:: Get the current folder path for the VFR detector
set "CURRENT_DIR=%~dp0"

echo [1/5] Running: vdscript_range_adjuster.py...
python vdscript_range_adjuster.py

echo.
echo [2/5] Running: vdscript_vfr_info.py...
python vdscript_vfr_info.py

echo.
echo [3/5] Running: gop_analyzer.py...
python gop_analyzer.py

echo.
echo [4/5] Running: exactcut_vfr_detector.pyw (Batch Mode)...
:: Running in batch mode requires the --batch-mode flag and the folder path
python exactcut_vfr_detector.pyw --batch-mode --path "%CURRENT_DIR%."

echo.
echo [5/5] Running: vdscript_to_timecode_cutlist_generator.py...
python vdscript_to_timecode_cutlist_generator.py

echo.
echo ---------------------------------------------------
echo ALL SCRIPTS FINISHED.
pause