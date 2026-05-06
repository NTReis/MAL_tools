@echo off
REM MAL Tools launcher (Windows)
REM Starts the proxy + hub. Close window or press Ctrl-C to stop.

cd /d "%~dp0"

where python >nul 2>&1
if %ERRORLEVEL%==0 (
  python mal_proxy.py %*
  goto :eof
)

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py -3 mal_proxy.py %*
  goto :eof
)

echo Python 3 is required but was not found on PATH.
echo Install it from https://www.python.org/downloads/ and re-run.
pause
exit /b 1
