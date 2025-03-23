[Setup]
AppName=Lyrics Scraper
AppVersion=1.0
AppPublisher=LisaHuaband
AppPublisherURL=https://github.com/LisaHusband/Crawling/blob/main/LyricsScraperInstaller.exe 
AppSupportURL=https://github.com/LisaHusband/Crawling
AppUpdatesURL=https://github.com/LisaHusband/Crawling 
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
Source: "README.md"; DestDir: "{app}"; Flags: isreadme
Source: "LICENSE.txt"; DestDir: "{app}"
; Source: "favicon.ico"; DestDir: "{app}"
Source: "alp.jpg"; DestDir: "{app}"
Source: "wc.png"; DestDir: "{app}"
Source: "dependencies\*"; DestDir: "{app}\dependencies"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Lyrics Scraper"; Filename: "{app}\Lyrics_Spiders.exe"
Name: "{commondesktop}\Lyrics Scraper"; Filename: "{app}\Lyrics_Spiders.exe"; Tasks: desktopicon

[Run]
; Filename: "notepad.exe"; Parameters: """{app}\README.md"""; Description: "View ReadMe"; Flags: nowait postinstall skipifsilent
Filename: "{app}\Lyrics_Spiders.exe"; Description: "Launch Lyrics Scraper"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\dependencies"

[Dirs]
Name: "{app}"; Permissions: users-full
