[Setup]
AppName=Hydra Companion
AppVersion=1.0
AppPublisher=Skete RAID
AppPublisherURL=https://github.com/sketeraid
DefaultDirName={pf}\Hydra Companion
DefaultGroupName=Hydra Companion
OutputDir=..\  ; puts installer in HydraCompanion folder
OutputBaseFilename=HydraCompanionSetup
SetupIconFile=hydra_icon.ico
WizardImageFile=installer_side.bmp
WizardSmallImageFile=installer_banner.bmp
LicenseFile=..\LICENSE.txt
UninstallDisplayIcon={app}\HydraCompanion.exe

[Files]
Source: "..\dist\HydraCompanion.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{commondesktop}\Hydra Companion"; Filename: "{app}\HydraCompanion.exe"; WorkingDir: "{app}"; IconFilename: "{app}\HydraCompanion.exe"
Name: "{group}\Hydra Companion"; Filename: "{app}\HydraCompanion.exe"; WorkingDir: "{app}"; IconFilename: "{app}\HydraCompanion.exe"

[Run]
Filename: "cmd.exe"; \
  Parameters: "/C copy ""HydraCompanionSetup.exe"" ""installer\HydraCompanionSetup.exe"""; \
  Flags: runhidden shellexec postinstall skipifsilent

Filename: "cmd.exe"; \
  Parameters: "/C copy ""HydraCompanionSetup.exe"" ""installer\output\HydraCompanionSetup.exe"""; \
  Flags: runhidden shellexec postinstall skipifsilent