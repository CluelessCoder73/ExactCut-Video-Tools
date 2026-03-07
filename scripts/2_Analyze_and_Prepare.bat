@echo off
setlocal enabledelayedexpansion
title Stage 2: Analyze and Prepare (ExactCut)

echo ======================================================
echo STEP 1: ADJUSTING VDSCRIPT RANGES (I-Frame Alignment)
echo ======================================================
python "%~dp0vdscript_range_adjuster.py"

echo.
echo ======================================================
echo STEP 2: ANALYZING GOP SIZES (GOP 5 RULE Check)
echo ======================================================
python "%~dp0gop_analyzer.py"

echo.
echo ======================================================
echo STEP 3: GENERATING HUMAN-READABLE INFO FILES
echo ======================================================
python "%~dp0vdscript_vfr_info.py"

echo.
echo ======================================================
echo STEP 4: GENERATING FINAL TIME-BASED CUTLISTS
echo ======================================================
python "%~dp0vdscript_to_timecode_cutlist_generator.py"

echo.
echo ------------------------------------------------------
echo ANALYSIS COMPLETE - CHECK RESULTS:
echo ------------------------------------------------------
echo 1. Open 'gop_info.txt' - Ensure Smallest GOP is 5+
echo 2. Check your '_info.txt' files for segment details.
echo 3. Your final cutlists are ready for the FFmpeg Cutter!
echo ------------------------------------------------------
echo.
pause