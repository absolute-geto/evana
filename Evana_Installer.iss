; ============================================================
;              Evana Media Player — Installer Script
;              Requires: Inno Setup 6.x
; ============================================================

#define MyAppName "Evana"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "Evana"
#define MyAppURL "https://github.com/yourusername/evana"
#define MyAppExeName "Evana.exe"
#define MyAppId "{{B8E7F3A2-9C4D-4A1B-8E5F-2D3C4B5A6E7F}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; مسار التثبيت الافتراضي
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes

; اسم ملف Setup الناتج
OutputDir=installer_output
OutputBaseFilename=Evana_Setup_v{#MyAppVersion}

; ضغط قوي (يقلل الحجم)
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; الأيقونة
SetupIconFile=assets\evana_icon.ico

; صلاحيات
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; الويندوز المدعوم
MinVersion=10.0
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible

; أيقونة في Add/Remove Programs
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} {#MyAppVersion}

; تصميم حديث
WizardStyle=modern
WizardSizePercent=110

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "Create a &Quick Launch shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
; ✅ ننسخ كل الملفات من dist/Evana
Source: "dist\Evana\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

; Desktop (اختياري)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Quick Launch (اختياري)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; اختيار تشغيل البرنامج بعد التثبيت
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; حذف الملفات المؤقتة عند إلغاء التثبيت
Type: filesandordirs; Name: "{app}\_internal\__pycache__"
Type: files; Name: "{app}\assets\*.log"

[Registry]
; حفظ مسار التثبيت في الـ Registry
Root: HKA; Subkey: "Software\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletekey