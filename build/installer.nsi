; Downloader Bot — Setup.exe installer (NSIS)
; Build:  makensis build/installer.nsi
; Requires: NSIS 3.x

!define APP_NAME      "Downloader Bot"
!define APP_VERSION   "1.0.0"
!define APP_PUBLISHER "Downloader Bot"
!define APP_EXEC      "DownloaderBot.exe"

; Modern UI 2
!include "MUI2.nsh"

Name "${APP_NAME}"
OutFile "DownloaderBot-Setup-1.0.0.exe"
Unicode true

InstallDir "$PROGRAMFILES64\${APP_NAME}"
InstallDirRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "InstallLocation"

!define MUI_ABORTWARNING

Section "Install ${APP_NAME} ${APP_VERSION}" Sect
    SetOutPath "$INSTDIR"

    ; the PyInstaller single-file build (dist is at repo root, one level up from build/)
    File "..\dist\${APP_EXEC}"

    ; start menu + desktop shortcuts
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXEC}" "" "$INSTDIR\${APP_EXEC}" 0
    CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXEC}" "" "$INSTDIR\${APP_EXEC}" 0

    ; default download folder
    CreateDirectory "$LOCALAPPDATA\${APP_NAME}\Downloads"

    ; uninstaller + registry
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "InstallLocation" '"$INSTDIR"'
SectionEnd

Section "Uninstall"
    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    RMDir "$SMPROGRAMS\${APP_NAME}"

    Delete "$INSTDIR\Uninstall.exe"
    Delete "$INSTDIR\${APP_EXEC}"
    RMDir /r "$INSTDIR"

    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
SectionEnd
