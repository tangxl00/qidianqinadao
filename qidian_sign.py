#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""起点读书自动签到主程序（argus 接口版）。

实测确认：
- 登录校验 GET /argus/api/v1/user/getlogininfo 依赖 Cookie 中的 ywkey + ywguid
- 签到 POST /argus/api/v3/checkin/checkin 签名依赖 Header SDKSign + Cookie QDH
- 四项缺一不可；其余抓到的 cookie 项可选带上
"""

import json
import os
import sys
import time
from typing import Any, Dict, List

import requests

from notifier import Notifier

BASE = "https://h5.if.qidian.com"
SIGN_URL = BASE + "/argus/api/v3/checkin/checkin"
LOGIN_URL = BASE + "/argus/api/v1/user/getlogininfo"
TIMEOUT = 15
MAX_RETRY = 3
UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/QDReaderiOS/5.9.486/762")


def build_headers(account: Dict[str, Any]) -> Dict[str, str]:
    cookie = (
        "ywkey=" + str(account["ywkey"]) + "; "
        "ywguid=" + str(account["ywguid"]) + "; "
        "QDH=" + str(account["QDH"])
    )
    for k in ("cmfuToken", "uuid", "QDHeader", "appId", "areaId",
              "qid", "qidth", "mode", "wal", "bar", "qdinfo"):
        if account.get(k):
            name = "QDInfo" if k == "qdinfo" else k
            cookie += "; " + name + "=" + str(account[k])
    return {
        "User-Agent": UA,
        "SDKSign": str(account["sdk_sign"]),
        "Cookie": cookie,
        "Content-Type": "application/json; charset=utf-8",
        "Origin": BASE,
        "Referer": BASE + "/new/welfareCenter/?_viewmode=0&_smode=1",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    }


def load_accounts() -> List[Dict[str, Any]]:
    raw = os.environ.get("QIDIAN_CONFIGS", "")
    if raw:
        data = json.loads(raw)
    else:
        with open("config.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    if isinstance(data, dict):
        data = [data]
    required = ("ywkey", "ywguid", "QDH", "sdk_sign")
    for i, acc in enumerate(data):
        missing = [k for k in required if not acc.get(k)]
        if missing:
            raise ValueError("账号[%d]缺少字段: %s" % (i, ", ".join(missing)))
    return data


def as_int(v: Any) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return -1


def check_login(session: requests.Session, headers: Dict[str, str]) -> bool:
    try:
        resp = session.get(LOGIN_URL, headers=headers, timeout=TIMEOUT)
        uid = (resp.json().get("Data") or {}).get("UserId")
        return str(uid) not in ("0", "None", "", "null")
    except Exception:
        return False


def do_sign(session: requests.Session, headers: Dict[str, str]) -> Dict[str, Any]:
    last: Dict[str, Any] = {"code": -1, "msg": "未知错误"}
    for attempt in range(1, MAX_RETRY + 1):
        try:
            resp = session.post(SIGN_URL, headers=headers, json={}, timeout=TIMEOUT)
            payload = resp.json()
            code = as_int(payload.get("Result", payload.get("result")))
            msg = payload.get("Message") or payload.get("message") or ""
            if code == 0:
                return {"code": 0, "msg": "签到成功"}
            if code == -91002:
                return {"code": 0, "msg": "今日已签到（跳过）"}
            if code == -3:
                return {"code": -3, "msg": "签名错误，请检查 SDKSign / QDH 是否填对"}
            last = {"code": code, "msg": msg or ("接口返回 Result=" + str(code))}
        except Exception as exc:  # noqa: BLE001
            last = {"code": -1, "msg": "请求异常: " + str(exc)}
        if attempt < MAX_RETRY:
            time.sleep(2 * attempt)
    return last


def main() -> int:
    notifier = Notifier.from_env()
    try:
        accounts = load_accounts()
    except Exception as exc:  # noqa: BLE001
        print("[ERROR] 读取账号配置失败: " + str(exc))
        notifier.send("起点签到配置错误", "读取账号配置失败: " + str(exc))
        return 1

    session = requests.Session()
    results: List[str] = []
    failures = 0

    for account in accounts:
        name = account.get("name") or "未命名账号"
        headers = build_headers(account)
        print("[" + name + "] 检查登录状态...")
        if not check_login(session, headers):
            failures += 1
            line = "- " + name + ": 登录态失效，请重新抓包更新凭证"
            print(line)
            results.append(line)
            continue
        print("[" + name + "] 执行签到...")
        result = do_sign(session, headers)
        if result["code"] == 0:
            line = "- " + name + ": " + result["msg"]
        else:
            failures += 1
            line = "- " + name + ": 失败 " + result["msg"] + "（Result=" + str(result["code"]) + "）"
        print(line)
        results.append(line)

    report = "## 起点读书签到报告\n\n" + "\n".join(results)
    title = ("起点签到完成：" + str(len(accounts) - failures) + "/" + str(len(accounts)) + " 成功") if failures else "起点签到全部成功"
    print("\n" + report)
    notifier.send(title, report)
    return 0 if failures == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
