"""Telegram Bot notification for portfolio alerts."""

import os
import httpx

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

EMOJI_MAP = {
    "CUT_LOSS": "\u274c",           # ❌
    "JUAL_SEMUA": "\U0001f534",     # 🔴
    "JUAL_SEBAGIAN": "\U0001f7e0",  # 🟠
    "JUAL_KURANGI": "\U0001f7e0",   # 🟠
    "SIAP_JUAL": "\U0001f7e1",      # 🟡
    "PERTIMBANGKAN_JUAL": "\U0001f7e1",  # 🟡
}


def is_configured() -> bool:
    return bool(BOT_TOKEN) and bool(CHAT_ID)


def _format_message(alerts: list[dict]) -> str:
    lines = ["\U0001f6a8 *Portfolio Alert*\n"]
    for a in alerts:
        emoji = EMOJI_MAP.get(a.get("signalCode", ""), "\u26a0\ufe0f")
        ticker = a.get("ticker", "???")
        label = a.get("signalLabel", "")
        pnl = a.get("pnlPct", 0)
        reason = a.get("reason", "")
        pnl_str = f"+{pnl:.1f}%" if pnl >= 0 else f"{pnl:.1f}%"
        lines.append(f"{emoji} *{ticker}* — {label}")
        lines.append(f"P&L: {pnl_str} | {reason}\n")
    return "\n".join(lines)


async def send_alert(alerts: list[dict]) -> tuple[bool, str]:
    if not is_configured():
        return False, "Telegram not configured"
    if not alerts:
        return False, "No alerts to send"

    text = _format_message(alerts)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "Markdown",
            })
            data = resp.json()
            if data.get("ok"):
                return True, "Sent"
            return False, data.get("description", "Unknown error")
    except Exception as e:
        return False, str(e)
