# iCloudPD Backup Assistant

A small Tkinter desktop app for Windows that builds and launches icloudpd backup commands.

Chinese version: see README.zh-CN.md.

## Dependency: icloudpd

This project depends on icloudpd and does not bundle icloudpd itself.

- Upstream project: https://github.com/icloud-photos-downloader/icloud_photos_downloader
- You must install or download an icloudpd executable before using this app.
- Default executable path used by this app:
  e:\app\icloud\icloudpd-1.32.3-windows-amd64.exe

## Features

- Input year-month, iCloud username, icloudpd executable path, and backup target path
- Supports two filter modes: by month or by date range
- Always adds folder structure argument: --folder-structure "{:%Y/%m}"
- Optional domain argument: --domain cn
- Always adds MFA provider argument: --mfa-provider console
- Optional dry run: --dry-run
- Optional post-backup cleanup argument: --keep-icloud-recent-days 0
- Launches icloudpd in a real Windows console for interactive password and MFA input

## Run

From this workspace, run:

  e:/develop/icloud_photobackup/.venv/Scripts/python.exe icloud_pd_app.py

## Build EXE with PyInstaller

Install build dependency:

  e:/develop/icloud_photobackup/.venv/Scripts/python.exe -m pip install -r requirements.txt

Build one-file GUI executable:

  e:/develop/icloud_photobackup/.venv/Scripts/python.exe -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --name icloud_pd_app ^
    icloud_pd_app.py

Output:

  dist/icloud_pd_app.exe

## Notes

- This app only prepares and starts commands.
- Ensure the target machine also has a valid icloudpd executable.