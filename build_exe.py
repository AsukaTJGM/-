import os
import sys
import shutil
import PyInstaller.__main__

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEST_DIR = r"C:\Users\Pan\Desktop\TaobaoDouble11Auto"

print(">>> 清理旧的编译缓存与输出...")
for p in [os.path.join(BASE_DIR, "dist"), os.path.join(BASE_DIR, "build")]:
    if os.path.exists(p):
        try:
            shutil.rmtree(p, ignore_errors=True)
        except Exception:
            pass

print(">>> 开始使用 PyInstaller 编译独立 EXE 软件 (TaobaoDouble11Auto)...")

params = [
    os.path.join(BASE_DIR, "app_gui.py"),
    "--name=TaobaoDouble11Auto",
    "--noconsole",
    "-y",
    "--clean",
    "--collect-all=rapidocr_onnxruntime",
    "--distpath=" + os.path.join(BASE_DIR, "dist"),
    "--workpath=" + os.path.join(BASE_DIR, "build"),
    "--specpath=" + BASE_DIR,
]

PyInstaller.__main__.run(params)

compiled_dir = os.path.join(BASE_DIR, "dist", "TaobaoDouble11Auto")
if not os.path.exists(compiled_dir):
    print("❌ 编译失败，未生成输出目录！")
    sys.exit(1)

# 复制 ADB 二进制文件到编译输出目录
for f in ["adb.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll"]:
    src = os.path.join(BASE_DIR, f)
    dst = os.path.join(compiled_dir, f)
    if os.path.exists(src):
        shutil.copy2(src, dst)

print(f">>> 正在同步到桌面运行目录: {DEST_DIR}...")
os.makedirs(DEST_DIR, exist_ok=True)

# 复制可执行文件和所有依赖
for item in os.listdir(compiled_dir):
    src_path = os.path.join(compiled_dir, item)
    dst_path = os.path.join(DEST_DIR, item)
    if os.path.isdir(src_path):
        os.makedirs(dst_path, exist_ok=True)
        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
    else:
        shutil.copy2(src_path, dst_path)

# 清理桌面目录下的旧残余文件
for fname in os.listdir(DEST_DIR):
    if fname.endswith(".bat") or fname.endswith(".py"):
        try:
            os.remove(os.path.join(DEST_DIR, fname))
        except Exception:
            pass

print(">>> 全部同步完成！桌面 EXE 已更新为最新免弹窗修复版本！")

