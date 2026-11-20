# -*- coding: utf-8 -*-
"""推送通知模块：支持 Server 酱 / PushPlus / Telegram / 企业微信 / 钉钉 / Bark。"""

import base64
import hashlib
import hmac
import json
import os
import time
import urllib.parse

import requests


class Notifier:
    def __init__(self) -> None:
        self.channels = []

    @classmethod
    def from_env(cls) -> "Notifier":
        obj = cls()
        for attr, env in (
            ("serverchan", "SERVERCHAN_KEY"),
            ("pushplus", "PUSHPLUS_TOKEN"),
            ("telegram", "TG_BOT_TOKEN"),
            ("wecom", "WECOM_WEBHOOK"),
            ("dingtalk", "DINGTALK_WEBHOOK"),
            ("bark", "BARK_URL"),
        ):
            if os.environ.get(env):
                obj.channels.append((attr, os.environ[env]))
        return obj

    def send(self, title: str, content: str) -> None:
        if not self.channels:
            return
        for name, value in self.channels:
            try:
                getattr(self, f"_send_{name}")(title, content, value)
            except Exception as exc:  # noqa: BLE001
                print(f"[WARN] 推送 {name} 失败: {exc}")

    def _post_json(self, url: str, payload: dict) -> None:
        requests.post(url, json=payload, timeout=15)

    def _send_serverchan(self, title: str, content: str, key: str) -> None:
        url = f"https://sc.ftqq.com/{key}.send"
        self._post_json(url, {"text": title, "desp": content})

    def _send_pushplus(self, title: str, content: str, token: str) -> None:
        self._post_json(
            "https://www.pushplus.plus/send",
            {"token": token, "title": title, "content": content, "template": "markdown"},
        )

    def _send_telegram(self, title: str, content: str, token: str) -> None:
        chat_id = os.environ.get("TG_CHAT_ID", "")
        if not chat_id:
            return
        text = f"*{title}*\n\n{content}"
        self._post_json(
            f"https://api.telegram.org/bot{token}/sendMessage",
            {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        )

    def _send_wecom(self, title: str, content: str, webhook: str) -> None:
        self._post_json(
            webhook,
            {"msgtype": "markdown", "markdown": {"content": f"**{title}**\n\n{content}"}},
        )

    def _send_dingtalk(self, title: str, content: str, webhook: str) -> None:
        secret = os.environ.get("DINGTALK_SECRET", "")
        url = webhook
        if secret:
            timestamp = str(round(time.time() * 1000))
            string_to_sign = f"{timestamp}\n{secret}"
            hmac_code = hmac.new(
                secret.encode("utf-8"), string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
            ).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            url = f"{webhook}&timestamp={timestamp}&sign={sign}"
        self._post_json(url, {"msgtype": "markdown", "markdown": {"title": title, "text": content}})

    def _send_bark(self, title: str, content: str, bark_url: str) -> None:
        base = bark_url.rstrip("/")
        self._post_json(
            f"{base}/{urllib.parse.quote(title)}/{urllib.parse.quote(content[:500])}", {}
        )
