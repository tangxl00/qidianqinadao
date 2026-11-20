# QIDIAN_CONFIGS 字段说明与重要限制

## 重要：SDKSign 是短时效动态签名

实测发现：同一套抓包凭证，抓取后约 15 分钟内签到正常，之后签到接口返回 \``Result=-3 签名错误`\`。

原因：SDKSign 明文结构为 \``随机串|毫秒时间戳|设备ID|版本|0|请求体MD5|签名`\`（qdapi 项目 3DES 解密样本证实），签名绑定时间戳与请求体，服务器校验时效。因此：

> **把抓取的 SDKSign 存进 GitHub Secrets 长期复用，从根上不可行。**

qdapi 公开的 3DES key 是 2025 年安卓 7.9.384 版本的；当前 iOS 5.9.486 使用不同 key（用旧 key 解当前 SDKSign 是乱码），公开算法无法直接用于实时重签。

## 推荐方案

1. **手机端执行（最稳）**：用仓库的 \`qidian_app_auto.js\` 配 Hamibot 定时任务，APP 自己生成签名，不存在过期问题。
2. **云端执行（保 GitHub）**：需要手机端 QX/Hamibot 在签到前抓取**新鲜** SDKSign/QDH，通过 API 写回 GitHub Secrets 或 Gist，Actions 再读取最新值执行。

## 四项凭证的含义（单次抓包仍有效）

| 字段 | 位置 | 用途 |
|---|---|---|
| \`ywkey\` | Cookie | 登录态密钥，每月失效 |
| \`ywguid\` | Cookie | 设备 GUID |
| \`QDH\` | Cookie | 签到接口签名要素 |
| \`sdk_sign\` | Header SDKSign | 签到接口签名要素，短时效 |

## JSON 格式

\`\`\`json
[
  {
    "name": "账号A",
    "ywkey": "...",
    "ywguid": "...",
    "QDH": "...",
    "sdk_sign": "..."
  }
]
\`\`\`

抓包位置：起点 APP 福利中心页 → 任意 \``h5.if.qidian.com`\` 请求 → Header 取 SDKSign，Cookie 取 ywkey / ywguid / QDH。