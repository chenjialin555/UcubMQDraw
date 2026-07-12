# Merge all docs/**/*.md into project root 总.md
$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$docsDir = Join-Path $projectRoot 'docs'
$outputFile = Join-Path $projectRoot '总.md'

if (-not (Test-Path $docsDir)) {
    Write-Error "docs folder not found: $docsDir"
    exit 1
}

function Get-SortKey {
    param([System.IO.FileInfo]$File)

    $rel = $File.FullName.Substring($docsDir.Length + 1).Replace('\', '/')

    if ($rel -eq 'README.md') { return '00_README.md' }
    if ($rel -notmatch '/') { return "01_$rel" }
    if ($rel -like 'details/*') { return "02_$rel" }
    if ($rel -like 'examples/*') { return "03_$rel" }
    if ($rel -like 'archive/*') { return "99_$rel" }
    return "01_$rel"
}

$files = Get-ChildItem -Path $docsDir -Filter '*.md' -Recurse -File
$files = $files | Sort-Object { Get-SortKey $_ }

$utf8NoBom = New-Object System.Text.UTF8Encoding $false
$lines = New-Object System.Collections.Generic.List[string]
$now = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

$lines.Add('# UcubMQDraw 文档合集')
$lines.Add('')
$lines.Add('> 由 merge-docs.bat 自动生成，请勿手工编辑。')
$lines.Add("> 生成时间：$now")
$lines.Add("> 共 $($files.Count) 个文件")
$lines.Add('')

foreach ($file in $files) {
    $relativePath = $file.FullName.Substring($docsDir.Length + 1).Replace('\', '/')

    $lines.Add('---')
    $lines.Add('')
    $lines.Add("<!-- 来源: docs/$relativePath -->")
    $lines.Add('')

    $content = [System.IO.File]::ReadAllText($file.FullName, [System.Text.Encoding]::UTF8).TrimEnd()
    if ($content.Length -gt 0) {
        $lines.Add($content)
    }
    $lines.Add('')
}

[System.IO.File]::WriteAllLines($outputFile, $lines, $utf8NoBom)
Write-Host "Merged $($files.Count) files -> $outputFile"
