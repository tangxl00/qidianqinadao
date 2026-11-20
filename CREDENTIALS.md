# QIDIAN_CONFIGS 是什么 / 怎么填

`QIDIAN_CONFIGS` 是存到 GitHub Secrets 的一个**账号配置 JSON**。脚本靠它知道"用谁的身份去签到"。值是一个数组，每个元素就是一个起点账号。

## 最小示例

```json
[
  {
    "name": "账号A",
    "sdk_sign": "这里填 SDKSign 的值",
    "qdinfo": "这里填 QDInfo 的值",
    "ywkey": "这里填 ywkey 的值",
    "ywguid": "这里填 ywguid 的值"
  }
]
```

- 只有**一个**账号：写一个对象即可（外面可带可不带中括号）。
- **多个**账号：在数组里放多个对象，脚本会依次签到并分别推送结果。

## 四个字段分别是什么

它们是起点 APP 登录后的**身份凭证**，相当于"你是谁"的证明。脚本把它们拼成请求头去调用签到接口。

| 字段 | 对应凭证 | 放在哪里 | 说明 |
|---|---|---|---|
| `sdk_sign` | `SDKSign` | HTTP 请求头 `Header` | 设备/客户端签名，和登录设备绑定 |
| `qdinfo` | `QDInfo` | `Cookie` | 登录态信息，标识已登录用户 |
| `ywkey` | `ywkey` | `Cookie` | 阅文登录密钥，**通常每月失效需更新** |
| `ywguid` | `ywguid` | `Cookie` | 设备唯一标识（GUID） |

脚本里 `build_headers()` 就是这么用的：

```python
cookie = f"QDInfo={qdinfo}; ywkey={ywkey}; ywguid={ywguid}"
headers = {"SDKSign": sdk_sign, "Cookie": cookie, ...}
```

## 怎么拿到这四个值（抓包）

1. 手机安装抓包工具（Stream / HTTPCanary / Charles / 小黄鸟），配置 HTTPS 证书信任。
2. 打开起点读书 APP，确保已登录。
3. 抓 APP 访问 `h5.if.qidian.com` 的任意请求（比如签到、获取用户信息、getlogininfo）。
4. 在请求详情里找：
   - **请求头（Header）** 里的 `SDKSign` → 填 `sdk_sign`
   - **Cookie** 里的 `QDInfo`、`ywkey`、`ywguid` → 分别填对应字段
5. 复制真实值替换掉示例里的占位符，整段 JSON 粘贴到 GitHub 的 `QIDIAN_CONFIGS` Secret。

> 注意：这些值是你账号的登录凭证，**等同于密码**，别发到公开地方。这也是仓库建议设 Private 的原因。

## 失效了怎么办

- 日志报"登录态失效，请重新抓包更新凭证" → 四个值过期了，重新抓包替换。
- `ywkey` 每月失效是正常现象，重点更新它。
- 想彻底免抓包：用 `qidian.qx.snippet` 的 MITM rewrite 让 APP 登录时自动刷新凭证，再同步到 Secrets。
