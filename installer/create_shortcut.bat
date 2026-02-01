@echo off
powershell -ExecutionPolicy Bypass -Command ^
"$s = (New-Object -ComObject WScript.Shell).CreateShortcut('%CommonPrograms%\Hydra Companion.lnk'); ^
$s.TargetPath = '%ProgramFiles%\Hydra Companion\HydraCompanion.exe'; ^
$s.WorkingDirectory = '%ProgramFiles%\Hydra Companion'; ^
$s.Save()"