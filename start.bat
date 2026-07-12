@echo off
setlocal EnableExtensions

cd /d "%~dp0"

REM ---------- ?? uv ?? ----------
where uv >nul 2>&1
if errorlevel 1 (
    if exist "%USERPROFILE%\.local\bin\uv.exe" (
        set "PATH=%USERPROFILE%\.local\bin;%PATH%"
    ) else (
        echo [INFO] ???? uv?????...
        powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
        set "PATH=%USERPROFILE%\.local\bin;%PATH%"
    )
)

where uv >nul 2>&1
if errorlevel 1 (
    echo [ERROR] uv ??????????: https://docs.astral.sh/uv/
    exit /b 1
)

REM ---------- ??????? ----------
if not exist ".venv" (
    echo [INFO] ??????...
    uv venv
    if errorlevel 1 exit /b 1
)

echo [INFO] ????...
uv sync
if errorlevel 1 exit /b 1

REM ---------- ?????? ----------
if not defined GRADIO_SERVER_PORT set "GRADIO_SERVER_PORT=7860"
set "PORT=%GRADIO_SERVER_PORT%"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$port = %PORT%;" ^
    "$conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue;" ^
    "if ($conns) {" ^
    "  Write-Host ('[WARN] ?? {0} ????????????...' -f $port);" ^
    "  $conns | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object {" ^
    "    Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue" ^
    "  };" ^
    "  Start-Sleep -Seconds 1" ^
    "}"

REM ---------- ?? ----------
if not defined UCUB_MQDRAW_USE_MOCK set "UCUB_MQDRAW_USE_MOCK=true"

echo [INFO] ?? UcubMQDraw -^> http://127.0.0.1:%PORT%
echo [INFO] Mock ??: UCUB_MQDRAW_USE_MOCK=%UCUB_MQDRAW_USE_MOCK%

uv run python app.py
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo.
    echo [ERROR] ??????????: %EXIT_CODE%
    pause
)
exit /b %EXIT_CODE%
