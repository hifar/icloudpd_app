
icloudpd为 icloud 照片备份功能
例子：

e:\app\icloud\icloudpd-1.32.3-windows-amd64.exe ^
  --domain cn ^
  --directory "F:\_Archive\icloudphoto" ^
  --username "hifar@icloud.com" ^
  --folder-structure "{:%Y/%m}" ^
  --skip-created-before 2025-11-01 ^
  --skip-created-after 2025-11-26 ^
  --mfa-provider console

其它参数：
--dry-run 会认证并检查远端文件，但不会改动本地或 iCloud，用来测试参数很合适。

新版里 --delete-after-download 已经 deprecated，文档建议用 --keep-icloud-recent-days。但这是危险操作：它会删除 iCloud 中已下载或确认本地存在的资源，只保留指定天数内拍摄的内容；如果设为 0，会删除所有已处理资源。

