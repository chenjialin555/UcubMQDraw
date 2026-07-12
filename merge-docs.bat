@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

echo 正在合并 docs 目录下的 Markdown 文档...

rem 确保 ps1 为 UTF-8 BOM，避免 PowerShell 5 中文乱码
powershell -NoProfile -Command "& {$p='%~dp0merge-docs.ps1';$c=[IO.File]::ReadAllText($p,[Text.Encoding]::UTF8);[IO.File]::WriteAllText($p,$c,(New-Object Text.UTF8Encoding $true))}"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0merge-docs.ps1"

if errorlevel 1 (
    echo 合并失败。
    exit /b 1
)

echo 已生成: %~dp0总.md
exit /b 0
