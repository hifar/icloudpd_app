# iCloudPD 备份助手

这是一个基于 Tkinter 的 Windows 桌面工具，用来生成并启动 icloudpd 备份命令。

## 依赖说明：icloudpd

本项目依赖 icloudpd，本工具不会内置 icloudpd 可执行文件。

- 上游项目地址：https://github.com/icloud-photos-downloader/icloud_photos_downloader
- 使用前请先安装或下载 icloudpd 可执行文件
- 本工具默认路径：
    e:\app\icloud\icloudpd-1.32.3-windows-amd64.exe

## 功能

- 输入备份年月、iCloud 账户名、icloudpd 可执行文件路径和备份目标路径
- 支持两种筛选方式：按月份、按日期范围
- 支持界面中英文切换（默认英文）
- 固定追加参数：--folder-structure "{:%Y/%m}"
- 可选参数：--domain cn
- 固定追加参数：--mfa-provider console
- 可选参数：--dry-run
- 可选参数：--keep-icloud-recent-days 0（备份后删除）
- 运行时打开真实 Windows 控制台，支持密码和 MFA 交互输入

## 运行

在项目目录执行：

    e:/develop/icloud_photobackup/.venv/Scripts/python.exe icloud_pd_app.py

## 使用 PyInstaller 打包 EXE

先安装打包依赖：

    e:/develop/icloud_photobackup/.venv/Scripts/python.exe -m pip install -r requirements.txt

再执行打包：

    e:/develop/icloud_photobackup/.venv/Scripts/python.exe -m PyInstaller ^
      --noconfirm ^
      --clean ^
      --onefile ^
      --windowed ^
      --name icloud_pd_app ^
      icloud_pd_app.py

产物位置：

    dist/icloud_pd_app.exe