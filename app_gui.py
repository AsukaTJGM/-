# -*- coding: utf-8 -*-
"""
淘宝双11自动化任务助手 - 桌面图形版 (GUI 稳健纯净版)
"""

import os
import sys
import time
import random
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADB_PATH = os.path.join(BASE_DIR, "adb.exe")
if not os.path.exists(ADB_PATH):
    ADB_PATH = "adb"

# Windows 绝不弹窗黑科技：同时注入 SW_HIDE 与 CREATE_NO_WINDOW
STARTUP_INFO = subprocess.STARTUPINFO()
STARTUP_INFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
STARTUP_INFO.wShowWindow = 0  # SW_HIDE
NO_WINDOW_FLAGS = 0x08000000  # CREATE_NO_WINDOW

# 使用纯 ASCII Unicode 转义，彻底杜绝 Windows 编码错乱 (CP936/GBK 乱码)
# 考试, 答题, 买, 下单, 充值, 邀请, 开卡, 拍立淘
DEFAULT_BLACK_LIST = [
    "\u8003\u8bd5", "\u7b54\u9898", "\u4e70", "\u4e0b\u5355", 
    "\u5145\u503c", "\u9080\u8bf7", "\u5f00\u5361", "\u62cd\u7acb\u6dd8"
]

class AutoTaskEngine:
    def __init__(self, log_callback, update_status_callback):
        self.log = log_callback
        self.update_status = update_status_callback
        self.is_running = False
        self.ocr = None
        self.device_id = None

    def init_ocr(self):
        if self.ocr is None:
            self.log("正在初始化 AI 视觉识别引擎 (RapidOCR)...")
            from rapidocr_onnxruntime import RapidOCR
            self.ocr = RapidOCR()
            self.log("AI 视觉引擎初始化完成！")

    def run_adb(self, cmd_list):
        full_cmd = [ADB_PATH]
        if self.device_id:
            full_cmd += ["-s", self.device_id]
        full_cmd += cmd_list
        try:
            # 彻底静默执行，注入 STARTUPINFO 隐藏窗口，绝不弹任何 cmd/conhost 窗口
            res = subprocess.run(
                full_cmd, 
                capture_output=True, 
                text=False, 
                timeout=15,
                startupinfo=STARTUP_INFO,
                creationflags=NO_WINDOW_FLAGS
            )
            return res.stdout
        except Exception as e:
            self.log(f"ADB 命令异常: {e}")
            return b""

    def get_screencap(self):
        return self.run_adb(["exec-out", "screencap", "-p"])

    def tap(self, x, y):
        self.run_adb(["shell", "input", "tap", str(int(x)), str(int(y))])

    def press_back(self):
        self.run_adb(["shell", "input", "keyevent", "4"])

    def swipe_screen(self, x1, y1, x2, y2, duration_ms=600):
        self.run_adb(["shell", "input", "swipe", str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(int(duration_ms))])

    def ensure_screen_on(self):
        """确保手机屏幕点亮"""
        res = self.run_adb(["shell", "dumpsys", "window"])
        if b"mAwake=false" in res:
            self.log("⚠️ 检测到手机熄屏，正在自动点亮屏幕...")
            self.run_adb(["shell", "input", "keyevent", "224"])
            time.sleep(1.0)
            self.swipe_screen(600, 2000, 600, 500, 300)
            time.sleep(1.0)

    def check_and_dismiss_open_dialog(self):
        img_bytes = self.get_screencap()
        if not img_bytes:
            return False
        res, _ = self.ocr(img_bytes)
        if not res:
            return False
        all_text = "".join([l[1] for l in res])
        # "想要打开" or "允许打开" or "小程序"
        if "\u60f3\u8981\u6253\u5f00" in all_text or "\u5141\u8bb8\u6253\u5f00" in all_text or "\u5c0f\u7a0b\u5e8f" in all_text:
            self.log("  🔔 捕获到【打开小程序】授权弹窗...")
            # 1. 尝试勾选『始终允许打开』
            for l in res:
                box, txt = l[0], l[1]
                cy = (box[0][1] + box[2][1]) / 2
                if any(k in txt for k in ["\u59cb\u7ec8", "\u5141\u8bb8"]) and cy > 1800:
                    cx = (box[0][0] + box[1][0]) / 2
                    self.tap(cx - 150, cy)
                    time.sleep(0.5)
                    break

            # 2. 精准点击底部的『打开』按钮（严格限定 Y>2000 且 X>600，绝不误点标题！）
            for l in res:
                box, txt = l[0], l[1]
                cx = (box[0][0] + box[1][0]) / 2
                cy = (box[0][1] + box[2][1]) / 2
                if txt.strip() in ["\u6253\u5f00", "\u5141\u8bb8"] and cy > 2000 and cx > 600:
                    self.log(f"  👉 精准点击『打开』按钮 (坐标: {int(cx)}, {int(cy)})...")
                    self.tap(cx, cy)
                    time.sleep(2.0)
                    return True

            # 3. 兜底坐标点击右下角『打开』按钮
            self.log("  👉 兜底点击右下角『打开』坐标 (870, 2350)...")
            self.tap(870, 2350)
            time.sleep(2.0)
            return True
        return False

    def browse_reciprocating(self, total_seconds=18):
        self.log(f"  ⏱️ 开始 {total_seconds} 秒往复活跃滑动浏览...")
        start_time = time.time()
        step = 0
        while self.is_running and (time.time() - start_time < total_seconds):
            start_x = 600 + random.randint(-50, 50)
            end_x = start_x + random.randint(-30, 30)

            if step % 3 == 2:
                self.swipe_screen(start_x, 1000, end_x, 1700, random.randint(500, 800))
            else:
                self.swipe_screen(start_x, 1800, end_x, 900, random.randint(600, 900))

            step += 1
            time.sleep(random.uniform(1.6, 2.2))

    def return_to_task_list(self, max_backs=4):
        self.log("  🔙 正在快速返回任务弹窗...")
        for _ in range(max_backs):
            if not self.is_running:
                return False
            img_bytes = self.get_screencap()
            res, _ = self.ocr(img_bytes)
            all_text = "".join([l[1] for l in res]) if res else ""
            if "\u505a\u4efb\u52a1\u8d5a\u80fd\u91cf" in all_text or "\u7d2f\u8ba1\u4efb\u52a1\u5956\u52b1" in all_text:
                self.log("  ✅ 已回到主面板")
                return True
            self.press_back()
            time.sleep(0.8)
        return False

    def handle_landing_page(self, browse_seconds=18):
        time.sleep(1.0)
        img_bytes = self.get_screencap()
        res, _ = self.ocr(img_bytes)
        all_text = "".join([l[1] for l in res]) if res else ""

        if any(k in all_text for k in ["\u641c\u7d22\u6709\u798f\u5229", "\u641c\u7d22\u540e\u6d4f\u89c8", "\u641c\u7d22\u53d1\u73b0", "\u5386\u53f2\u641c\u7d22"]):
            self.log("  🔍 识别到【搜索任务】，快速点击关键词...")
            clicked = False
            if res:
                for l in res:
                    box, txt = l[0], l[1]
                    if any(k in txt for k in ["\u4e07\u4ee3", "hbn", "\u77ed\u88e4", "\u6a21\u578b", "\u53d1\u73b0"]):
                        cx = (box[0][0] + box[1][0]) / 2
                        cy = (box[0][1] + box[2][1]) / 2
                        self.log(f"  👉 命中词: {txt}，进入列表...")
                        self.tap(cx, cy)
                        clicked = True
                        break
            if not clicked:
                self.tap(300, 1100)
            time.sleep(1.2)

        self.browse_reciprocating(total_seconds=browse_seconds)
        self.return_to_task_list()

    def run_loop(self, max_tasks=40):
        self.is_running = True
        try:
            self.init_ocr()
        except Exception as e:
            self.log(f"❌ 初始化 OCR 失败: {e}")
            self.is_running = False
            self.update_status("idle")
            return

        self.log("=" * 45)
        self.log("🚀 自动化任务循环启动！")
        self.log("=" * 45)

        completed = 0
        no_button_retries = 0

        while self.is_running and (completed < max_tasks):
            self.ensure_screen_on()
            img_bytes = self.get_screencap()
            if not img_bytes:
                self.log("❌ 截图失败，请检查手机 ADB 连接")
                time.sleep(2)
                continue

            result, _ = self.ocr(img_bytes)
            if not result:
                self.log("⚠️ 画面未识别到文字，请确保手机屏幕停留在【做任务赚能量】")
                time.sleep(2)
                continue

            buttons = []
            text_items = []

            for line in result:
                box, text, score = line[0], line[1], line[2]
                center_x = (box[0][0] + box[1][0]) / 2
                center_y = (box[0][1] + box[2][1]) / 2

                # 宽泛匹配右侧按钮：只要在右侧且包含“去”或“浏览”或“逛”或“完成”
                # "\u53bb" (去), "\u5b8c\u6210" (完成), "\u6d4f\u89c8" (浏览), "\u901b" (逛)
                is_btn = any(b in text for b in ["\u53bb", "\u5b8c\u6210", "\u6d4f\u89c8", "\u901b"])
                if is_btn and center_x > 800:
                    buttons.append({"box": box, "center": (center_x, center_y), "text": text})
                else:
                    text_items.append({"box": box, "center": (center_x, center_y), "text": text})

            if not buttons:
                self.log("🔄 当前屏幕无可用按钮，向下滑动刷新列表...")
                self.swipe_screen(600, 2100, 600, 1100, 600)
                time.sleep(2)
                no_button_retries += 1
                if no_button_retries >= 3:
                    self.log("🎉 连续多次未发现新任务，所有任务已全部刷完！")
                    break
                continue

            buttons.sort(key=lambda b: b["center"][1])
            target_button = None
            target_task_name = "浏览任务"

            for btn in buttons:
                btn_y = btn["center"][1]
                matched_texts = [
                    t["text"] for t in text_items 
                    if abs(t["center"][1] - btn_y) < 80 and t["center"][0] < 850
                ]
                row_title = "".join(matched_texts)

                is_black = any(bad in row_title for bad in DEFAULT_BLACK_LIST)
                if not is_black:
                    target_button = btn
                    target_task_name = row_title if row_title else btn["text"]
                    break
                else:
                    self.log(f"  ⏭️ 跳过特殊任务: {row_title}")

            if not target_button:
                self.log("当前屏幕全是特殊任务，向下滑动翻页...")
                self.swipe_screen(600, 2100, 600, 1100, 600)
                time.sleep(2)
                continue

            # "点击去逛" (\u70b9\u51fb\u53bb\u901b), "浏览" (\u6d4f\u89c8), "搜" (\u641c)
            is_click_and_return = "\u70b9\u51fb\u53bb\u901b" in target_task_name or ("\u6d4f\u89c8" not in target_task_name and "\u641c" not in target_task_name)
            self.log(f"\n👉 [点击任务] {target_task_name} (坐标: {int(target_button['center'][0])}, {int(target_button['center'][1])})")
            self.tap(target_button["center"][0], target_button["center"][1])

            if is_click_and_return:
                self.log("  ⚡ 识别为【点击即领】任务，极速唤起返回...")
                time.sleep(0.8)
                self.check_and_dismiss_open_dialog()
                time.sleep(0.5)
                self.return_to_task_list()
            else:
                browse_sec = 6 if "5\u79d2" in target_task_name else 17
                self.handle_landing_page(browse_seconds=browse_sec)

            completed += 1
            no_button_retries = 0
            self.log(f"✅ 已累计完成 {completed} 个任务！\n")
            time.sleep(0.4)

        self.is_running = False
        self.update_status("idle")
        self.log(f"\n🏁 任务结束，累计执行 {completed} 次任务！")


class AppGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("淘宝双11自动化助手 v1.0")
        self.geometry("680x640")
        self.minsize(580, 520)

        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.engine = AutoTaskEngine(self.append_log, self.set_status)
        self.worker_thread = None

        self.setup_ui()
        self.check_device()

    def setup_ui(self):
        top_frame = ttk.Frame(self, padding="12 10")
        top_frame.pack(fill=tk.X)

        title_lbl = ttk.Label(top_frame, text="淘宝双11自动化任务助手", font=("Microsoft YaHei UI", 15, "bold"))
        title_lbl.pack(side=tk.LEFT)

        self.status_badge = ttk.Label(top_frame, text="● 待命", font=("Microsoft YaHei UI", 10), foreground="#666666")
        self.status_badge.pack(side=tk.RIGHT, padx=10)

        dev_group = ttk.LabelFrame(self, text=" 设备连接管理 ", padding="10")
        dev_group.pack(fill=tk.X, padx=14, pady=5)

        f1 = ttk.Frame(dev_group)
        f1.pack(fill=tk.X, pady=2)

        ttk.Label(f1, text="当前设备:", font=("Microsoft YaHei UI", 10)).pack(side=tk.LEFT, padx=5)
        self.dev_label = ttk.Label(f1, text="正在检测...", font=("Microsoft YaHei UI", 10, "bold"), foreground="#2980b9")
        self.dev_label.pack(side=tk.LEFT, padx=5)

        self.btn_refresh_dev = ttk.Button(f1, text="🔄 刷新设备", command=self.check_device)
        self.btn_refresh_dev.pack(side=tk.RIGHT, padx=5)

        f2 = ttk.Frame(dev_group)
        f2.pack(fill=tk.X, pady=6)

        ttk.Label(f2, text="无线连接:").pack(side=tk.LEFT, padx=5)
        self.ip_entry = ttk.Entry(f2, width=24)
        self.ip_entry.insert(0, "192.168.1.104:33821")
        self.ip_entry.pack(side=tk.LEFT, padx=5)

        self.btn_connect = ttk.Button(f2, text="一键连接无线", command=self.connect_wireless)
        self.btn_connect.pack(side=tk.LEFT, padx=5)

        self.btn_scrcpy = ttk.Button(f2, text="📱 打开投屏监视", command=self.open_scrcpy)
        self.btn_scrcpy.pack(side=tk.RIGHT, padx=5)

        ctl_group = ttk.LabelFrame(self, text=" 任务控制与配置 ", padding="10")
        ctl_group.pack(fill=tk.X, padx=14, pady=5)

        f3 = ttk.Frame(ctl_group)
        f3.pack(fill=tk.X, pady=4)

        ttk.Label(f3, text="最大任务次数:").pack(side=tk.LEFT, padx=5)
        self.task_num_spin = ttk.Spinbox(f3, from_=1, to=100, width=8)
        self.task_num_spin.set(40)
        self.task_num_spin.pack(side=tk.LEFT, padx=5)

        self.btn_start = ttk.Button(f3, text="▶ 启动全自动任务", command=self.start_task)
        self.btn_start.pack(side=tk.RIGHT, padx=6)

        self.btn_stop = ttk.Button(f3, text="⏹ 停止运行", command=self.stop_task, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.RIGHT, padx=6)

        log_group = ttk.LabelFrame(self, text=" 实时执行日志 ", padding="8")
        log_group.pack(fill=tk.BOTH, expand=True, padx=14, pady=6)

        self.log_text = scrolledtext.ScrolledText(
            log_group, wrap=tk.WORD, font=("Consolas", 10),
            background="#1e1e1e", foreground="#d4d4d4", insertbackground="white"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def append_log(self, text):
        def _append():
            timestamp = time.strftime("[%H:%M:%S] ")
            self.log_text.insert(tk.END, timestamp + text + "\n")
            self.log_text.see(tk.END)
        self.after(0, _append)

    def set_status(self, state):
        def _update():
            if state == "running":
                self.status_badge.config(text="● 正在自动运行中", foreground="#27ae60")
                self.btn_start.config(state=tk.DISABLED)
                self.btn_stop.config(state=tk.NORMAL)
            else:
                self.status_badge.config(text="● 已停止 / 待命", foreground="#666666")
                self.btn_start.config(state=tk.NORMAL)
                self.btn_stop.config(state=tk.DISABLED)
        self.after(0, _update)

    def check_device(self):
        try:
            res = subprocess.run([ADB_PATH, "devices"], capture_output=True, text=True, timeout=5, startupinfo=STARTUP_INFO, creationflags=NO_WINDOW_FLAGS)
            lines = [l.strip() for l in res.stdout.splitlines() if l.strip()]
            devs = [l for l in lines[1:] if "device" in l and "offline" not in l]
            if devs:
                dev_name = devs[0].split()[0]
                self.engine.device_id = dev_name
                self.dev_label.config(text=f"🟢 已连接 ({dev_name})", foreground="#27ae60")
                self.append_log(f"检测到可用设备: {dev_name}")
            else:
                self.engine.device_id = None
                self.dev_label.config(text="🔴 未检测到设备", foreground="#c0392b")
                self.append_log("⚠️ 当前无已连接的 ADB 设备")
        except Exception as e:
            self.dev_label.config(text="❌ ADB 检测异常", foreground="#c0392b")
            self.append_log(f"ADB 检测失败: {e}")

    def connect_wireless(self):
        target = self.ip_entry.get().strip()
        if not target:
            messagebox.showwarning("提示", "请输入手机无线调试的 IP:端口")
            return
        self.append_log(f"正在尝试连接无线设备: {target}...")
        try:
            res = subprocess.run([ADB_PATH, "connect", target], capture_output=True, text=True, timeout=8, startupinfo=STARTUP_INFO, creationflags=NO_WINDOW_FLAGS)
            self.append_log(res.stdout.strip())
            self.check_device()
        except Exception as e:
            self.append_log(f"连接失败: {e}")

    def open_scrcpy(self):
        scrcpy_exe = os.path.join(os.path.dirname(BASE_DIR), "scrcpy-win64-v5.0.1", "scrcpy.exe")
        if not os.path.exists(scrcpy_exe):
            scrcpy_exe = "scrcpy"
        try:
            subprocess.Popen([scrcpy_exe, "--no-audio", "-m", "1024"])
            self.append_log("已唤起投屏监视窗口！")
        except Exception as e:
            self.append_log(f"启动投屏失败: {e}")

    def start_task(self):
        try:
            max_tasks = int(self.task_num_spin.get())
        except Exception:
            max_tasks = 40

        self.set_status("running")
        self.worker_thread = threading.Thread(target=self.engine.run_loop, args=(max_tasks,), daemon=True)
        self.worker_thread.start()

    def stop_task(self):
        self.engine.is_running = False
        self.append_log("🛑 正在停止任务...")
        self.set_status("idle")

if __name__ == "__main__":
    app = AppGUI()
    app.mainloop()
