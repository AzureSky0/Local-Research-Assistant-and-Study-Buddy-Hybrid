; Windows installer for Loci (Inno Setup 6).
; Built by scripts/build_windows.py after PyInstaller, which passes:
;   /DAppVersion=0.3.3  /DSourceDir=<dist\Loci>  /DOutputDir=<dist>
;
; Updating: every Loci installer has the same AppId, so a newer installer
; finds the installed copy by itself and replaces it in the same folder.
; The user's library (%LOCALAPPDATA%\Loci) is never touched by installing,
; updating or uninstalling.

#ifndef AppVersion
  #error AppVersion must be passed with /DAppVersion=x.y.z
#endif
#ifndef SourceDir
  #error SourceDir must be passed with /DSourceDir=<path to dist\Loci>
#endif
#ifndef OutputDir
  #define OutputDir "."
#endif

#define AppName "Loci"
#define AppExe "Loci.exe"
#define Repository "https://github.com/AzureSky0/Local-Research-Assistant-and-Study-Buddy-Hybrid"

[Setup]
; Never change this: it is how a new version recognises an installed one.
AppId={{075E35D4-682E-4A7F-947E-3E38475FE61C}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=AzureSky0
AppPublisherURL={#Repository}
AppSupportURL={#Repository}/issues
AppUpdatesURL={#Repository}/releases
VersionInfoVersion={#AppVersion}

; Installs for the current user only: no administrator prompt.
; {autopf} is then %LOCALAPPDATA%\Programs.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; An update reuses the folder of the installed copy without asking.
UsePreviousAppDir=yes
DisableDirPage=auto

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0

; Loci holds this mutex while it runs (app/core/single_instance.py), so
; setup and the uninstaller ask the user to close it first.
AppMutex=LociRunningMutex
SetupMutex=LociSetupMutex
CloseApplications=yes
RestartApplications=no

UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExe}
OutputDir={#OutputDir}
OutputBaseFilename={#AppName}-{#AppVersion}-windows-setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[InstallDelete]
; Remove the previous version's program files before copying the new ones,
; so no outdated library is left behind. Only program files live here.
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}\licenses"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[Code]
const
  UninstallKey = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{075E35D4-682E-4A7F-947E-3E38475FE61C}_is1';

{ Warn before replacing a newer installed version with an older one. }
function InitializeSetup(): Boolean;
var
  Installed: String;
  InstalledPacked, NewPacked: Int64;
begin
  Result := True;
  if RegQueryStringValue(HKEY_CURRENT_USER, UninstallKey, 'DisplayVersion', Installed)
    and StrToVersion(Installed, InstalledPacked)
    and StrToVersion('{#AppVersion}', NewPacked)
    and (ComparePackedVersion(InstalledPacked, NewPacked) > 0) then
  begin
    Result := SuppressibleMsgBox(
      'A newer version of {#AppName} (' + Installed + ') is already installed.' + #13#10 + #13#10 +
      'Install the older version {#AppVersion} instead? Your library is kept either way, ' +
      'but an older version may not be able to open a library that a newer version has updated.',
      mbConfirmation, MB_YESNO or MB_DEFBUTTON2, IDNO) = IDYES;
  end;
end;
