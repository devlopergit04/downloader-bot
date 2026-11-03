; Downloader Bot — Setup.exe installer (NSIS)
; Build:  pyinstaller ...  then  makensis build/installer.nsi
; Requires: NSIS 3.x  (https://nsis.sourceforge.io)

!define APP_NAME      "Downloader Bot"
!define APP_VERSION   "1.0.0"
!define APP_PUBLISHER "Downloader Bot"
!define APP_EXEC      "DownloaderBot.exe"
!define APP_ICON      "assets\\logo.ico"

; Modern UI 2
!include "MUI2.nsh"

Name "${APP_NAME}"
OutFile "DownloaderBot-Setup-${APP_VERSION}.exe"
Unicode true

; Install location: Program Files (64-bit aware)
InstallDir "$PROGRAMFILES64\\${APP_NAME}"
InstallDirRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "InstallLocation"

; Installer metadata
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\\${APP_EXEC}"

; Sections
Section "Install ${APP_NAME} ${APP_VERSION}" Sect
    SetOutPath "$INSTDIR"

    ; the PyInstaller single-file build
    File "dist\\${APP_EXEC}"

    ; desktop + start menu shortcuts
    CreateDirectory "$SMPROGRAMS\\${APP_NAME}"
    CreateShortcut "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXEC}" "" "$INSTDIR\\${APP_EXEC}" 0
    CreateShortcut "$DESKTOP\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXEC}" "" "$INSTDIR\\${APP_EXEC}" 0

    ; default download folder
    CreateDirectory "$LOCALAPPDATA\\${APP_NAME}\\Downloads"

    ; uninstaller + registry
    WriteUninstaller "$INSTDIR\\Uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "UninstallString" '"$INSTDIR\\Uninstall.exe"'
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "InstallLocation" '"$INSTDIR"'
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayIcon" '"$INSTDIR\\${APP_EXEC}"'
SectionEnd

Section "Uninstall"
    Delete "$DESKTOP\\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk"
    RMDir "$SMPROGRAMS\\${APP_NAME}"

    Delete "$INSTDIR\\Uninstall.exe"
    Delete "$INSTDIR\\${APP_EXEC}"
    RMDir /r "$INSTDIR"

    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}"
SectionEnd

; Run the app after install (finish page button)
Function .onFinish
    IfFileExists "$INSTDIR\\${APP_EXEC}" _RunIt
    Goto done
_RunIt:
    ExecWait '"$INSTDIR\\${APP_EXEC}"'
    Goto done
done:
FunctionEnd
