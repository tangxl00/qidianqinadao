#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""起点读书自动签到主程序。"""

import json
import os
import sys
import time
from typing import Any, Dict, List

import requests

from notifier import Notifier

SIGN_URL = "https://h5.if.qidian.com/mercury/aggregation/activity/signin"
USER_URL = "https://h5.if.qidian.com/mercury/aggregation/user/getUserInfo"
TIMEOUT = 15
MAX_RETRY = 3


def build_headers(account: Dict[str, Any]) -> Dict[str, str]:
    cookie = (
        f"QDInfo={account.get('qdinfo', '')}; "
        f"ywkey={account.get('ywkey', '')}; "
        f"ywguid={account.get('ywguid', '')}"
    )
    return {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"
        ),
        "SDKSign": account.get("sdk_sign", ""),
        "Cookie": cookie,
        "Content-Type": "application/json; charset=utf-8",
        "Origin": "https://h5.if.qidian.com",
        "Referer": "https://h5.if.qidian.com/",
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
    required = ("sdk_sign", "qdinfo", "ywkey", "ywguid")
    for i, acc in enumerate(data):
        missing = [k for k in required if not acc.get(k)]
        if missing:
            raise ValueError(f"账号[{i}]缺少字段: {', '.join(missing)}")
    return data


def check_login(session: requests.Session, headers: Dict[str, str]) -> bool:
    try:
        resp = session.get(USER_URL, headers=headers, timeout=TIMEOUT)
        payload = resp.json()
        return payload.get("code") == 0
    except Exception:
        return False


def do_sign(session: requests.Session, headers: Dict[str, str]) -> Dict[str, Any]:
    last_error: Dict[str, Any] = {"code": -1, "msg": "未知错误"}
    for attempt in range(1, MAX_RETRY + 1):
        try:
            resp = session.post(SIGN_URL, headers=headers, json={}, timeout=TIMEOUT)
            payload = resp.json()
            code = payload.get("code")
            msg = payload.get("msg") or payload.get("message") or ""
            if code == 0:
                data = payload.get("data") or {}
                return {
                    "code": 0,
                    "msg": "签到成功",
                    "continuous": data.get("signInCount") or data.get("continuousDays") or "",
                    "reward": data.get("rewardDesc") or data.get("award") or "",
                }
            last_error = {"code": code, "msg": msg or f"接口返回 code={code}"}
            if code in (1001, 1002, 1003, 401, 403):
                break
        except Exception as exc:  # noqa: BLE001
            last_error = {"code": -1, "msg": f"请求异常: {exc}"}
        if attempt < MAX_RETRY:
            time.sleep(2 * attempt)
    return last_error


def main() -> int:
    notifier = Notifier.from_env()
    try:
        accounts = load_accounts()
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] 读取账号配置失败: {exc}")
        notifier.send("起点签到配置错误", f"读取账号配置失败: {exc}")
        return 1

    session = requests.Session()
    results: List[str] = []
    failures = 0

    for account in accounts:
        name = account.get("name") or "未命名账号"
        headers = build_headers(account)
        print(f"[{name}] 检查登录状态...")
        if not check_login(session, headers):
            failures += 1
            line = f"- {name}: ❌ 登录态失效，请重新抓包更新凭证"
            print(line)
            results.append(line)
            continue
        print(f"[{name}] 执行签到...")
        result = do_sign(session, headers)
        if result["code"] == 0:
            extra = []
            if result["continuous"]:
                extra.append(f"连续{result['continuous']}天")
            if result["reward"]:
                extra.append(str(result["reward"]))
            suffix = "（" + "，".join(extra) + "）" if extra else ""
            line = f"- {name}: ✅ {result['msg']}{suffix}"
        else:
            failures += 1
            line = f"- {name}: ❌ {result['msg']}（code={result['code']}）"
        print(line)
        results.append(line)

    report = "## 起点读书签到报告\n\n" + "\n".join(results)
    title = f"起点签到完成：{len(accounts) - failures}/{len(accounts)} 成功" if failures else "起点签到全部成功"
    print("\n" + report)
    notifier.send(title, report)
    return 0 if failures == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
