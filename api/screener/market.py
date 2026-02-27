"""Market hours detection and status for IDX."""

from datetime import datetime


def get_market_status() -> dict:
    """
    Get current IDX market status.

    Jam trading IDX:
      Sesi 1: 09:00 - 12:00 (180 menit)
      Sesi 2: 13:30 - 15:50 (140 menit)
      Total : 320 menit
    """
    now = datetime.now()

    # Weekend
    if now.weekday() >= 5:
        return {
            "is_open": False,
            "progress": 0,
            "progress_pct": 0,
            "session": "weekend",
            "timestamp": now.isoformat(),
        }

    current_min = now.hour * 60 + now.minute

    SESI1_START = 9 * 60
    SESI1_END = 12 * 60
    SESI2_START = 13 * 60 + 30
    SESI2_END = 15 * 60 + 50

    SESI1_DUR = SESI1_END - SESI1_START  # 180
    SESI2_DUR = SESI2_END - SESI2_START  # 140
    TOTAL_DUR = SESI1_DUR + SESI2_DUR    # 320

    if current_min < SESI1_START:
        progress = 0
        session = "pre_market"
        is_open = False
    elif current_min <= SESI1_END:
        elapsed = current_min - SESI1_START
        progress = max(elapsed / TOTAL_DUR, 0.05)
        session = "sesi_1"
        is_open = True
    elif current_min < SESI2_START:
        progress = SESI1_DUR / TOTAL_DUR
        session = "istirahat"
        is_open = False
    elif current_min <= SESI2_END:
        elapsed = SESI1_DUR + (current_min - SESI2_START)
        progress = elapsed / TOTAL_DUR
        session = "sesi_2"
        is_open = True
    else:
        progress = 1.0
        session = "closed"
        is_open = False

    return {
        "is_open": is_open,
        "progress": round(progress, 4),
        "progress_pct": round(progress * 100, 1),
        "session": session,
        "timestamp": now.isoformat(),
    }
