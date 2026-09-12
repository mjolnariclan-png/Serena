@echo off
echo Setting up Serena with hotkeys...
echo.
echo Creating shortcut with hotkeys...
echo.

cd /d "%~dp0"

powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Serena.lnk'); $Shortcut.TargetPath = '%CD%\start_serena.bat'; $Shortcut.WorkingDirectory = '%CD%'; $Shortcut.Save()"

echo.
echo Shortcut created on Desktop: Serena.lnk
echo.
echo To set up hotkeys:
echo 1. Right-click the Serena.lnk shortcut on your desktop
echo 2. Select Properties
echo 3. Click in the "Shortcut key" field
echo 4. Press your desired hotkey combination (e.g., Ctrl+Alt+S)
echo 5. Click Apply and OK
echo.
echo Now pressing that hotkey will launch Serena!
echo.
pause