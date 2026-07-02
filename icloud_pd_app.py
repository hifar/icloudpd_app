import re
import subprocess
import threading
import tkinter as tk
from calendar import monthrange
from datetime import date, timedelta
from tkinter import messagebox, ttk


DEFAULT_ICLOUD_EXE = r"e:\app\icloud\icloudpd-1.32.3-windows-amd64.exe"
DEFAULT_TARGET_DIR = r"F:\_Archive\icloudphoto"


I18N = {
    "en": {
        "window_title": "iCloudPD Backup Assistant",
        "language": "Language",
        "lang_en": "English",
        "lang_zh": "Chinese",
        "filter_mode": "Filter Mode",
        "mode_month": "By Month",
        "mode_date_range": "By Date Range",
        "year_month": "Year-Month (YYYY-MM)",
        "start_date": "Start Date (YYYY-MM-DD)",
        "end_date": "End Date (YYYY-MM-DD)",
        "icloud_exe": "iCloud Executable Path",
        "target_dir": "Backup Target Path",
        "username": "iCloud Username",
        "domain_cn": "domain cn",
        "dry_run": "Dry Run",
        "delete_after_backup": "Delete After Backup (--keep-icloud-recent-days 0)",
        "preview_btn": "Preview Command",
        "run_btn": "Run",
        "stop_btn": "Stop",
        "preview_box": "Command Preview",
        "status_box": "Run Status",
        "status_intro": "The app launches a real console window for password and MFA input.\n",
        "error_title": "Invalid Parameters",
        "info_title": "Info",
        "confirm_title": "Confirm Run",
        "confirm_text": "Please confirm before running:\n\n{cmd}",
        "already_running": "A command is already running. Please stop it or wait for completion.",
        "err_year_month": "Year-Month must use YYYY-MM format, for example 2026-07",
        "err_fill": "Please fill in {field}",
        "err_date_format": "{field} must use YYYY-MM-DD format",
        "err_end_before_start": "End date cannot be earlier than start date",
        "err_unknown_mode": "Unknown filter mode",
        "err_exe": "Please provide iCloud executable path",
        "err_target": "Please provide backup target path",
        "err_username": "Please provide iCloud username",
        "field_start_date": "Start Date",
        "field_end_date": "End Date",
        "status_cmd": "> {cmd}\n",
        "status_not_found": "[Error] Executable not found. Please check iCloud path.\n",
        "status_start_failed": "[Error] Failed to start: {err}\n",
        "status_started": "[Info] Process started in a new console window (PID: {pid}). Use that console for password/MFA input.\n",
        "status_done": "\n[Done] Process exit code: {code}\n",
        "status_stop_requested": "\n[Info] Stop request sent...\n",
        "status_stop_failed": "\n[Error] Failed to stop process: {err}\n",
    },
    "zh": {
        "window_title": "iCloudPD 备份助手",
        "language": "语言",
        "lang_en": "英文",
        "lang_zh": "中文",
        "filter_mode": "筛选方式",
        "mode_month": "按月份",
        "mode_date_range": "按日期范围",
        "year_month": "备份年月 (YYYY-MM)",
        "start_date": "开始日期 (YYYY-MM-DD)",
        "end_date": "结束日期 (YYYY-MM-DD)",
        "icloud_exe": "iCloud 可执行路径",
        "target_dir": "备份目标路径",
        "username": "iCloud 账户名",
        "domain_cn": "domain cn",
        "dry_run": "Dry Run",
        "delete_after_backup": "备份后删除（--keep-icloud-recent-days 0）",
        "preview_btn": "生成命令预览",
        "run_btn": "运行",
        "stop_btn": "停止",
        "preview_box": "命令预览",
        "status_box": "运行状态",
        "status_intro": "运行后会打开真实控制台窗口，可在其中输入密码和 MFA。\n",
        "error_title": "参数错误",
        "info_title": "提示",
        "confirm_title": "确认运行",
        "confirm_text": "请确认命令后执行：\n\n{cmd}",
        "already_running": "已有命令正在运行，请先停止或等待完成",
        "err_year_month": "备份年月格式必须是 YYYY-MM，例如 2026-07",
        "err_fill": "请填写{field}",
        "err_date_format": "{field}格式必须是 YYYY-MM-DD",
        "err_end_before_start": "结束日期不能早于开始日期",
        "err_unknown_mode": "未知的筛选方式",
        "err_exe": "请填写 iCloud 可执行路径",
        "err_target": "请填写备份目标路径",
        "err_username": "请填写 iCloud 账户名",
        "field_start_date": "开始日期",
        "field_end_date": "结束日期",
        "status_cmd": "> {cmd}\n",
        "status_not_found": "[错误] 未找到可执行文件，请检查 iCloud 路径。\n",
        "status_start_failed": "[错误] 启动失败: {err}\n",
        "status_started": "[提示] 已在新控制台窗口启动进程 (PID: {pid})，请在控制台中交互输入密码/MFA。\n",
        "status_done": "\n[完成] 进程退出码: {code}\n",
        "status_stop_requested": "\n[提示] 已请求停止进程...\n",
        "status_stop_failed": "\n[错误] 停止进程失败: {err}\n",
    },
}


class ICloudPDApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.geometry("980x720")

        self.process: subprocess.Popen | None = None

        self.lang_var = tk.StringVar(value="en")
        self.year_month_var = tk.StringVar()
        self.filter_mode_var = tk.StringVar(value="month")
        self.start_date_var = tk.StringVar()
        self.end_date_var = tk.StringVar()
        self.icloud_exe_var = tk.StringVar(value=DEFAULT_ICLOUD_EXE)
        self.target_dir_var = tk.StringVar(value=DEFAULT_TARGET_DIR)
        self.username_var = tk.StringVar()
        self.domain_cn_var = tk.BooleanVar(value=True)
        self.dry_run_var = tk.BooleanVar(value=True)
        self.delete_after_backup_var = tk.BooleanVar(value=False)

        self._build_ui()
        self._schedule_output_poll()

    def t(self, key: str) -> str:
        lang = self.lang_var.get()
        return I18N.get(lang, I18N["en"]).get(key, key)

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        form = ttk.Frame(self.root, padding=12)
        form.grid(row=0, column=0, sticky="nsew")

        form.columnconfigure(1, weight=1)

        self.language_label = ttk.Label(form)
        self.language_label.grid(row=0, column=0, sticky="w", pady=4)
        language_frame = ttk.Frame(form)
        language_frame.grid(row=0, column=1, sticky="w", pady=4)
        self.lang_en_radio = ttk.Radiobutton(
            language_frame,
            value="en",
            variable=self.lang_var,
            command=self._apply_language,
        )
        self.lang_en_radio.pack(side="left", padx=(0, 14))
        self.lang_zh_radio = ttk.Radiobutton(
            language_frame,
            value="zh",
            variable=self.lang_var,
            command=self._apply_language,
        )
        self.lang_zh_radio.pack(side="left")

        self.filter_mode_label = ttk.Label(form)
        self.filter_mode_label.grid(row=1, column=0, sticky="w", pady=4)
        filter_frame = ttk.Frame(form)
        filter_frame.grid(row=1, column=1, sticky="w", pady=4)
        self.month_radio = ttk.Radiobutton(
            filter_frame,
            value="month",
            variable=self.filter_mode_var,
            command=self._on_filter_mode_change,
        )
        self.month_radio.pack(side="left", padx=(0, 14))
        self.date_range_radio = ttk.Radiobutton(
            filter_frame,
            value="date_range",
            variable=self.filter_mode_var,
            command=self._on_filter_mode_change,
        )
        self.date_range_radio.pack(side="left")

        self.year_month_label = ttk.Label(form)
        self.year_month_label.grid(row=2, column=0, sticky="w", pady=4)
        self.year_month_entry = ttk.Entry(form, textvariable=self.year_month_var)
        self.year_month_entry.grid(row=2, column=1, sticky="ew", pady=4)

        self.start_date_label = ttk.Label(form)
        self.start_date_label.grid(row=3, column=0, sticky="w", pady=4)
        self.start_date_entry = ttk.Entry(form, textvariable=self.start_date_var)
        self.start_date_entry.grid(row=3, column=1, sticky="ew", pady=4)

        self.end_date_label = ttk.Label(form)
        self.end_date_label.grid(row=4, column=0, sticky="w", pady=4)
        self.end_date_entry = ttk.Entry(form, textvariable=self.end_date_var)
        self.end_date_entry.grid(row=4, column=1, sticky="ew", pady=4)

        self.icloud_exe_label = ttk.Label(form)
        self.icloud_exe_label.grid(row=5, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.icloud_exe_var).grid(row=5, column=1, sticky="ew", pady=4)

        self.target_dir_label = ttk.Label(form)
        self.target_dir_label.grid(row=6, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.target_dir_var).grid(row=6, column=1, sticky="ew", pady=4)

        self.username_label = ttk.Label(form)
        self.username_label.grid(row=7, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.username_var).grid(row=7, column=1, sticky="ew", pady=4)

        options = ttk.Frame(form)
        options.grid(row=8, column=0, columnspan=2, sticky="w", pady=6)
        self.domain_checkbox = ttk.Checkbutton(options, variable=self.domain_cn_var)
        self.domain_checkbox.pack(side="left", padx=(0, 14))
        self.dry_run_checkbox = ttk.Checkbutton(options, variable=self.dry_run_var)
        self.dry_run_checkbox.pack(side="left", padx=(0, 14))
        self.delete_checkbox = ttk.Checkbutton(options, variable=self.delete_after_backup_var)
        self.delete_checkbox.pack(side="left")

        buttons = ttk.Frame(form)
        buttons.grid(row=9, column=0, columnspan=2, sticky="w", pady=(8, 2))
        self.preview_btn = ttk.Button(buttons, command=self.preview_command)
        self.preview_btn.pack(side="left", padx=(0, 8))
        self.run_btn = ttk.Button(buttons, command=self.run_command)
        self.run_btn.pack(side="left", padx=(0, 8))
        self.stop_btn = ttk.Button(buttons, command=self.stop_command, state="disabled")
        self.stop_btn.pack(side="left")

        self.preview_box = ttk.LabelFrame(self.root, padding=8)
        self.preview_box.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        self.preview_box.columnconfigure(0, weight=1)
        self.preview_box.rowconfigure(0, weight=1)

        self.command_preview = tk.Text(self.preview_box, height=4, wrap="word")
        self.command_preview.grid(row=0, column=0, sticky="nsew")

        self.output_box = ttk.LabelFrame(self.root, padding=8)
        self.output_box.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.output_box.columnconfigure(0, weight=1)
        self.output_box.rowconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=2)

        self.output_text = tk.Text(self.output_box, wrap="word")
        self.output_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.output_box, orient="vertical", command=self.output_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.output_text.config(yscrollcommand=scrollbar.set)

        self._set_intro_status()
        self._apply_language()
        self._on_filter_mode_change()

    def _set_intro_status(self) -> None:
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, self.t("status_intro"))
        self.output_text.config(state="disabled")

    def _apply_language(self) -> None:
        self.root.title(self.t("window_title"))

        self.language_label.config(text=self.t("language"))
        self.lang_en_radio.config(text=self.t("lang_en"))
        self.lang_zh_radio.config(text=self.t("lang_zh"))

        self.filter_mode_label.config(text=self.t("filter_mode"))
        self.month_radio.config(text=self.t("mode_month"))
        self.date_range_radio.config(text=self.t("mode_date_range"))

        self.year_month_label.config(text=self.t("year_month"))
        self.start_date_label.config(text=self.t("start_date"))
        self.end_date_label.config(text=self.t("end_date"))
        self.icloud_exe_label.config(text=self.t("icloud_exe"))
        self.target_dir_label.config(text=self.t("target_dir"))
        self.username_label.config(text=self.t("username"))

        self.domain_checkbox.config(text=self.t("domain_cn"))
        self.dry_run_checkbox.config(text=self.t("dry_run"))
        self.delete_checkbox.config(text=self.t("delete_after_backup"))

        self.preview_btn.config(text=self.t("preview_btn"))
        self.run_btn.config(text=self.t("run_btn"))
        self.stop_btn.config(text=self.t("stop_btn"))

        self.preview_box.config(text=self.t("preview_box"))
        self.output_box.config(text=self.t("status_box"))

        self._set_intro_status()

    def _on_filter_mode_change(self) -> None:
        is_month = self.filter_mode_var.get() == "month"
        self.year_month_entry.config(state="normal" if is_month else "disabled")
        self.start_date_entry.config(state="disabled" if is_month else "normal")
        self.end_date_entry.config(state="disabled" if is_month else "normal")

    def _append_status(self, text: str) -> None:
        self.output_text.config(state="normal")
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state="disabled")

    def _parse_year_month(self, year_month: str) -> tuple[str, str] | tuple[None, None]:
        value = year_month.strip()
        if not value:
            return None, None

        if not re.fullmatch(r"\d{4}[-/]\d{2}", value):
            raise ValueError(self.t("err_year_month"))

        year, month = re.split(r"[-/]", value)

        month_int = int(month)
        if month_int < 1 or month_int > 12:
            raise ValueError(self.t("err_year_month"))

        return year, month

    @staticmethod
    def _month_date_range(year: str, month: str) -> tuple[str, str]:
        y = int(year)
        m = int(month)
        first = date(y, m, 1)
        last_day = monthrange(y, m)[1]
        last = date(y, m, last_day)
        # Use end date + 1 day to avoid excluding same-day photos by time boundary.
        end_exclusive = last + timedelta(days=1)
        return first.isoformat(), end_exclusive.isoformat()

    def _parse_iso_date(self, value: str, field_key: str) -> date:
        text = value.strip()
        if not text:
            raise ValueError(self.t("err_fill").format(field=self.t(field_key)))
        try:
            return date.fromisoformat(text)
        except ValueError as exc:
            raise ValueError(self.t("err_date_format").format(field=self.t(field_key))) from exc

    def _resolve_date_filters(self) -> tuple[str, str] | tuple[None, None]:
        mode = self.filter_mode_var.get()
        if mode == "month":
            year, month = self._parse_year_month(self.year_month_var.get())
            if year is None or month is None:
                return None, None
            return self._month_date_range(year, month)

        if mode == "date_range":
            start = self._parse_iso_date(self.start_date_var.get(), "field_start_date")
            end = self._parse_iso_date(self.end_date_var.get(), "field_end_date")
            if end < start:
                raise ValueError(self.t("err_end_before_start"))

            # Use end date + 1 day as exclusive upper bound.
            end_exclusive = end + timedelta(days=1)
            return start.isoformat(), end_exclusive.isoformat()

        raise ValueError(self.t("err_unknown_mode"))

    def _build_command(self) -> list[str]:
        exe = self.icloud_exe_var.get().strip()
        target = self.target_dir_var.get().strip()
        username = self.username_var.get().strip()
        skip_before, skip_after = self._resolve_date_filters()

        if not exe:
            raise ValueError(self.t("err_exe"))
        if not target:
            raise ValueError(self.t("err_target"))
        if not username:
            raise ValueError(self.t("err_username"))

        cmd = [
            exe,
            "--folder-structure",
            "{:%Y/%m}",
            "--directory",
            target,
            "--username",
            username,
            "--mfa-provider",
            "console",
        ]

        if self.domain_cn_var.get():
            cmd.extend(["--domain", "cn"])

        if skip_before is not None and skip_after is not None:
            cmd.extend(["--skip-created-before", skip_before])
            cmd.extend(["--skip-created-after", skip_after])

        if self.dry_run_var.get():
            cmd.append("--dry-run")

        if self.delete_after_backup_var.get():
            cmd.extend(["--keep-icloud-recent-days", "0"])

        return cmd

    @staticmethod
    def _to_cmdline(cmd: list[str]) -> str:
        return subprocess.list2cmdline(cmd)

    def preview_command(self) -> None:
        try:
            cmd = self._build_command()
        except ValueError as exc:
            messagebox.showerror(self.t("error_title"), str(exc))
            return

        cmd_text = self._to_cmdline(cmd)
        self.command_preview.delete("1.0", tk.END)
        self.command_preview.insert(tk.END, cmd_text)

    def run_command(self) -> None:
        if self.process is not None:
            messagebox.showinfo(self.t("info_title"), self.t("already_running"))
            return

        try:
            cmd = self._build_command()
        except ValueError as exc:
            messagebox.showerror(self.t("error_title"), str(exc))
            return

        cmd_text = self._to_cmdline(cmd)
        self.command_preview.delete("1.0", tk.END)
        self.command_preview.insert(tk.END, cmd_text)

        confirmed = messagebox.askyesno(
            self.t("confirm_title"),
            self.t("confirm_text").format(cmd=cmd_text),
        )
        if not confirmed:
            return

        self._append_status(self.t("status_cmd").format(cmd=cmd_text))

        self.run_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

        worker = threading.Thread(target=self._run_process_worker, args=(cmd,), daemon=True)
        worker.start()

    def _run_process_worker(self, cmd: list[str]) -> None:
        try:
            self.process = subprocess.Popen(
                cmd,
                creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
            )
        except FileNotFoundError:
            self.root.after(0, lambda: self._append_status(self.t("status_not_found")))
            self.root.after(0, self._mark_process_done)
            return
        except Exception as exc:
            self.root.after(0, lambda: self._append_status(self.t("status_start_failed").format(err=exc)))
            self.root.after(0, self._mark_process_done)
            return

        pid = self.process.pid
        self.root.after(
            0,
            lambda: self._append_status(self.t("status_started").format(pid=pid)),
        )

        code = self.process.wait()
        self.root.after(0, lambda: self._append_status(self.t("status_done").format(code=code)))
        self.root.after(0, self._mark_process_done)

    def _mark_process_done(self) -> None:
        self.process = None
        self.run_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def stop_command(self) -> None:
        if self.process is None:
            return

        try:
            self.process.terminate()
            self._append_status(self.t("status_stop_requested"))
        except Exception as exc:
            self._append_status(self.t("status_stop_failed").format(err=exc))

    def _schedule_output_poll(self) -> None:
        # Kept for compatibility with existing initialization flow.
        return


def main() -> None:
    root = tk.Tk()
    app = ICloudPDApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
