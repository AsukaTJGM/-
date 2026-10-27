# -*- coding: utf-8 -*-
"""
淘宝双11「淘金币赛车-做任务赚能量」电脑端全自动脚本 (增强搜索自适应版)
特性：
1. 智能识别「搜索有福利」任务：进入后自动点击搜索发现/历史词，进入结果页进行 18 秒真滑动
2. 循环智能返回：自动检测屏幕，按返回键直到彻底回到「做任务赚能量」弹窗，防止层级不一致卡死
3. 自动过滤答题、跨端跳支付宝、拍立淘相机等复杂任务
"""

import os
import sys
import time
import random
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rapidocr_onnxruntime import RapidOCR

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADB_PATH = os.path.join(BASE_DIR, "adb.exe")
if not os.path.exists(ADB_PATH):
    ADB_PATH = "adb"

ocr = RapidOCR()

# 黑名单：只跳过考试答题、拍立淘相机、充值下单等不可控任务
BLACK_LIST = ["考试", "答题", "买", "下单", "充值", "邀请", "开卡", "拍立淘"]

def run_adb(cmd_list):
    full_cmd = [ADB_PATH] + cmd_list
    res = subprocess.run(full_cmd, capture_output=True, text=False)
    return res.stdout

def get_screencap():
    return run_adb(["exec-out", "screencap", "-p"])

def tap(x, y):
    run_adb(["shell", "input", "tap", str(int(x)), str(int(y))])

def press_back():
    run_adb(["shell", "input", "keyevent", "4"])

def swipe_screen(x1, y1, x2, y2, duration_ms=600):
    run_adb(["shell", "input", "swipe", str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(int(duration_ms))])

def browse_reciprocating(total_seconds=18):
    """往复双向活跃滑动"""
    print(f"  ⏱️  开始 {total_seconds} 秒往复滑动浏览...")
    start_time = time.time()
    step = 0
    while time.time() - start_time < total_seconds:
        start_x = 600 + random.randint(-50, 50)
        end_x = start_x + random.randint(-30, 30)

        # 2次下滑，1次上滑回看，防止滑到底倒计时停止
        if step % 3 == 2:
            swipe_screen(start_x, 1000, end_x, 1700, random.randint(500, 800))
        else:
            swipe_screen(start_x, 1800, end_x, 900, random.randint(600, 900))

        step += 1
        time.sleep(random.uniform(1.6, 2.2))

def return_to_task_list(max_backs=4):
    """智能返回：一直按返回键，直到回到任务弹窗"""
    print("  🔙 正在智能返回任务弹窗...")
    for i in range(max_backs):
        img_bytes = get_screencap()
        res, _ = ocr(img_bytes)
        all_text = "".join([l[1] for l in res]) if res else ""
        if "做任务赚能量" in all_text or "累计任务奖励" in all_text:
            print("  ✅ 已成功回到【做任务赚能量】面板")
            return True
        press_back()
        time.sleep(1.8)
    return False

def check_and_dismiss_open_dialog():
    """检测并自动点击『“淘宝”想要打开“支付宝”小程序』确认弹窗"""
    img_bytes = get_screencap()
    res, _ = ocr(img_bytes)
    if not res:
        return False
    all_text = "".join([l[1] for l in res])
    if "想要打开" in all_text or "允许打开" in all_text:
        print("  🔔 捕获到【打开支付宝小程序】授权弹窗，正在自动点击『打开』...")
        # 优先点击『始终允许打开』复选框以绝后患 (X: 180, Y: 2180 附近)
        for l in res:
            box, txt = l[0], l[1]
            if "打开" in txt and (box[0][0] + box[1][0]) / 2 > 500:
                cx = (box[0][0] + box[1][0]) / 2
                cy = (box[0][1] + box[2][1]) / 2
                tap(cx, cy)
                time.sleep(1.5)
                return True
        # 兜底点击右下角『打开』按钮
        tap(860, 2360)
        time.sleep(1.5)
        return True
    return False

def handle_landing_page(browse_seconds=18):
    """检测落地页类型（处理搜一搜等特殊页面）"""
    time.sleep(2.0)
    img_bytes = get_screencap()
    res, _ = ocr(img_bytes)
    all_text = "".join([l[1] for l in res]) if res else ""

    # 如果是「搜一搜你心仪的宝贝」落地页
    if "搜索有福利" in all_text or "搜索后浏览" in all_text or "搜索发现" in all_text or "历史搜索" in all_text:
        print("  🔍 识别到【搜索任务】页面，正在自动点击搜索关键词...")
        clicked = False
        if res:
            for l in res:
                box, txt = l[0], l[1]
                if any(k in txt for k in ["神宝", "万代", "hbn", "短裤", "模型", "发现"]):
                    cx = (box[0][0] + box[1][0]) / 2
                    cy = (box[0][1] + box[2][1]) / 2
                    print(f"  👉 命中推荐搜索词: {txt}，点击进入搜索结果...")
                    tap(cx, cy)
                    clicked = True
                    break
        if not clicked:
            print("  👉 兜底点击推荐搜索卡片 (300, 1100)...")
            tap(300, 1100)

        time.sleep(2.5)

    # 无论普通浏览还是搜索结果，进入后均进行往复滑动
    browse_reciprocating(total_seconds=browse_seconds)

    # 智能返回任务列表
    return_to_task_list()

def analyze_and_execute_once():
    img_bytes = get_screencap()
    if not img_bytes:
        return False, "screencap_failed"

    result, _ = ocr(img_bytes)
    if not result:
        return False, "no_text"

    buttons = []
    text_items = []

    for line in result:
        box, text, score = line[0], line[1], line[2]
        center_x = (box[0][0] + box[1][0]) / 2
        center_y = (box[0][1] + box[2][1]) / 2

        if any(b in text for b in ["去完成", "去浏览", "去逛逛"]) and center_x > 800:
            buttons.append({"box": box, "center": (center_x, center_y), "text": text})
        else:
            text_items.append({"box": box, "center": (center_x, center_y), "text": text})

    if not buttons:
        return False, "no_buttons"

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

        is_black = any(bad in row_title for bad in BLACK_LIST)
        if not is_black:
            target_button = btn
            target_task_name = row_title if row_title else "未命名任务"
            break
        else:
            print(f"  ⏭️  跳过特殊任务: {row_title}")

    if not target_button:
        return False, "all_blacklisted"

    # 判断是否为「点击去逛」秒领任务（如去蚂蚁森林、逛支付宝金豆等，无需停留 15 秒）
    is_click_and_return = "点击去逛" in target_task_name or ("浏览" not in target_task_name and "搜" not in target_task_name)

    print(f"\n👉 [点击任务] {target_task_name} (坐标: {int(target_button['center'][0])}, {int(target_button['center'][1])})")
    tap(target_button["center"][0], target_button["center"][1])
    
    if is_click_and_return:
        print("  ⚡ 识别为【点击即领】任务，检测是否弹出授权弹窗...")
        time.sleep(1.5)
        check_and_dismiss_open_dialog()
        time.sleep(2.0)
        return_to_task_list()
    else:
        # 自适应判断是 5 秒还是 15 秒任务
        browse_sec = 7 if "5秒" in target_task_name else 18
        handle_landing_page(browse_seconds=browse_sec)
    time.sleep(1.5)

    return True, "success"

def main():
    print("=" * 55)
    print("  🚀 淘宝双11「淘金币赛车」自适应自动化启动")
    print("  支持普通浏览任务 + 搜索有福利任务自动搜索")
    print("=" * 55)

    max_tasks = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    completed = 0
    no_button_retries = 0

    while completed < max_tasks:
        success, reason = analyze_and_execute_once()
        if success:
            completed += 1
            no_button_retries = 0
            print(f"✅ 已累计完成 {completed} 个任务！\n")
            time.sleep(1.0)
        else:
            if reason in ["no_buttons", "all_blacklisted"]:
                print("🔄 当前屏幕无可用任务，向下滑动刷新列表...")
                swipe_screen(600, 2100, 600, 1100, 600)
                time.sleep(2)
                no_button_retries += 1
                if no_button_retries >= 3:
                    print("\n🎉 连续多次未发现新任务，所有纯浏览/搜索任务已全部刷完！")
                    break
            else:
                time.sleep(2)

    print(f"\n🏁 自动化执行完毕，共执行 {completed} 次任务！请在手机上点击领取能量大礼包。")

if __name__ == "__main__":
    main()
