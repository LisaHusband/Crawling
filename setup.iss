[Setup]
AppName=Lyrics Scraper
AppVersion=1.0
; AppPublisher=Mr.Chen
; AppPublisherURL=https://yourwebsite.com 
; AppSupportURL=https://yourwebsite.com/support 
; AppUpdatesURL=https://yourwebsite.com/download 
DefaultDirName={pf}\LyricsScraper
DefaultGroupName=Lyrics Scraper
UninstallDisplayIcon={app}\Lyrics_Spiders.exe
Compression=lzma
SolidCompression=yes
OutputDir=.
OutputBaseFilename=LyricsScraperInstaller
SetupIconFile="favicon.ico"
LicenseFile="LICENSE.txt"
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"
Name: "allusers"; Description: "Install for all users"; GroupDescription: "Installation Type"

[Files]
Source: "dist\Lyrics_Spiders.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.txt"; DestDir: "{app}"; Flags: isreadme
Source: "LICENSE.txt"; DestDir: "{app}"
Source: "favicon.ico"; DestDir: "{app}"
Source: "dependencies\*"; DestDir: "{app}\dependencies"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Lyrics Scraper"; Filename: "{app}\Lyrics_Spiders.exe"
Name: "{commondesktop}\Lyrics Scraper"; Filename: "{app}\Lyrics_Spiders.exe"; Tasks: desktopicon

[Run]
Filename: "notepad.exe"; Parameters: """{app}\README.txt"""; Description: "View ReadMe"; Flags: nowait postinstall skipifsilent
Filename: "{app}\Lyrics_Spiders.exe"; Description: "Launch Lyrics Scraper"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\dependencies"
