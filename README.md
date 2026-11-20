# 起点读书自动签到（GitHub Actions + APP 自动化）
一套完整的起点读书每日任务自动化方案，分两部分：
| 方案 | 覆盖任务 | 运行环境 | 稳定性 |
|---|---|---|---|
| A. GitHub Actions 接口签到 | 每日签到 | 云端定时，无需手机 | 高（纯 HTTP） |
| B. APP 内自动化脚本 | 签到 + 激励视频 + 额外章节卡 + 抽奖 | 手机（Hamibot/Auto.js） | 高（模拟真人点击，APP 自己完成加密） |
> 为什么激励视频/抽奖不直接调接口？
> 这些任务依赖起点 APP 的签名算法与设备指纹。主流开源项目（如 QDjob）的加密模块 enctrypt_qidian.py、Login.py 均明确不公开。因此最可靠的方式是让 APP 自己点，脚本只负责模拟点击。
## 方案 A：GitHub Actions 每日签到
### 1. 获取签到凭证
1. 手机抓包（Stream / HTTPCanary / Charles），对起点 App 抓 HTTPS。
2. 打开「福利中心/签到」页，抓任意发往 `https://h5.if.qidian.com` 的请求。
3. 记录：Header 的 `SDKSign`；Cookie 的 `QDInfo`、`ywkey`（每月更新）、`ywguid`。
### 2. 配置 Secrets
Fork 本仓库 → Settings → Secrets and variables → Actions → 新建：
| Secret | 必填 | 说明 |
|---|---|---|
| `QIDIAN_CONFIGS` | 是 | 账号 JSON 数组，见下 |
| `SERVERCHAN_KEY` / `PUSHPLUS_TOKEN` / `TG_BOT_TOKEN` / `TG_CHAT_ID` / `WECOM_WEBHOOK` / `DINGTALK_WEBHOOK` / `DINGTALK_SECRET` / `BARK_URL` | 否 | 通知渠道 |
`QIDIAN_CONFIGS` 格式：
```json
[
  {"name":"账号A","sdk_sign":"SDKSign值","qdinfo":"QDInfo值","ywkey":"ywkey值","ywguid":"ywguid值"}
]
```
### 3. 启用
Actions 页确认工作流启用，默认每天北京时间 08:00 执行，可手动 Run workflow 测试。
## 方案 B：APP 自动化脚本（激励视频等）
文件：`qidian_app_auto.js`
### 使用步骤
1. 手机安装 `Hamibot`（推荐，支持云端推送/定时）或 `Auto.js`。
2. 开启无障碍服务与悬浮窗权限。
3. 打开起点读书 APP 并登录，停在首页。
4. 把 `qidian_app_auto.js` 内容新建为脚本并运行。
5. 运行期间保持屏幕常亮、不要操作手机（约 2~4 分钟）。
### 覆盖任务
- 每日签到：自动进福利中心点签到，已签到会跳过
- 激励视频任务：10 + 10 + 20 点章节卡（3 条视频）
- 额外章节卡：额外 3 次小视频（10 点）
- 每日抽奖：自动抽取免费次数
### 可调参数（脚本顶部 CONFIG）
| 参数 | 含义 | 建议 |
|---|---|---|
| `videoWatchSec` | 单条视频观看秒数 | 32（起点一般要求 15~30 秒） |
| `stepDelay` | 点击间隔 | 1200ms，越大越像真人 |
| `doExtraVideo` / `doLottery` | 是否执行额外视频/抽奖 | 按需开关 |
### 定时执行（Hamibot）
在 Hamibot 里给该脚本设置「定时任务」，每天固定时间（如 08:30）自动运行；配合 Hamibot 的推送把报告发到微信。
> 提示：起点不同版本 UI 文案略有差异，脚本已兼容「福利/任务中心/我的→福利中心」等多种入口与「看视频/去观看/领取」等按钮文案。若某版本入口特殊，按实际文案在 candidates 数组里补一个关键词即可。
## 目录结构
```
.
├── qidian_sign.py              # 方案A：接口签到主程序
├── notifier.py                 # 通知模块（6 种渠道）
├── qidian_app_auto.js          # 方案B：APP 内自动化（签到+激励视频+抽奖）
├── requirements.txt
├── config.example.json
├── .github/workflows/sign.yml  # 云端定时工作流
└── README.md
```
## 常见问题
- Cookie 失效/未登录：重新抓包更新 `QDInfo`/`ywkey`/`ywguid`。
- ywkey 每月失效：正常现象，每月更新一次。
- APP 脚本点不到按钮：确认无障碍已开、APP 在首页；按实际 UI 文案调整脚本里的关键词。
- 视频看完没奖励：把 `videoWatchSec` 调大；部分账号有风控，手动看一次后再跑。
## 从 QX / qdapi 生态借鉴的设计
调研了 Quantumult X 与 qdapi 的起点实现（如 `pzx521521/qdapi`、`yinghuo666/qdapi`），以下设计已吸收进本仓库：
| 借鉴点 | 来源做法 | 本仓库落地 |
|---|---|---|
| 任务类型化 | QX 把任务拆为 TaskType 1~4：每小时宝箱 / 每日8任务 / 3个视频任务 / 游戏中心10分钟 | APP 脚本新增 `doTreasureBox`、`doGameCenter`，对应 TaskType 1、4 |
| 防风控间隔 | qdapi 每日任务默认 15s 间隔再执行下一个 | 脚本新增 `taskInterval`（默认 15s + 随机抖动），任务间自动等待 |
| 多账号并行 | qdapi 多账号同时处理 | 接口签到方案（方案A）已支持 JSON 多账号依次处理 |
| 版本排错 | “领取失败请升级版本”是 APP 版本号过低 | 见下方常见问题 |
| 部署形态 | 支持 GitHub Actions / Vercel / 云函数 / NAS | 本仓库采用 GitHub Actions，零成本免运维 |
### 关于 SDKSign 的自动生成（进阶方向）
qdapi 项目揭示了 `SDKSign` / `QDInfo` 是 DES3（CBC）加密生成的（key、IV 见其 README 的破解流程）。目前本仓库采取“抓包拿现成凭证”的稳妥做法。若想减少每月抓包，可研究其 DES3 生成算法实现自动续期——但这类凭证与设备指纹绑定，公开算法可能随 APP 升级失效，建议作为长期优化而非必需。
## 常见问题（补充）
- 提示“领取失败，请升级至最新版本领取”：APP 版本号过低，更新起点 APP 后重新抓包 `QDInfo` 与 `SDKSign`。
- 接口签到 `code` 非 0：多为 Cookie 失效或风控，重新抓包凭证；避免短时间内多次手动触发。
- 游戏中心任务耗时约 10 分钟且多账号需不同设备 Cookie（imei 加密未公开），默认关闭，需要时手动打开 `doGameCenter`。


## QX 重写脚本的核心机制（重点借鉴）

仓库新增 `qidian.qx.snippet`，对应 Quantumult X 的 `Yuheng0101/X` QDReader 实现。它的配置只有三段，却揭示了一个比"算 DES3"更聪明的思路：

```text
[mitm]
hostname = h5.if.qidian.com

[rewrite_local]
^https?://h5.if.qidian.com/argus/api/v1/user/getlogininfo url script-response-body qdreader.js

[task_local]
11 2 * * * qdreader.js, tag=起点读书自动签到
```

三段各自的作用：

1. `[mitm]`：对 `h5.if.qidian.com` 开启 HTTPS 中间人解密，这是改写接口的前提（需在 QX 安装 MITM 证书并信任）。
2. `[rewrite_local]`：拦截 APP 请求登录信息接口 `getlogininfo` 的**响应体**，交给脚本处理。脚本在 APP 正常登录时"顺手"拿到最新的 `SDKSign`/`QDInfo` 等凭证并保存 —— 这就是 **Cookie 自动刷新**。
3. `[task_local]`：每天 02:11 定时运行脚本执行签到。

### 为什么这个机制值得借鉴

它绕开了"每月手动抓包"和"自己实现 DES3 算法"两条麻烦路：**让 APP 自己登录，脚本只在旁边把凭证记下来**。凭证永远是 APP 当前有效的，不怕算法升级失效。这正是我们接口签到方案（方案A）里"抓包凭证会过期"问题的优雅解法。

### 与本仓库方案的对照

| 维度 | QX 重写方案 | 本仓库方案A（GitHub Actions） |
|---|---|---|
| Cookie 来源 | MITM 改写 `getlogininfo` 自动刷新 | 手动抓包，每月更新 |
| 运行环境 | 手机 + QX + MITM 证书 | 云端 GitHub Actions，无需手机 |
| 持续运行 | 需 QX 常驻 + 证书信任 | 定时触发即可 |
| 适用场景 | 已在用 QX/Surge、想要凭证自动续期 | 想零运维、云端托管 |

> 组合用法：用 QX 的 rewrite 负责"自动续凭证"，把刷新后的凭证同步到 GitHub Secrets，方案A 就再也不用手动抓包了。这是两套方案互补的最佳实践。

> 说明：`qdreader.js` 本体是 RC4 + Base64 混淆的（解码密钥硬编码在脚本头部），其任务逻辑与上面拆解的 rewrite 钩子一致；本仓库不复制该混淆脚本，仅提供机制说明与等效配置片段。
