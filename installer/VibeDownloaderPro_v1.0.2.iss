#define MyAppName "Vibe Downloader Pro"
#define MyAppVersion "1.0.2"
#define MyAppPublisher "InFinite Studios Canada"
#define MyAppExeName "Vibe Downloader Pro.exe"
#define SourceDir "D:\GitHub_App _Creation\VibeDownloader\1_DESKTOP\v1.0.2\dist\Vibe Downloader Pro"
#define OutputDir "D:\GitHub_App _Creation\VibeDownloader\1_DESKTOP\v1.0.2\release"

[Setup]
AppId={{A7B45164-B9D9-4D81-B886-2F5E8AD74C8E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename=VibeDownloaderProSetup-v1.0.2
SetupIconFile=D:\GitHub_App _Creation\VibeDownloader\1_DESKTOP\v1.0.2\VDL_PRO_ICO.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
CloseApplications=yes
RestartApplications=no
UninstallDisplayIcon={app}\{#MyAppExeName}
LicenseFile=D:\GitHub_App _Creation\VibeDownloader\1_DESKTOP\v1.0.2\LICENSE

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

