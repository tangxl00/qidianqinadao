# 部署到 GitHub 并定时自动运行

本指南把仓库部署到 GitHub，用 GitHub Actions 每天定时执行签到（方案A，云端免手机）。全程约 5 分钟。

## 一、准备 GitHub 账号与凭证

1. 注册/登录 [GitHub](https://github.com)。
2. 按 README 的「方案 A → 获取签到凭证」抓包拿到 4 个值：`SDKSign`、`QDInfo`、`ywkey`、`ywguid`。

## 二、创建仓库并上传代码

### 方式 1：网页上传（最简单，无需装 git）

1. 打开 https://github.com/new
2. 填写 Repository name，例如 `qidian-auto-sign`；选择 **Private**（强烈建议，虽然凭证在 Secrets 里，但私有更安全）。
3. 点击 **Create repository**。
4. 在新仓库页面点 **Add file → Upload files**，把本文件夹里的这些文件全部拖进去：
   - `qidian_sign.py`、`notifier.py`、`requirements.txt`
   - `.github/workflows/sign.yml`（注意保留目录结构；网页上传时可直接在输入框写路径 `.github/workflows/sign.yml`）
   - 可选：`config.example.json`、`qidian_app_auto.js`、`qidian.qx.snippet`
   - **不要**上传 `config.json`（填了真实凭证的本地文件）。
5. 拉到底部点 **Commit changes**。

### 方式 2：命令行推送（装了 git 的机器）

```bash
# 在本仓库目录执行
git init
git add .
git commit -m "init: qidian auto sign"
git branch -M main
git remote add origin https://github.com/你的用户名/qidian-auto-sign.git
git push -u origin main
```

> `.gitignore` 已忽略 `config.json`，真实凭证不会被提交。若仓库里没有 `.gitignore`，新建一份写入：`config.json`、`__pycache__/`、`.env`。

## 三、配置 Secrets（凭证只放这里）

进入仓库 **Settings → Secrets and variables → Actions → New repository secret**，逐个添加：

**必填：**

| Name | Value |
|---|---|
| `QIDIAN_CONFIGS` | 见下方 JSON |

`QIDIAN_CONFIGS` 的值（多账号就写多个对象）：

```json
[
  {"name":"账号A","sdk_sign":"你的SDKSign","qdinfo":"你的QDInfo","ywkey":"你的ywkey","ywguid":"你的ywguid"}
]
```

**选填（通知渠道，想接收签到结果就配其中一个）：**

| Name | 说明 |
|---|---|
| `SERVERCHAN_KEY` | Server 酱 SendKey |
| `PUSHPLUS_TOKEN` | PushPlus token |
| `TG_BOT_TOKEN` / `TG_CHAT_ID` | Telegram 机器人 token 与聊天 ID |
| `WECOM_WEBHOOK` | 企业微信群机器人 Webhook |
| `DINGTALK_WEBHOOK` / `DINGTALK_SECRET` | 钉钉机器人 Webhook 与签名密钥 |
| `BARK_URL` | Bark 推送地址 |

## 四、启用并测试定时运行

1. 点顶部 **Actions** 标签。首次进入若提示启用工作流，点 **I understand my workflows, go ahead and enable them**。
2. 左侧选 **起点读书自动签到**，右侧点 **Run workflow → Run workflow**，手动跑一次。
3. 点击这次运行，点 **sign** 任务，实时看日志。出现「签到成功」或「全部成功」即配置正确。
4. 若失败，看日志提示：`登录态失效`就重新抓包更新凭证；`code` 非 0 多为风控或 Cookie 过期。

## 五、定时规则说明

工作流里的 cron：

```yaml
on:
  schedule:
    - cron: '0 0 * * *'   # UTC 00:00 = 北京时间 08:00
```

- GitHub 的 cron 一律用 **UTC 时间**，北京时间 = UTC + 8。
- 常用换算：北京 08:00 → `0 0 * * *`；北京 12:00 → `0 4 * * *`；北京 07:17 → `17 23 * * *`。
- GitHub 在整点高峰期会延迟甚至跳过任务，建议错峰（如 `17 23 * * *`）更稳。
- 工作流已加 `concurrency`（防止并发重复执行）和 `timeout-minutes: 15`（超时自动终止）。

## 六、关于定时任务的"自动休眠"限制

GitHub 会在仓库 **60 天无活动**后暂停定时任务。保持活跃的方法：随便改点文件、或手动 Run workflow 一次即可恢复。这是 GitHub 官方行为，不是脚本问题。

## 七、让凭证自动续期（进阶，配合 QX）

方案A 的凭证（尤其 `ywkey`）每月要更新。想彻底免维护：

1. 按 `qidian.qx.snippet` 在 Quantumult X 配置 MITM + rewrite，让 APP 登录时自动刷新凭证。
2. 写个小脚本把刷新后的 4 个值通过 GitHub API 更新到 Secrets（或用 `gh secret set QIDIAN_CONFIGS`）。
3. 这样方案A 就永远用着最新凭证，无需手动抓包。

> 提示：GitHub Actions 免费额度对公开仓库无限、私有仓库每月 2000 分钟，每天一次签到远远够用。
