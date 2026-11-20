# QIDIAN_CONFIGS 是什么 / 怎么填

\`QIDIAN_CONFIGS\` 是存到 GitHub Secrets 的账号配置 JSON。脚本靠它知道"用谁的身份去签到"。值是一个数组，每个元素一个起点账号。

## 最小示例（实测确认）

\`\`\`json
[
  {
    "name": "账号A",
    "ywkey": "抓包得到的 ywkey 值",
    "ywguid": "抓包得到的 ywguid 值"
  }
]
\`\`\`

- 单账号：写一个对象即可（可带可不带中括号）。
- 多账号：数组里放多个对象，脚本依次签到并分别推送。

## 必需字段（只有两项）

实测结论：签到接口 \`POST /argus/api/v3/checkin/checkin\` 的登录态**只依赖 Cookie 中的 ywkey + ywguid**。

| 字段 | 对应 Cookie | 说明 |
|---|---|---|
| \`ywkey\` | ywkey | 阅文登录密钥，**每月失效需更新** |
| \`ywguid\` | ywguid | 设备唯一标识（GUID） |

验证过程：去掉 SDKSign / borgus / ibex / tstamp / helios / Referer / User-Agent / cmfuToken / QDH / QDHeader 后，只要 ywkey+ywguid 在，\`getlogininfo\` 仍返回正确 UserId；去掉 ywkey 或 ywguid 任意一个 → UserId=0（未登录）。

## 可选字段（抓到就填，更贴近真实请求）

| 字段 | 对应 Cookie/Header |
|---|---|
| \`cmfuToken\` | Cookie 中的 cmfuToken |
| \`QDHeader\` | Cookie 中的 QDHeader |
| \`uuid\` / \`QDH\` / \`appId\` / \`areaId\` / \`qid\` / \`qidth\` | Cookie 中的同名项 |
| \`qdinfo\` | Cookie 中的 QDInfo（旧字段，已非必需） |

## 怎么拿到 ywkey / ywguid

1. 手机安装抓包工具（Stream / HTTPCanary / Charles / 小黄鸟），配置 HTTPS 证书信任。
2. 打开起点读书 APP，确保已登录，进入「福利中心」。
3. 抓任意发往 \`h5.if.qidian.com\` 的请求（如 \`/argus/api/v1/user/getlogininfo\`）。
4. 在请求头 Cookie 里找到 \`ywkey=xxx\` 和 \`ywguid=xxx\`，填入 JSON。
5. 整段 JSON 粘贴到 GitHub 的 \`QIDIAN_CONFIGS\` Secret。

> 这些值等同于账号密码，别发公开地方，建议仓库设 Private。

## 失效了怎么办

- 日志报"登录态失效" → ywkey / ywguid 过期，重新抓包替换。
- \`ywkey\` 每月失效属正常，重点更新它。
- 想彻底免抓包：用 \`qidian.qx.snippet\` 的 MITM rewrite 让 APP 登录时自动刷新凭证，再同步到 Secrets。