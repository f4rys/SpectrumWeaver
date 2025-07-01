@echo off
echo Building SpectrumWeaver with PyInstaller...
echo.

REM Clean previous build (from project root)
if exist "..\build" rmdir /s /q "..\build"
if exist "..\dist" rmdir /s /q "..\dist"
if exist "..\output\spectrum_weaver.exe" del "..\output\spectrum_weaver.exe"

REM Build with PyInstaller using the spec file and uv environment
echo Running PyInstaller in uv environment...
cd ..
uv run pyinstaller tools\spectrum_weaver.spec
cd tools

REM Check if build was successful
if exist "..\dist\spectrum_weaver.exe" (
    echo.
    echo Build successful!
    
    REM Create output directory if it doesn't exist
    if not exist "..\output" mkdir "..\output"
    
    REM Copy the executable to output directory
    copy "..\dist\spectrum_weaver.exe" "..\output\spectrum_weaver.exe"
    echo Executable copied to output\spectrum_weaver.exe
    
    echo.
    echo Build complete! You can find the executable at:
    cd ..
    echo %cd%\output\spectrum_weaver.exe
    echo.
    echo File size:
    dir "output\spectrum_weaver.exe" | find "spectrum_weaver.exe"
    cd tools
) else (
    echo.
    echo Build failed! Check the output above for errors.
    echo.
    echo Common solutions:
    echo 1. Make sure all dependencies are installed: uv sync
    echo 2. Try running the debug build first: build_debug.bat
    echo 3. Check that you're using the correct Python environment
)

echo.
pause
