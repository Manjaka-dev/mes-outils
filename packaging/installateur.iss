; Installateur de « Mes outils » (Inno Setup 6).
;   iscc /DVersion=1.3.0 packaging\installateur.iss
; Emballe dist\Mes outils\ (construit par PyInstaller) dans
; dist\Mes-outils-Setup.exe. Installation pour l'utilisateur seul, sans droits
; administrateur ; les données restent dans %APPDATA%\Mes outils (jamais
; effacées, même à la désinstallation).

#ifndef Version
  #define Version "0.0.0"
#endif

[Setup]
AppId={{6E1F2B7A-4C3D-4E8B-9A51-2F7C0D9B3E64}
AppName=Mes outils
AppVersion={#Version}
AppVerName=Mes outils {#Version}
AppPublisher=Mes outils
AppPublisherURL=https://github.com/rarianaAina/mes-outils
AppSupportURL=https://github.com/rarianaAina/mes-outils/issues
AppUpdatesURL=https://github.com/rarianaAina/mes-outils/releases
VersionInfoVersion={#Version}
DefaultDirName={localappdata}\Programs\Mes outils
DisableProgramGroupPage=yes
DisableDirPage=auto
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=Mes-outils-Setup
SetupIconFile=..\outil\mes_outils.ico
UninstallDisplayIcon={app}\Mes outils.exe
UninstallDisplayName=Mes outils
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; La bulle tient ce verrou tant qu'elle tourne : l'installateur demande de
; la fermer avant de remplacer le programme.
AppMutex=MesOutils.Bulle
CloseApplications=yes
ShowLanguageDialog=auto
LicenseFile=..\LICENSE

[Languages]
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
fr.Demarrage=Lancer Mes outils au démarrage de Windows
en.Demarrage=Start Mes outils when Windows starts
fr.Options=Options :
en.Options=Options:

[Tasks]
Name: "bureau"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:Options}"
Name: "demarrage"; Description: "{cm:Demarrage}"; GroupDescription: "{cm:Options}"

[InstallDelete]
; Mise à jour : les fichiers de l'ancienne version disparaissent d'abord.
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "..\dist\Mes outils\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\Mes outils"; Filename: "{app}\Mes outils.exe"
Name: "{userdesktop}\Mes outils"; Filename: "{app}\Mes outils.exe"; Tasks: bureau
Name: "{userstartup}\Mes outils"; Filename: "{app}\Mes outils.exe"; Tasks: demarrage

[UninstallDelete]
; Raccourcis éventuellement créés plus tard depuis l'onglet Réglages.
Type: files; Name: "{userdesktop}\Mes outils.lnk"
Type: files; Name: "{userstartup}\Mes outils.lnk"

[Run]
Filename: "{app}\Mes outils.exe"; Description: "{cm:LaunchProgram,Mes outils}"; Flags: nowait postinstall skipifsilent
