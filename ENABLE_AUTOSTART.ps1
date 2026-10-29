$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
if (!(Test-Path (Join-Path $projectRoot 'pairing.key')) -or !(Test-Path (Join-Path $projectRoot 'connection.json'))) {
    throw 'Configure DAVEFLIX using CONFIGURE_WEBSITE.bat before enabling automatic startup.'
}
# Resolve the real interpreter now, so startup does not depend on PATH or Conda.
$launcher = Get-Command py -ErrorAction SilentlyContinue
if ($launcher) {
    $pythonPath = & $launcher.Source -3 -c 'import sys; print(sys.executable)'
} else {
    $pythonCommand = Get-Command python -ErrorAction Stop
    $pythonPath = & $pythonCommand.Source -c 'import sys; print(sys.executable)'
}
if ($LASTEXITCODE -ne 0 -or !$pythonPath) { throw 'A working Python installation was not found.' }
$pythonPath = ([string]$pythonPath).Trim()
$pythonWindowless = Join-Path (Split-Path $pythonPath) 'pythonw.exe'
if (!(Test-Path $pythonWindowless)) { throw 'pythonw.exe was not found beside Python. Repair your Python installation first.' }
$startupDirectory = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupDirectory 'DAVEFLIX.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pythonWindowless
$shortcut.Arguments = '"' + (Join-Path $projectRoot 'server.py') + '" --background'
$shortcut.WorkingDirectory = $projectRoot
$shortcut.Description = 'Start the DAVEFLIX PC media server when signing into Windows'
$shortcut.Save()
Write-Host 'DAVEFLIX will start silently when you next sign into Windows.'
Write-Host 'Your current server can stay running until then. Tailscale must also start with Windows.'
Write-Host 'Startup errors are recorded in server.log in the DAVEFLIX folder.'
