; Instalador de Dicta (Inno Setup 6).
;
; Instalación POR USUARIO en %LOCALAPPDATA%\Programs\Dicta: la app escribe
; dicta_config.json, dicta.log y audios/ junto al .exe, así que necesita una
; carpeta escribible sin administrador.
;
; Compilar:  ISCC.exe installer\dicta.iss

#define AppName "Dicta"
#define AppVersion "1.0.10"
#define AppPublisher "JDMoreu"
#define AppExe "dicta.exe"
#define PayloadDir "..\dist\dicta"

[Setup]
AppId={{8F3E2C1A-5B47-4E9D-9C2A-7D1F6B4A3E10}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppSupportURL=https://github.com/JDMoreu/dicta
AppUpdatesURL=https://github.com/JDMoreu/dicta/releases/latest
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; Sin UAC: instalación por usuario.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist
OutputBaseFilename=dicta-{#AppVersion}-setup
SetupIconFile=..\dicta.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; La app vive en la bandeja: tras instalar se puede abrir directamente.
DisableFinishedPage=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked
Name: "startup"; Description: "Abrir Dicta al iniciar sesión"; GroupDescription: "Inicio automático:"; Flags: unchecked

[Files]
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "Dicta"; ValueData: """{app}\{#AppExe}"""; Flags: uninsdeletevalue; Tasks: startup

[Run]
Filename: "{app}\{#AppExe}"; Description: "Abrir {#AppName} ahora"; Flags: nowait postinstall skipifsilent
