# 起点读书自动签到（GitHub Actions + APP 自动化）

| 方案 | 覆盖任务 | 运行环境 | 稳定性 |
|---|---|---|---|
| A. GitHub Actions 接口签到 | 每日签到 | 云端定时，无需手机 | 高（纯 HTTP） |
| B. APP 内自动化脚本 | 签到 + 激励视频 + 额外章节卡 + 抽奖 | 手机（Hamibot/Auto.js） | 高（模拟真人点击，APP 自己完成加密） |

> 为什么激励视频/抽奖不直接调接口？
> 这些任务依赖起点 APP 的签名算法与设备指纹，主流开源项目的加密模块均未公开。因此最可靠的方式是让 APP 自己点。

## 方案 A：GitHub Actions 每日签到

### 1. 获取签到凭证（实测已确认）

抓包起点 APP 访问 \``h5.if.qidian.com/new/welfareCenter/`\` 的请求，
真正必需的是 **Cookie 里的两项**：

| 字段 | 位置 | 说明 |
|---|---|---|
| \`ywkey\` | Cookie | 阅文登录密钥，**每月失效需更新** |
| \`ywguid\` | Cookie | 设备唯一标识（GUID） |

实测结论：去掉 SDKSign / borgus / ibex / tstamp / helios / Referer / UA / cmfuToken / QDH / QDHeader 后，
只要 \`ywkey\` + \`ywguid\` 在，登录接口仍返回正确 UserId；任缺其一则 UserId=0（未登录）。
所以最小凭证就是这两项；其余项抓到也建议一并填（更贴近真实请求）。

### 2. 真实签到接口

仓库最初用的 \`/mercury/aggregation/activity/signin\` 已失效（全部 404），现已更正为实测可用的 argus 接口：

- 签到：\`POST https://h5.if.qidian.com/argus/api/v3/checkin/checkin\`（无参数，返回 Result=0 成功，Result=-91002 表示今日已签）
- 登录校验：\`GET /argus/api/v1/user/getlogininfo\`
- 本周签到信息：\`GET /argus/api/v3/checkin/getcurrentweekcheckininfo\`

### 3. 配置 Secrets

Fork 本仓库 → Settings → Secrets and variables → Actions → 新建：

| Secret | 必填 | 说明 |
|---|---|---|
| \`QIDIAN_CONFIGS\` | 是 | 账号 JSON 数组，见下 |
| \`SERVERCHAN_KEY\` / \`PUSHPLUS_TOKEN\` / \`TG_BOT_TOKEN\` / \`TG_CHAT_ID\` / \`WECOM_WEBHOOK\` / \`DINGTALK_WEBHOOK\` / \`DINGTALK_SECRET\` / \`BARK_URL\` | 否 | 通知渠道 |

\`QIDIAN_CONFIGS\` 最小格式：

\`\`\`json
[
  {"name":"账号A","ywkey":"ywkey值","ywguid":"ywguid值"}
]
\`\`\`

多账号就在数组里放多个对象。抓到的 cmfuToken / QDHeader 等可选字段也可一并写进对象。

### 4. 启用

Actions 页确认工作流启用，默认每天北京时间 08:00 执行，可手动 Run workflow 测试。

## 方案 B：APP 自动化脚本（激励视频等）

文件：\`qidian_app_auto.js\`

1. 手机安装 \`Hamibot\`（推荐）或 \`Auto.js\`，开启无障碍与悬浮窗权限。
2. 打开起点读书 APP 并登录，停在首页。
3. 新建脚本粘贴 \`qidian_app_auto.js\` 并运行，期间保持屏幕常亮（约 2~4 分钟）。

覆盖任务：每日签到、激励视频（10+10+20 章节卡）、额外 3 次章节卡、每日抽奖、每小时宝箱、游戏中心。

可调参数在脚本顶部 CONFIG：\`videoWatchSec\`（默认 32）、\`stepDelay\`（默认 1200ms）、\`taskInterval\`（默认 15s 防风控）、\`doExtraVideo\` / \`doLottery\` / \`doTreasureBox\` / \`doGameCenter\`。

## 目录结构

\`\`\`
.
├── qidian_sign.py              # 方案A：接口签到主程序（argus 版）
├── notifier.py                 # 通知模块（6 种渠道）
├── qidian_app_auto.js          # 方案B：APP 内自动化
├── requirements.txt
├── config.example.json
├── CREDENTIALS.md              # 凭证字段说明
├── qidian.qx.snippet           # QX 自动刷新凭证配置
├── DEPLOY.md                   # GitHub 部署指南
├── .github/workflows/sign.yml  # 云端定时工作流
└── README.md
\`\`\`

## 常见问题

- **提示登录态失效**：\`ywkey\` / \`ywguid\` 过期，重新抓包替换；\`ywkey\` 每月失效属正常。
- **Result=-91002**：今日已签到，脚本按成功处理（幂等）。
- **APP 脚本点不到按钮**：确认无障碍已开、APP 在首页；按实际 UI 文案调整脚本里的关键词。
- **视频看完没奖励**：把 \`videoWatchSec\` 调大；部分账号有风控，手动看一次后再跑。
- **领取失败请升级版本**：APP 版本过低，更新起点 APP。


## 重要更新：云端接口签到的时效限制

实测确认 SDKSign 是**短时效动态签名**（明文含毫秒时间戳 + 请求体 MD5），抓取后约 15 分钟即失效。因此方案 A（GitHub Actions + 静态 Secrets）**只适合刚抓完包立即手动验证，不能长期无人值守运行**——超过时效签到会返回 \`Result=-3 签名错误\`。

要长期自动运行，二选一：

1. **方案 B（推荐）**：手机装 Hamibot，用 \`qidian_app_auto.js\` 定时执行。APP 自己生成签名，最稳定，还覆盖激励视频/抽奖。
2. **云端 + 自动续签**：手机端 QX rewrite 或脚本在每次签到前抓取新鲜 SDKSign/QDH，写回 GitHub Secrets，方案 A 再读取最新值执行。需要手机常在线。

qdapi 公开的 3DES key（2025 安卓 7.9.384）与当前 iOS 5.9.486 使用的 key 不同，其算法无法直接用于实时重签。

## QX 自动刷新凭证（进阶）

\`qidian.qx.snippet\` 借鉴 Quantumult X 的实现，思路是让 APP 正常登录时用 MITM rewrite 顺手记录最新凭证，免去每月手动抓包：

\`\`\`text
[mitm]
hostname = h5.if.qidian.com

[rewrite_local]
^https?://h5.if.qidian.com/argus/api/v1/user/getlogininfo url script-response-body qdreader.js

[task_local]
11 2 * * * qdreader.js, tag=起点读书自动签到
\`\`\`

组合用法：用 QX rewrite 自动续凭证 → 同步到 GitHub Secrets → 方案A 云端定时签到，互补免维护。
> \`qdreader.js\` 本体为 RC4+Base64 混淆脚本，本仓库不复制，仅提供机制说明与等效配置。