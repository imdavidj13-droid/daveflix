$ErrorActionPreference = 'Stop'
$shortcutPath = Join-Path ([Environment]::GetFolderPath('Startup')) 'DAVEFLIX.lnk'
if (Test-Path $shortcutPath) { Remove-Item -LiteralPath $shortcutPath }
Write-Host 'DAVEFLIX automatic startup is disabled. A currently running server is left running.'
