; =====================================================================
;  Instalador de eco  (Inno Setup 6 o 7)
;
;  Compilar (build.bat lo hace solo y busca la 6 y la 7):
;      "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" instalador.iss
;
;  Genera:  dist\eco-setup.exe
;
;  Qué instala:
;    - eco-ide.exe        (el IDE de escritorio)
;    - eco.exe            (el intérprete, tipo node)
;    - carpeta de ejemplos, README y docs/ (guías)
;    - acceso directo en Menú Inicio (y escritorio, opcional)
;    - {app} en el PATH del usuario  ->  puedes escribir "eco" en cualquier terminal
;    - asociación de archivos .eco  ->  doble clic abre el IDE
;
;  AppId distinto del antiguo "mi-lenguaje": los dos programas pueden
;  convivir y cada uno se desinstala desde su propia entrada.
; =====================================================================

#define MyAppName "eco"
#define MyAppVersion "0.4.0"
#define MyAppExeName "eco-ide.exe"
#define MyCliName "eco.exe"

[Setup]
AppId={{A3C7D95E-4B18-4F26-9D0A-6E52B8C41F07}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=Proyecto eco
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; sin pedir administrador
PrivilegesRequired=lowest
; refresca el PATH tras instalar
ChangesEnvironment=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=dist
OutputBaseFilename=eco-setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#MyAppName} {#MyAppVersion}
VersionInfoVersion={#MyAppVersion}
VersionInfoProductTextVersion={#MyAppVersion}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; \
      GroupDescription: "Accesos directos:"; Flags: unchecked
Name: "addpath"; Description: "Añadir eco al PATH (usar 'eco' en cualquier terminal)"; \
      GroupDescription: "Entorno:"; Flags: checkedonce
Name: "assoc"; Description: "Asociar los archivos .eco con el IDE"; \
      GroupDescription: "Entorno:"; Flags: checkedonce

[Files]
Source: "dist\{#MyCliName}";           DestDir: "{app}"; Flags: ignoreversion
Source: "dist\{#MyAppExeName}";        DestDir: "{app}"; Flags: ignoreversion
Source: "README.md";                   DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE";                     DestDir: "{app}"; Flags: ignoreversion
Source: "ejemplos\*";                  DestDir: "{app}\ejemplos"; \
        Flags: ignoreversion recursesubdirs createallsubdirs
Source: "docs\*";                      DestDir: "{app}\docs"; \
        Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName} IDE";      Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{#MyAppName} REPL";     Filename: "{app}\{#MyCliName}"
Name: "{group}\Ejemplos";              Filename: "{app}\ejemplos"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName} IDE"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; ---- PATH del usuario (solo si todavía no está) ----
; solo con la casilla "Añadir eco al PATH" marcada (Tasks: addpath)
; en la desinstalación lo limpiamos en [Code] para no borrar el resto del PATH
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; \
      ValueData: "{olddata};{app}"; Check: NeedsAddPath(); Tasks: addpath

; ---- asociación de .eco ----
Root: HKCU; Subkey: "Software\Classes\.eco"; ValueType: string; \
      ValueName: ""; ValueData: "ecolangfile"; \
      Flags: uninsdeletevalue uninsdeletekeyifempty; Tasks: assoc
Root: HKCU; Subkey: "Software\Classes\ecolangfile"; ValueType: string; \
      ValueName: ""; ValueData: "Programa de eco"; Flags: uninsdeletekey; Tasks: assoc
Root: HKCU; Subkey: "Software\Classes\ecolangfile\DefaultIcon"; ValueType: string; \
      ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"; Tasks: assoc
Root: HKCU; Subkey: "Software\Classes\ecolangfile\shell\open\command"; ValueType: string; \
      ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: assoc
Root: HKCU; Subkey: "Software\Classes\ecolangfile\shell\run\command"; ValueType: string; \
      ValueName: ""; ValueData: """{app}\{#MyCliName}"" ""%1"""; Tasks: assoc

[Run]
Filename: "{app}\{#MyAppExeName}"; \
      Description: "Abrir el {#MyAppName} IDE"; Flags: nowait postinstall skipifsilent

; al desinstalar, borramos la carpeta del programa si ha quedado vacía
[UninstallDelete]
Type: dirifempty; Name: "{app}"

[Code]
function NeedsAddPath(): Boolean;
var
  Path: String;
begin
  Result := True;
  if RegQueryStringValue(HKCU, 'Environment', 'Path', Path) then
    Result := Pos(LowerCase(ExpandConstant('{app}')), LowerCase(Path)) = 0;
end;

function RemoveSubstring(const Sub, S: String): String;
var
  P: Integer;
begin
  Result := S;
  P := Pos(LowerCase(Sub), LowerCase(Result));
  while P > 0 do
  begin
    Delete(Result, P, Length(Sub));
    P := Pos(LowerCase(Sub), LowerCase(Result));
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Path: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    { sacamos nuestra entrada del PATH sin tocar el resto }
    if RegQueryStringValue(HKCU, 'Environment', 'Path', Path) then
    begin
      Path := RemoveSubstring(';' + ExpandConstant('{app}'), Path);
      Path := RemoveSubstring(ExpandConstant('{app}'), Path);
      RegWriteExpandStringValue(HKCU, 'Environment', 'Path', Path);
    end;
  end;
end;
