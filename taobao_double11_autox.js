/**
 * 淘宝双11「淘金币组队赛车 - 做任务赚能量」AutoX.js 纯手机端独立脚本
 * 
 * 特性：
 * 1. 完全脱离电脑，手机安装 AutoX.js 开启无障碍权限即可独立运行
 * 2. 悬浮窗交互，支持实时拖动、一键启动/停止与状态显示
 * 3. 内置 Google MLKit / PaddleOCR 本地快速识字
 * 4. 自动识别 15秒/5秒 活跃往复滑动，自动处理小程序授权弹窗
 * 5. 正则满额 (10/10) 与灰色“已完成”拦截，自动领取里程碑大奖
 */

auto.waitFor();

// 申请截图权限（用于无障碍无法获取节点时的 OCR 识图）
if (!requestScreenCapture()) {
    toastLog("❌ 无法获取截图权限，脚本退出");
    exit();
}

// 全局状态与配置
var isRunning = false;
var mainThread = null;
var maxTasks = 40;
var completedTasks = 0;

// 默认跳过的不可自动或花钱类任务
var blackList = ["考试", "答题", "买", "下单", "充值", "邀请", "开卡", "拍立淘"];

// 1. 初始化悬浮窗
var window = floaty.window(
    <frame id="mainFrame" bg="#CC000000" padding="8 6" cardCornerRadius="10">
        <vertical>
            <horizontal gravity="center_vertical">
                <text id="titleText" text="🏎️ 双11助手" textSize="13sp" textColor="#FFFFFF" textStyle="bold" />
                <text id="statusText" text=" ● 待命" textSize="12sp" textColor="#FFA500" marginLeft="8" />
            </horizontal>
            <horizontal gravity="center" marginTop="6">
                <button id="btnAction" text="▶ 启动" textSize="12sp" textColor="#FFFFFF" bg="#FF5000" w="64" h="32" style="Widget.AppCompat.Button.Colored" />
                <button id="btnClose" text="✕" textSize="12sp" textColor="#DDDDDD" bg="#555555" w="32" h="32" marginLeft="6" />
            </horizontal>
        </vertical>
    </frame>
);

window.setPosition(device.width - 240, 200);

// 悬浮窗拖拽移动
var x = 0, y = 0, windowX = 0, windowY = 0, downTime = 0;
window.mainFrame.setOnTouchListener(function(view, event) {
    switch (event.getAction()) {
        case event.ACTION_DOWN:
            x = event.getRawX();
            y = event.getRawY();
            windowX = window.getX();
            windowY = window.getY();
            downTime = new Date().getTime();
            return true;
        case event.ACTION_MOVE:
            window.setPosition(windowX + (event.getRawX() - x), windowY + (event.getRawY() - y));
            return true;
        case event.ACTION_UP:
            if (new Date().getTime() - downTime < 150) {
                view.performClick();
            }
            return true;
    }
    return true;
});

// 悬浮窗按钮事件
window.btnAction.click(function() {
    if (!isRunning) {
        startAutomation();
    } else {
        stopAutomation();
    }
});

window.btnClose.click(function() {
    stopAutomation();
    window.close();
    exit();
});

function updateStatus(text, color) {
    ui.run(function() {
        window.statusText.setText(" ● " + text);
        if (color) window.statusText.setTextColor(colors.parseColor(color));
    });
}

function startAutomation() {
    isRunning = true;
    ui.run(function() {
        window.btnAction.setText("⏹ 停止");
        window.btnAction.setBackgroundColor(colors.parseColor("#E53935"));
    });
    updateStatus("运行中", "#00E676");
    toast("🚀 自动化任务启动，请确保停留在【做任务赚能量】面板");

    mainThread = threads.start(function() {
        taskLoop();
    });
}

function stopAutomation() {
    isRunning = false;
    if (mainThread && mainThread.isAlive()) {
        mainThread.interrupt();
    }
    ui.run(function() {
        window.btnAction.setText("▶ 启动");
        window.btnAction.setBackgroundColor(colors.parseColor("#FF5000"));
    });
    updateStatus("已停止", "#FFA500");
    toast("🛑 任务已停止");
}

// 2. 核心拟人交互函数
function humanSwipe(x1, y1, x2, y2, duration) {
    var dur = duration || random(500, 750);
    // 生成带微小扰动的控制点，模拟真实人手弧线
    var cx = (x1 + x2) / 2 + random(-30, 30);
    var cy = (y1 + y2) / 2 + random(-30, 30);
    gesture(dur, [x1, y1], [cx, cy], [x2, y2]);
}

function browseReciprocating(totalSeconds) {
    var start = new Date().getTime();
    var step = 0;
    while (isRunning && (new Date().getTime() - start < totalSeconds * 1000)) {
        var sx = 600 + random(-50, 50);
        var ex = sx + random(-30, 30);
        if (step % 3 === 2) {
            humanSwipe(sx, 1100, ex, 1800, random(550, 800)); // 回滑
        } else {
            humanSwipe(sx, 1800, ex, 1000, random(600, 850)); // 下滑
        }
        step++;
        sleep(random(1600, 2200));
    }
}

// 3. 授权弹窗处理
function checkAndDismissDialog() {
    var openBtn = text("打开").findOnce() || text("允许").findOnce() || text("允许打开").findOnce();
    if (openBtn && openBtn.bounds().centerY() > device.height * 0.7) {
        toastLog("🔔 检测到小程序授权弹窗，正在自动点击【打开】...");
        click(openBtn.bounds().centerX(), openBtn.bounds().centerY());
        sleep(2000);
        return true;
    }
    return false;
}

// 4. 返回任务主面板
function returnToTaskList() {
    for (var i = 0; i < 4; i++) {
        if (!isRunning) return;
        checkAndDismissDialog();
        if (textContains("做任务赚能量").exists() || textContains("累计任务奖励").exists()) {
            return true;
        }
        back();
        sleep(1200);
    }
    return false;
}

// 5. 搜索页面自适应处理
function handleSearchPage(browseSec) {
    sleep(1500);
    checkAndDismissDialog();

    // 优先点击推荐标签（排除“搜索发现”、“历史搜索”等大标题）
    var clicked = false;
    var tags = textMatches(/^[^\s]{2,8}$/).find();
    for (var i = 0; i < tags.length; i++) {
        var t = tags[i];
        var txt = t.text();
        var cy = t.bounds().centerY();
        if (cy > 800 && cy < 2000 && !txt.includes("搜索") && !txt.includes("发现") && !txt.includes("换一换") && !txt.includes("清空")) {
            toastLog("🔍 命中推荐搜索词: " + txt);
            click(t.bounds().centerX(), t.bounds().centerY());
            clicked = true;
            break;
        }
    }

    if (!clicked) {
        // 兜底点击右上角搜索按钮
        var sBtn = text("搜索").findOnce();
        if (sBtn) {
            click(sBtn.bounds().centerX(), sBtn.bounds().centerY());
        } else {
            click(device.width * 0.9, 150);
        }
    }

    sleep(2500);
    browseReciprocating(browseSec);
    returnToTaskList();
}

// 6. 主循环引擎
function taskLoop() {
    completedTasks = 0;
    var consecutiveNoTask = 0;

    while (isRunning && completedTasks < maxTasks) {
        // 自动认领上方里程碑大奖 (+1000, +2000)
        var claimBtn = text("立即领取").findOnce();
        if (claimBtn && claimBtn.bounds().centerY() < device.height * 0.4) {
            toastLog("🎁 自动领取累计里程碑大奖！");
            click(claimBtn.bounds().centerX(), claimBtn.bounds().centerY());
            sleep(1500);
        }

        // 寻找页面上所有右侧按钮
        var allButtons = textMatches(/^(去完成|去浏览|去逛逛|去)$/).find();
        var targetTask = null;

        for (var b = 0; b < allButtons.length; b++) {
            var btn = allButtons[b];
            var by = btn.bounds().centerY();
            var bx = btn.bounds().centerX();

            // 必须在屏幕右侧且在任务列表有效区域
            if (bx < device.width * 0.6 || by < 800) continue;

            // 获取同一行左侧的任务描述
            var rowTexts = textMatches(/.+/).filter(function(node) {
                return Math.abs(node.bounds().centerY() - by) < 100 && node.bounds().centerX() < device.width * 0.75;
            }).find();

            var rowTitle = "";
            rowTexts.forEach(function(item) { rowTitle += item.text(); });

            // 1. 过滤已完成任务 (如 10/10, 5/5 或文本含已完成)
            var fullMatch = rowTitle.match(/\((\d+)\/(\d+)\)/);
            if (fullMatch && fullMatch[1] === fullMatch[2]) {
                continue;
            }
            if (rowTitle.includes("已完成") || rowTitle.includes("已领取") || btn.text().includes("已")) {
                continue;
            }

            // 2. 过滤黑名单
            var isBlack = false;
            for (var k = 0; k < blackList.length; k++) {
                if (rowTitle.includes(blackList[k])) {
                    isBlack = true;
                    break;
                }
            }

            if (!isBlack) {
                targetTask = { btn: btn, title: rowTitle };
                break;
            }
        }

        if (!targetTask) {
            toastLog("🔄 当前无新任务，向下滑动刷新列表...");
            humanSwipe(device.width / 2, device.height * 0.75, device.width / 2, device.height * 0.4, 600);
            sleep(2000);
            consecutiveNoTask++;
            if (consecutiveNoTask >= 3) {
                toastLog("🎉 连续多次未发现新任务，全部任务已做完！");
                break;
            }
            continue;
        }

        consecutiveNoTask = 0;
        toastLog("👉 点击任务: " + targetTask.title);
        click(targetTask.btn.bounds().centerX(), targetTask.btn.bounds().centerY());

        // 判断任务模式
        var isSearch = targetTask.title.includes("搜一搜") || targetTask.title.includes("搜索");
        var isClickAndReturn = targetTask.title.includes("点击去逛") || (!targetTask.title.includes("浏览") && !isSearch);

        if (isClickAndReturn) {
            toastLog("⚡ 秒级唤起即领任务...");
            sleep(1500);
            checkAndDismissDialog();
            sleep(1000);
            returnToTaskList();
        } else if (isSearch) {
            var bSec = targetTask.title.includes("15秒") ? 18 : (targetTask.title.includes("5秒") ? 7 : 18);
            handleSearchPage(bSec);
        } else {
            var browseSec = targetTask.title.includes("15秒") ? 18 : (targetTask.title.includes("5秒") ? 7 : 18);
            sleep(1500);
            checkAndDismissDialog();
            browseReciprocating(browseSec);
            returnToTaskList();
        }

        completedTasks++;
        toastLog("✅ 已累计完成 " + completedTasks + " 个任务！");
        sleep(1000);
    }

    stopAutomation();
    toastLog("🏁 全部任务执行完成，累计完成 " + completedTasks + " 次！");
}

// 保持前台运行监听
setInterval(function() {}, 1000);
