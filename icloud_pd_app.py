import re
import subprocess
import threading
import tkinter as tk
from calendar import monthrange
from datetime import date, timedelta
from tkinter import messagebox, ttk


DEFAULT_ICLOUD_EXE = r"e:\app\icloud\icloudpd-1.32.3-windows-amd64.exe"
DEFAULT_TARGET_DIR = r"F:\_Archive\icloudphoto"


class ICloudPDApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("iCloudPD 备份助手")
        self.root.geometry("980x720")

        self.process: subprocess.Popen | None = None

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

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        form = ttk.Frame(self.root, padding=12)
        form.grid(row=0, column=0, sticky="nsew")

        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="筛选方式").grid(row=0, column=0, sticky="w", pady=4)
        filter_frame = ttk.Frame(form)
        filter_frame.grid(row=0, column=1, sticky="w", pady=4)
        ttk.Radiobutton(
            filter_frame,
            text="按月份",
            value="month",
            variable=self.filter_mode_var,
            command=self._on_filter_mode_change,
        ).pack(side="left", padx=(0, 14))
        ttk.Radiobutton(
            filter_frame,
            text="按日期范围",
            value="date_range",
            variable=self.filter_mode_var,
            command=self._on_filter_mode_change,
        ).pack(side="left")

        self.year_month_entry = ttk.Entry(form, textvariable=self.year_month_var)
        self.year_month_entry.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="备份年月 (YYYY-MM)").grid(row=1, column=0, sticky="w", pady=4)

        ttk.Label(form, text="开始日期 (YYYY-MM-DD)").grid(row=2, column=0, sticky="w", pady=4)
        self.start_date_entry = ttk.Entry(form, textvariable=self.start_date_var)
        self.start_date_entry.grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="结束日期 (YYYY-MM-DD)").grid(row=3, column=0, sticky="w", pady=4)
        self.end_date_entry = ttk.Entry(form, textvariable=self.end_date_var)
        self.end_date_entry.grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="iCloud 可执行路径").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.icloud_exe_var).grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="备份目标路径").grid(row=5, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.target_dir_var).grid(row=5, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="iCloud 账户名").grid(row=6, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.username_var).grid(row=6, column=1, sticky="ew", pady=4)

        options = ttk.Frame(form)
        options.grid(row=7, column=0, columnspan=2, sticky="w", pady=6)
        ttk.Checkbutton(options, text="domain cn", variable=self.domain_cn_var).pack(side="left", padx=(0, 14))
        ttk.Checkbutton(options, text="Dry Run", variable=self.dry_run_var).pack(side="left", padx=(0, 14))
        ttk.Checkbutton(options, text="备份后删除（--keep-icloud-recent-days 0）", variable=self.delete_after_backup_var).pack(side="left")

        buttons = ttk.Frame(form)
        buttons.grid(row=8, column=0, columnspan=2, sticky="w", pady=(8, 2))
        ttk.Button(buttons, text="生成命令预览", command=self.preview_command).pack(side="left", padx=(0, 8))
        self.run_btn = ttk.Button(buttons, text="运行", command=self.run_command)
        self.run_btn.pack(side="left", padx=(0, 8))
        self.stop_btn = ttk.Button(buttons, text="停止", command=self.stop_command, state="disabled")
        self.stop_btn.pack(side="left")

        preview_box = ttk.LabelFrame(self.root, text="命令预览", padding=8)
        preview_box.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        preview_box.columnconfigure(0, weight=1)
        preview_box.rowconfigure(0, weight=1)

        self.command_preview = tk.Text(preview_box, height=4, wrap="word")
        self.command_preview.grid(row=0, column=0, sticky="nsew")

        output_box = ttk.LabelFrame(self.root, text="运行状态", padding=8)
        output_box.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        output_box.columnconfigure(0, weight=1)
        output_box.rowconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=2)

        self.output_text = tk.Text(output_box, wrap="word")
        self.output_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(output_box, orient="vertical", command=self.output_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.output_text.config(yscrollcommand=scrollbar.set)
        self.output_text.insert(
            tk.END,
            "运行后会打开真实控制台窗口，可在其中输入密码和 MFA。\n",
        )
        self.output_text.config(state="disabled")
        self._on_filter_mode_change()

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
            raise ValueError("备份年月格式必须是 YYYY-MM，例如 2026-07")

        year, month = re.split(r"[-/]", value)

        month_int = int(month)
        if month_int < 1 or month_int > 12:
            raise ValueError("备份年月格式必须是 YYYY-MM，例如 2026-07")

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

    @staticmethod
    def _parse_iso_date(value: str, field_name: str) -> date:
        text = value.strip()
        if not text:
            raise ValueError(f"请填写{field_name}")
        try:
            return date.fromisoformat(text)
        except ValueError as exc:
            raise ValueError(f"{field_name}格式必须是 YYYY-MM-DD") from exc

    def _resolve_date_filters(self) -> tuple[str, str] | tuple[None, None]:
        mode = self.filter_mode_var.get()
        if mode == "month":
            year, month = self._parse_year_month(self.year_month_var.get())
            if year is None or month is None:
                return None, None
            return self._month_date_range(year, month)

        if mode == "date_range":
            start = self._parse_iso_date(self.start_date_var.get(), "开始日期")
            end = self._parse_iso_date(self.end_date_var.get(), "结束日期")
            if end < start:
                raise ValueError("结束日期不能早于开始日期")

            # Use end date + 1 day as exclusive upper bound.
            end_exclusive = end + timedelta(days=1)
            return start.isoformat(), end_exclusive.isoformat()

        raise ValueError("未知的筛选方式")

    def _build_command(self) -> list[str]:
        exe = self.icloud_exe_var.get().strip()
        target = self.target_dir_var.get().strip()
        username = self.username_var.get().strip()
        skip_before, skip_after = self._resolve_date_filters()

        if not exe:
            raise ValueError("请填写 iCloud 可执行路径")
        if not target:
            raise ValueError("请填写备份目标路径")
        if not username:
            raise ValueError("请填写 iCloud 账户名")

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
            messagebox.showerror("参数错误", str(exc))
            return

        cmd_text = self._to_cmdline(cmd)
        self.command_preview.delete("1.0", tk.END)
        self.command_preview.insert(tk.END, cmd_text)

    def run_command(self) -> None:
        if self.process is not None:
            messagebox.showinfo("提示", "已有命令正在运行，请先停止或等待完成")
            return

        try:
            cmd = self._build_command()
        except ValueError as exc:
            messagebox.showerror("参数错误", str(exc))
            return

        cmd_text = self._to_cmdline(cmd)
        self.command_preview.delete("1.0", tk.END)
        self.command_preview.insert(tk.END, cmd_text)

        confirmed = messagebox.askyesno("确认运行", f"请确认命令后执行：\n\n{cmd_text}")
        if not confirmed:
            return

        self._append_status(f"> {cmd_text}\n")

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
            self.root.after(0, lambda: self._append_status("[错误] 未找到可执行文件，请检查 iCloud 路径。\n"))
            self.root.after(0, self._mark_process_done)
            return
        except Exception as exc:
            self.root.after(0, lambda: self._append_status(f"[错误] 启动失败: {exc}\n"))
            self.root.after(0, self._mark_process_done)
            return

        pid = self.process.pid
        self.root.after(
            0,
            lambda: self._append_status(
                f"[提示] 已在新控制台窗口启动进程 (PID: {pid})，请在控制台中交互输入密码/MFA。\n"
            ),
        )

        code = self.process.wait()
        self.root.after(0, lambda: self._append_status(f"\n[完成] 进程退出码: {code}\n"))
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
            self._append_status("\n[提示] 已请求停止进程...\n")
        except Exception as exc:
            self._append_status(f"\n[错误] 停止进程失败: {exc}\n")

    def _schedule_output_poll(self) -> None:
        # Kept for compatibility with existing initialization flow.
        return


def main() -> None:
    root = tk.Tk()
    app = ICloudPDApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
