/**
 * 起点读书 APP 自动化任务（Hamibot / Auto.js 通用）
 * 覆盖：每日签到 + 激励视频 + 额外章节卡 + 每日抽奖 + 每小时宝箱 + 游戏中心
 * 原理：模拟真人在 APP 内点击，签名/加密由 APP 自身完成，不依赖外部逆向接口。
 *
 * 借鉴说明：任务分类参考 QX / qdapi 生态的 TaskType 1~4 设计；
 * 任务间加入随机间隔，降低风控概率（qdapi 每日任务默认 15s 间隔）。
 *
 * 使用：
 *   1. 手机安装 Hamibot（或 Auto.js）并开启无障碍服务
 *   2. 打开起点读书 APP，登录账号，停在首页
 *   3. 在 Hamibot 中新建脚本，粘贴本文件内容，运行
 *   4. 建议关闭锁屏、保持屏幕常亮；运行期间不要操作手机
 */

// ============ 可配置项 ============
const CONFIG = {
  stepDelay: 1200,          // 各任务之间的基础等待（毫秒），越大越像真人
  taskInterval: 15000,      // 任务之间的间隔（qdapi 用 15s 防风控），默认 15s
  videoWatchSec: 32,        // 激励视频观看时长（秒），起点通常要求 15~30 秒
  continueOnError: true,    // 单个任务失败后是否继续下一个
  doLottery: true,          // 是否执行抽奖
  doExtraVideo: true,       // 是否执行额外章节卡（额外 3 次小视频）
  doTreasureBox: true,      // 是否领取每小时宝箱（借鉴 QX TaskType 1）
  doGameCenter: false,      // 游戏中心 10 分钟任务（耗时长、易风控，默认关闭，借鉴 TaskType 4）
};

// ============ 工具函数 ============
function log(msg) { console.log("[起点助手] " + msg); }
function sleep(ms) { return java.lang.Thread.sleep(ms); }
function rand(min, max) { return min + Math.random() * (max - min); }
function taskGap() { sleep(CONFIG.taskInterval + rand(0, 1500)); }

function waitForText(text, timeoutMs) {
  timeoutMs = timeoutMs || 10000;
  let end = java.lang.System.currentTimeMillis() + timeoutMs;
  while (java.lang.System.currentTimeMillis() < end) {
    let node = textContains(text).findOne(300);
    if (node) return node;
    sleep(300);
  }
  return null;
}

function clickText(text, timeoutMs) {
  let node = waitForText(text, timeoutMs);
  if (!node) { log("未找到按钮: " + text); return false; }
  try {
    let b = node.bounds();
    click(b.centerX(), b.centerY());
    log("点击: " + text);
    sleep(CONFIG.stepDelay);
    return true;
  } catch (e) { log("点击失败: " + text + " -> " + e); return false; }
}

function backToHome(maxBack) {
  maxBack = maxBack || 8;
  for (let i = 0; i < maxBack; i++) {
    if (textContains("书架").findOne(500) || textContains("书城").findOne(500)) break;
    back();
    sleep(500);
  }
}

function openWelfareCenter() {
  backToHome();
  if (clickText("福利", 5000)) return true;
  if (clickText("任务中心", 5000)) return true;
  if (clickText("我的", 4000)) {
    sleep(800);
    if (clickText("福利中心", 4000)) return true;
    if (clickText("每日任务", 4000)) return true;
  }
  return false;
}

// ============ 任务实现 ============

function taskSignIn() {
  log("=== 每日签到 ===");
  if (!openWelfareCenter()) { log("进入福利中心失败，跳过签到"); return false; }
  if (textContains("已签到").findOne(1500)) { log("今日已签到"); return true; }
  let ok = clickText("签到", 4000) || clickText("立即签到", 4000);
  if (ok) {
    sleep(1000);
    clickText("知道了", 1500) || clickText("确定", 1500) || clickText("关闭", 1500);
    log("签到完成");
  }
  return ok;
}

function watchOneVideo(rewardLabel) {
  log("观看激励视频: " + rewardLabel);
  let btn = null;
  let candidates = ["看视频", "去观看", "观看视频", "领取", "免费领取"];
  for (let label of candidates) {
    btn = textContains(label).findOne(1200);
    if (btn) break;
  }
  if (!btn) { log("未找到视频入口按钮"); return false; }
  try { let b = btn.bounds(); click(b.centerX(), b.centerY()); }
  catch (e) { log("点击视频入口失败: " + e); return false; }

  sleep(2000);
  let waited = 0;
  while (waited < CONFIG.videoWatchSec) {
    sleep(1000); waited++;
    if (textContains("领取奖励").findOne(200) || textContains("返回").findOne(200)) break;
  }
  clickText("领取奖励", 2000) || clickText("关闭", 1500) || clickText("返回", 1500);
  sleep(CONFIG.stepDelay);
  log("视频任务结束: " + rewardLabel);
  return true;
}

function taskIncentiveVideos() {
  log("=== 激励视频任务 ===");
  if (!openWelfareCenter()) return false;
  let rewards = ["10点章节卡", "10点章节卡", "20点章节卡"];
  let done = 0;
  for (let r of rewards) {
    if (watchOneVideo(r)) done++;
    taskGap();
  }
  log("激励视频完成 " + done + "/" + rewards.length);
  return done > 0;
}

function taskExtraVideos() {
  log("=== 额外章节卡任务 ===");
  if (!openWelfareCenter()) return false;
  let done = 0;
  for (let i = 0; i < 3; i++) {
    if (watchOneVideo("额外章节卡")) done++;
    taskGap();
  }
  log("额外视频完成 " + done + "/3");
  return done > 0;
}

function taskLottery() {
  log("=== 每日抽奖 ===");
  if (!openWelfareCenter()) return false;
  let ok = clickText("抽奖", 4000) || clickText("每日抽奖", 4000) || clickText("免费抽", 4000);
  if (!ok) { log("未找到抽奖入口"); return false; }
  sleep(1200);
  let draw = clickText("立即抽取", 3000) || clickText("抽一次", 3000) || clickText("免费抽", 3000);
  if (draw) {
    sleep(1500);
    clickText("知道了", 1500) || clickText("确定", 1500) || clickText("关闭", 1500);
    log("抽奖完成");
  }
  return draw;
}

/** 每小时宝箱：借鉴 qdapi TaskType 1 */
function taskTreasureBox() {
  log("=== 每小时宝箱 ===");
  if (!openWelfareCenter()) return false;
  let ok = clickText("宝箱", 4000) || clickText("领宝箱", 4000) || clickText("免费宝箱", 4000);
  if (!ok) { log("当前无宝箱可领"); return false; }
  sleep(1200);
  clickText("领取", 3000) || clickText("开启", 3000) || clickText("立即领取", 3000);
  sleep(1000);
  clickText("知道了", 1500) || clickText("确定", 1500) || clickText("关闭", 1500);
  log("宝箱已领取");
  return true;
}

/** 游戏中心任务：借鉴 qdapi TaskType 4（每 30s 心跳一次，累计约 20 次 / 10 分钟） */
function taskGameCenter() {
  log("=== 游戏中心任务（约 10 分钟）===");
  if (!openWelfareCenter()) return false;
  let ok = clickText("游戏中心", 4000) || clickText("去游戏", 4000) || clickText("玩游戏", 4000);
  if (!ok) { log("未找到游戏中心入口"); return false; }
  sleep(2000);
  for (let i = 0; i < 20; i++) {
    if (i % 3 === 0) { try { click(rand(300, 600), rand(600, 900)); } catch (e) {} }
    sleep(30000);
    log("游戏中心心跳 " + (i + 1) + "/20");
  }
  back();
  log("游戏中心任务结束");
  return true;
}

// ============ 主流程 ============
function runTask(name, fn) {
  try { return fn(); }
  catch (e) {
    log(name + " 异常: " + e);
    if (!CONFIG.continueOnError) throw e;
    return false;
  }
}

function main() {
  log("启动起点读书自动化任务");
  if (typeof launchApp === "function") {
    try { launchApp("起点读书"); } catch (e) { log("启动APP失败，请手动打开: " + e); }
  }
  sleep(2500);

  let summary = [];
  summary.push("签到: " + (runTask("签到", taskSignIn) ? "OK" : "FAIL"));
  if (CONFIG.doTreasureBox) { taskGap(); summary.push("宝箱: " + (runTask("宝箱", taskTreasureBox) ? "OK" : "FAIL")); }
  taskGap(); summary.push("激励视频: " + (runTask("激励视频", taskIncentiveVideos) ? "OK" : "FAIL"));
  if (CONFIG.doExtraVideo) { taskGap(); summary.push("额外视频: " + (runTask("额外视频", taskExtraVideos) ? "OK" : "FAIL")); }
  if (CONFIG.doLottery) { taskGap(); summary.push("抽奖: " + (runTask("抽奖", taskLottery) ? "OK" : "FAIL")); }
  if (CONFIG.doGameCenter) { taskGap(); summary.push("游戏中心: " + (runTask("游戏中心", taskGameCenter) ? "OK" : "FAIL")); }

  let report = "起点APP任务完成 -> " + summary.join(" | ");
  log(report);
  return report;
}

main();
