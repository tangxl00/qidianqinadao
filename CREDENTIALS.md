# QIDIAN_CONFIGS 必填四项（实测确认）

签到流程实测结论：

| 环节 | 接口 | 依赖凭证 |
|---|---|---|
| 登录校验 | \``GET /argus/api/v1/user/getlogininfo`\` | Cookie: \`ywkey\` + \`ywguid\` |
| 签到 | \``POST /argus/api/v3/checkin/checkin`\` | Header: \`SDKSign\` + Cookie: \`QDH\` |

四项缺一不可，否则签到返回 \`Result=-3 签名错误\`。

## JSON 格式

\`\`\`json
[
  {
    "name": "账号A",
    "ywkey": "抓包 Cookie 里的 ywkey",
    "ywguid": "抓包 Cookie 里的 ywguid",
    "QDH": "抓包 Cookie 里的 QDH",
    "sdk_sign": "抓包 Header 里的 SDKSign"
  }
]
\`\`\`

- 单账号：一个对象即可（可带可不带中括号）。
- 多账号：数组放多个对象，依次签到并分别推送。

## 抓包位置（以你这次的完整请求头为例）

- \`ywkey\` → Request Header \`Cookie\` 中的 \`ywkey=ywNxozbxeoRn\`
- \`ywguid\` → Cookie 中的 \`ywguid=120050683056\`
- \`QDH\` → Cookie 中的 \`QDH=uXYCI5kDTisura...\`（整段，含结尾 \`=\`）
- \`sdk_sign\` → 请求头 \`SDKSign: EgPU/EXgrtN/...\`

## 可选字段

抓到也建议填，更贴近真实请求：\`cmfuToken\`、\`uuid\`、\`QDHeader\`、\`appId\`、\`areaId\`、\`qid\`、\`qidth\`。

## 失效处理

- \`登录态失效\` → ywkey / ywguid 过期，重新抓包。
- \`签名错误(Result=-3)\` → SDKSign / QDH 填错或过期，重新抓完整请求头。
- \`ywkey\` 每月失效属正常，到期重抓这四项即可。