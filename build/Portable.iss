; Portable installer script for Palworld Save Tools (Windows)
; Uses Inno Setup preprocessor defines passed from CI:
;   /DAppVersion=2.0.3
;   /DAppExeName=PalworldSaveTools-V2.0.3-win.exe
;   /DAppDirName=PalworldSaveTools-V2.0.3-win.exe.dist
;
; Compile:
;   iscc /DAppVersion=2.0.3 /DAppExeName=... /DAppDirName=... build\Portable.iss

#define AppName "PalworldSaveTools"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
DisableDirPage=yes
DisableWelcomePage=yes
DisableFinishedPage=yes
OutputDir=..\dist
OutputBaseFilename={#AppName}-V{#AppVersion}-win
Compression=lzma2/max
SolidCompression=yes
PrivilegesRequired=lowest
SetupIconFile=..\resources\assets\icons\app\icon.ico
UninstallDisplayIcon=..\resources\assets\icons\app\icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\{#AppDirName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\license"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
