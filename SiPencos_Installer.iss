[Setup]
AppName=SiPencos
AppVersion=1.0
DefaultDirName={autopf}\SiPencos
DefaultGroupName=SiPencos
UninstallDisplayIcon={app}\SiPencos.exe
Compression=lzma2
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=SiPencos_Setup

[Files]
Source: "dist\SiPencos\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SiPencos"; Filename: "{app}\SiPencos.exe"
Name: "{autodesktop}\SiPencos"; Filename: "{app}\SiPencos.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
