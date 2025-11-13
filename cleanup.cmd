@echo off
REM Cleanup Script - Remove Unused Files
REM Run this to clean up the project

echo ========================================
echo Cleaning up unused files...
echo ========================================
echo.

REM Remove history folder
if exist .history (
    echo Removing .history folder...
    rmdir /s /q .history
    echo [OK] Removed .history
) else (
    echo [SKIP] .history not found
)

REM Remove empty folders
if exist docs (
    echo Removing empty docs folder...
    rmdir /s /q docs
    echo [OK] Removed docs
)

if exist examples (
    echo Removing empty examples folder...
    rmdir /s /q examples
    echo [OK] Removed examples
)

REM Remove Python cache folders
echo Removing Python cache folders...
if exist __pycache__ rmdir /s /q __pycache__
if exist endpoints\__pycache__ rmdir /s /q endpoints\__pycache__
if exist middleware\__pycache__ rmdir /s /q middleware\__pycache__
if exist models\__pycache__ rmdir /s /q models\__pycache__
if exist services\__pycache__ rmdir /s /q services\__pycache__
if exist templates\__pycache__ rmdir /s /q templates\__pycache__
if exist utils\__pycache__ rmdir /s /q utils\__pycache__
echo [OK] Removed Python cache

REM Remove unused service files
if exist services\parallel_generate_endpoint.py (
    echo Removing unused parallel_generate_endpoint.py...
    del services\parallel_generate_endpoint.py
    echo [OK] Removed parallel_generate_endpoint.py
)

if exist services\storage_client.py (
    echo Removing unused storage_client.py...
    del services\storage_client.py
    echo [OK] Removed storage_client.py
)

REM Remove old test report
if exist BACKEND_TEST_REPORT.md (
    echo Removing old BACKEND_TEST_REPORT.md...
    del BACKEND_TEST_REPORT.md
    echo [OK] Removed BACKEND_TEST_REPORT.md
)

REM Remove frontend demo if exists
if exist frontend-demo.html (
    echo Removing frontend-demo.html...
    del frontend-demo.html
    echo [OK] Removed frontend-demo.html
)

REM Ask about local test projects
echo.
echo ========================================
echo Local Test Projects Found:
echo ========================================
if exist projects\biharweatheryazk echo - projects\biharweatheryazk
if exist projects\fittrackerqwz4 echo - projects\fittrackerqwz4
if exist projects\fittrackrvxz echo - projects\fittrackrvxz
echo.
set /p REMOVE_PROJECTS="Remove local test projects? (y/n): "

if /i "%REMOVE_PROJECTS%"=="y" (
    if exist projects\biharweatheryazk rmdir /s /q projects\biharweatheryazk
    if exist projects\fittrackerqwz4 rmdir /s /q projects\fittrackerqwz4
    if exist projects\fittrackrvxz rmdir /s /q projects\fittrackrvxz
    echo [OK] Removed local test projects
) else (
    echo [SKIP] Kept local test projects
)

echo.
echo ========================================
echo Cleanup Complete!
echo ========================================
echo.
echo Summary:
echo - Removed .history folder
echo - Removed empty folders (docs, examples)
echo - Removed Python cache
echo - Removed unused service files
echo - Removed old documentation
echo.
echo Your project is now cleaner!
echo.
pause
