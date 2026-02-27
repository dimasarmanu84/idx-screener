"""
Wrapper around existing Python screeners.
Imports functions from screener_idx.py and screener_idx_swing.py,
runs screening, and returns JSON-safe dicts.
"""

import sys
import os
import asyncio
import math
import warnings
from datetime import datetime
from typing import Optional

import numpy as np

warnings.filterwarnings("ignore")

# Add parent directory to path so we can import the existing screener modules
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

# Import BSJP/Intraday screener
import screener_idx as bsjp_mod

# Import Swing screener
import screener_idx_swing as swing_mod


# ============================================================
# STOCK LISTS
# ============================================================

STOCK_GROUPS = {
    # BSJP / Intraday
    "lq45": bsjp_mod.LQ45,
    "idx80": bsjp_mod.LQ45 + bsjp_mod.IDX80_EXTRA,
    "all_idx": sorted(set(bsjp_mod.LQ45 + bsjp_mod.IDX80_EXTRA + bsjp_mod.SMALLCAP_POPULAR)),
    # Small Cap
    "smallcap": bsjp_mod.SMALLCAP_RISKY,
    # All + Small Cap (ARA Hunter default — scan seluas mungkin)
    "all_stocks": sorted(set(bsjp_mod.LQ45 + bsjp_mod.IDX80_EXTRA + bsjp_mod.SMALLCAP_POPULAR + bsjp_mod.SMALLCAP_RISKY)),
    # Swing (Syariah)
    "jii": swing_mod.JII,
    "jii70": swing_mod.JII + swing_mod.JII70_EXTRA,
    "issi": sorted(set(swing_mod.JII + swing_mod.JII70_EXTRA + swing_mod.ISSI_EXTRA)),
}


def _init_all_bursa():
    """Load all IDX tickers into STOCK_GROUPS at startup."""
    try:
        all_tickers = bsjp_mod.fetch_all_idx_tickers()
        if all_tickers and len(all_tickers) > 100:
            STOCK_GROUPS["all_bursa"] = all_tickers
        else:
            # Fallback ke all_stocks
            STOCK_GROUPS["all_bursa"] = STOCK_GROUPS["all_stocks"]
    except Exception:
        STOCK_GROUPS["all_bursa"] = STOCK_GROUPS["all_stocks"]


_init_all_bursa()

SMALLCAP_RISKY_SET = set(bsjp_mod.SMALLCAP_RISKY)

# ============================================================
# FUNDAMENTAL CLASSIFICATION
# ============================================================
# Kategori saham berdasarkan kualitas fundamental:
#   "blue_chip"   — LQ45, likuid, fundamental kuat
#   "mid_cap"     — IDX80 non-LQ45, cukup likuid
#   "fundamental" — Small cap tapi punya bisnis nyata & revenue
#   "spekulatif"  — Gorengan murni, tanpa fundamental kuat

_LQ45_SET = set(bsjp_mod.LQ45)
_IDX80_SET = set(bsjp_mod.IDX80_EXTRA)
_SMALLCAP_POPULAR_SET = set(bsjp_mod.SMALLCAP_POPULAR)


def _get_fundamental_class(ticker: str) -> dict:
    """Klasifikasi fundamental saham berdasarkan kategori list."""
    if ticker in _LQ45_SET:
        return {
            "fund_class": "blue_chip",
            "fund_label": "Blue Chip",
            "fund_color": "blue",
            "fund_desc": "LQ45 — likuid, fundamental kuat",
        }
    if ticker in _IDX80_SET:
        return {
            "fund_class": "mid_cap",
            "fund_label": "Mid Cap",
            "fund_color": "green",
            "fund_desc": "IDX80 — cukup likuid, fundamental baik",
        }
    if ticker in _SMALLCAP_POPULAR_SET:
        return {
            "fund_class": "fundamental",
            "fund_label": "Small Cap Fundamental",
            "fund_color": "yellow",
            "fund_desc": "Small cap dengan bisnis nyata & revenue",
        }
    if ticker in SMALLCAP_RISKY_SET:
        return {
            "fund_class": "spekulatif",
            "fund_label": "Spekulatif",
            "fund_color": "red",
            "fund_desc": "Gorengan — tanpa fundamental kuat, hati-hati",
        }
    # Default: unknown (dari all_bursa atau manual input)
    return {
        "fund_class": "unknown",
        "fund_label": "Belum Dikategorikan",
        "fund_color": "gray",
        "fund_desc": "Belum ada klasifikasi fundamental",
    }


def resolve_stocks(stock_param: str) -> list[str]:
    """Resolve stock group name or comma-separated tickers into list."""
    if stock_param in STOCK_GROUPS:
        return STOCK_GROUPS[stock_param]
    return [s.strip().upper() for s in stock_param.split(",") if s.strip()]


# ============================================================
# JSON SANITIZER
# ============================================================

def _sanitize(obj):
    """Convert numpy types to Python native for JSON serialization."""
    if isinstance(obj, (np.float64, np.float32, np.floating)):
        val = float(obj)
        if math.isnan(val) or math.isinf(val):
            return None
        return round(val, 6)
    if isinstance(obj, (np.int64, np.int32, np.integer)):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return round(obj, 6)
    return obj


# ============================================================
# STATUS HELPERS
# ============================================================

def _status_label(rule_score, max_rules):
    if rule_score == max_rules:
        return "PERFECT"
    elif rule_score >= max_rules - 1:
        return "STRONG"
    elif rule_score >= max_rules - 2:
        return "MODERATE"
    elif rule_score >= max_rules - 3:
        return "WEAK"
    return "FAIL"


def _quality_label(quality, mode="bsjp"):
    """Quality label — different thresholds per mode."""
    if mode == "swing":
        if quality >= 65:
            return "STRONG BUY"
        elif quality >= 45:
            return "BUY"
        elif quality >= 30:
            return "WATCH"
        return "SKIP"
    elif mode in ("bsjp_smallcap", "intraday_smallcap"):
        # Small cap: lower thresholds since quality scores are naturally lower
        if quality >= 70:
            return "STRONG BUY"
        elif quality >= 50:
            return "BUY"
        elif quality >= 35:
            return "WATCH"
        return "SKIP"
    else:
        if quality >= 80:
            return "STRONG BUY"
        elif quality >= 60:
            return "BUY"
        elif quality >= 40:
            return "WATCH"
        return "SKIP"


def _rr_grade(rr1):
    """Grade R:R ratio — used for display and label validation."""
    if rr1 is None or rr1 <= 0:
        return "JANGAN ENTRY", "skip"
    if rr1 >= 2.0:
        return "EXCELLENT", "strong_buy"
    if rr1 >= 1.5:
        return "GOOD", "buy"
    if rr1 >= 1.0:
        return "CUKUP", "watch"
    if rr1 >= 0.5:
        return "BURUK", "skip"
    return "JANGAN ENTRY", "skip"


def _downgrade_label_by_rr(q_label, rr1, mode="bsjp"):
    """
    Downgrade quality label if R:R is too low.
    - R:R >= 1.5 → no downgrade
    - R:R 1.0-1.49 → max BUY (can't be S.BUY)
    - R:R 0.5-0.99 → max WATCH
    - R:R < 0.5 → SKIP
    """
    if rr1 is None or rr1 <= 0:
        return "SKIP"
    if rr1 >= 1.5:
        return q_label  # No downgrade
    if rr1 >= 1.0:
        # Max BUY
        if q_label == "STRONG BUY":
            return "BUY"
        return q_label
    if rr1 >= 0.5:
        # Max WATCH
        if q_label in ("STRONG BUY", "BUY"):
            return "WATCH"
        return q_label
    # R:R < 0.5 → SKIP
    return "SKIP"


# ============================================================
# TIMEFRAME & RISK HELPERS
# ============================================================

def _get_timeframe(mode: str) -> dict:
    """Return timeframe label and hold period per mode."""
    if mode == "intraday":
        return {"label": "Jangka Pendek", "hold": "1 hari", "color": "blue"}
    if mode == "bsjp":
        return {"label": "Jangka Pendek", "hold": "1-3 hari", "color": "blue"}
    # swing
    return {"label": "Jangka Menengah", "hold": "2-8 minggu", "color": "purple"}


def _get_swing_timeframe(stage, atr_pct, dist_ma50_pct=0, is_breakout=False, q_label="SKIP") -> dict:
    """Return dynamic timeframe for swing based on stock conditions."""
    # Stage 4 — Declining
    if stage == 4:
        return {"label": "Hindari", "hold": "Jangan hold", "color": "red"}
    # Stage 3 — Topping
    if stage == 3:
        return {"label": "Segera Jual", "hold": "1-2 minggu", "color": "orange"}
    # Stage 1 — Basing
    if stage == 1:
        if is_breakout:
            return {"label": "Awal Uptrend", "hold": "4-8 minggu", "color": "blue"}
        return {"label": "Tunggu Breakout", "hold": "Belum entry", "color": "gray"}
    # Stage 2 — Advancing (main swing territory)
    if atr_pct > 4.0:
        return {"label": "Swing Cepat", "hold": "1-3 minggu", "color": "blue"}
    if is_breakout and dist_ma50_pct is not None and dist_ma50_pct < 5:
        return {"label": "Awal Breakout", "hold": "4-8 minggu", "color": "purple"}
    if dist_ma50_pct is not None and dist_ma50_pct > 15:
        return {"label": "Extended", "hold": "1-3 minggu", "color": "orange"}
    return {"label": "Jangka Menengah", "hold": "2-6 minggu", "color": "purple"}


def _calc_risk_label(entry_data, pct_change, mode, stage=None, vol_ratio=None):
    """
    Calculate risk level based on multiple factors:
    - %SL distance
    - R:R ratio
    - CHG% today
    - Stage (swing only)
    - Volume ratio
    """
    risk_score = 0

    # Factor 1: %SL distance
    sl_pct = abs(entry_data.get("sl_pct", 0)) if entry_data else 0
    if sl_pct > 10:
        risk_score += 3
    elif sl_pct > 6:
        risk_score += 2
    elif sl_pct > 3:
        risk_score += 1

    # Factor 2: R:R
    rr1 = entry_data.get("rr1", 0) if entry_data else 0
    if rr1 < 1.0:
        risk_score += 3
    elif rr1 < 1.5:
        risk_score += 2
    elif rr1 < 2.0:
        risk_score += 1

    # Factor 3: CHG% today
    chg = abs(pct_change or 0)
    if chg > 5:
        risk_score += 3
    elif chg > 3:
        risk_score += 2
    elif chg > 2:
        risk_score += 1

    # Factor 4: Stage (swing only)
    if mode == "swing" and stage is not None:
        if stage == 1:
            risk_score += 1
        elif stage >= 3:
            risk_score += 3

    # Factor 5: Volume
    vr = vol_ratio if vol_ratio is not None else 1.0
    if vr < 0.5:
        risk_score += 2
    elif vr < 0.8:
        risk_score += 1

    # Determine label
    if risk_score >= 7:
        label, color = "SANGAT HIGH RISK", "red"
    elif risk_score >= 4:
        label, color = "HIGH RISK", "orange"
    else:
        label, color = "MODERATE", "green"

    # Max allocation per mode + risk
    if mode == "intraday":
        alloc = {"SANGAT HIGH RISK": "1%", "HIGH RISK": "2%", "MODERATE": "3%"}
    elif mode == "bsjp":
        alloc = {"SANGAT HIGH RISK": "2%", "HIGH RISK": "3%", "MODERATE": "5%"}
    else:  # swing
        alloc = {"SANGAT HIGH RISK": "2%", "HIGH RISK": "3%", "MODERATE": "5%"}

    return {
        "risk_label": label,
        "risk_color": color,
        "risk_score": risk_score,
        "max_alloc": alloc[label],
    }


# ============================================================
# BSJP / INTRADAY SCREENING
# ============================================================

def _scan_one_bsjp(ticker: str, mode: str, market_progress, smallcap_enabled: bool = False) -> Optional[dict]:
    """Scan a single stock for BSJP/Intraday mode. Returns dict or None on error."""
    import logging
    import yfinance as yf

    df = bsjp_mod.fetch_stock_data(ticker)
    if df is None:
        return None

    try:
        data = bsjp_mod.calculate_indicators(df)
        data["ticker"] = ticker

        # Market cap
        _yf_logger = logging.getLogger("yfinance")
        _prev_level = _yf_logger.level
        _yf_logger.setLevel(logging.CRITICAL)
        try:
            info = yf.Ticker(f"{ticker}.JK").info
            data["market_cap_t"] = info.get("marketCap", 0) / 1e12
        except Exception:
            data["market_cap_t"] = 0
        finally:
            _yf_logger.setLevel(_prev_level)

        data["value_b"] = (data["close"] * data["volume"]) / 1e9

        # Volume normalization
        bsjp_mod.normalize_volume(data, market_progress)

    except Exception:
        return None

    # Determine if this stock is small cap (market cap < 500B or in risky list)
    is_smallcap = smallcap_enabled and (
        data["market_cap_t"] < 0.5 or ticker in SMALLCAP_RISKY_SET  # < 500B
    )

    # === HARD REJECT: ARA/ARB & extreme price moves ===
    chg = data["pct_change"]
    ara_limit = 7 if is_smallcap else 10
    hard_reject_reason = None

    if chg >= ara_limit:
        hard_reject_reason = f"ARA +{chg:.1f}% — JANGAN BELI! Risiko ARB besok"
    elif chg <= -7:
        hard_reject_reason = f"ARB {chg:.1f}% — Sedang crash, jangan tangkap pisau jatuh"
    elif is_smallcap and abs(chg) > 5:
        hard_reject_reason = f"Small cap CHG% {chg:+.1f}% terlalu extreme"

    if hard_reject_reason:
        return _sanitize({
            "ticker": ticker,
            "close": data["close"],
            "pct_change": chg,
            "rule_score": 0,
            "max_rules": 0,
            "quality": 0,
            "status": "REJECT",
            "q_label": "SKIP",
            "rr_grade": None,
            "timeframe": _get_timeframe(mode),
            "risk": {
                "risk_label": "EXTREME",
                "risk_color": "red",
                "risk_score": 100,
                "max_alloc": "0%",
            },
            "fundamental": _get_fundamental_class(ticker),
            "is_smallcap": is_smallcap,
            "hard_reject": hard_reject_reason,
            "rules": [],
            "entry_data": None,
            "indicators": {
                "rsi": data.get("rsi"),
                "macd_line": data.get("macd_line"),
                "macd_signal": data.get("macd_signal"),
                "macd_hist": data.get("macd_hist"),
                "adx": data.get("adx"),
                "stoch_k": data.get("stoch_k"),
                "stoch_d": data.get("stoch_d"),
                "mfi": data.get("mfi"),
                "atr": data.get("atr"),
                "atr_pct": data.get("atr_pct"),
                "ema20": data.get("ema20"),
                "ema50": data.get("ema50"),
                "bb_upper": data.get("bb_upper"),
                "bb_middle": data.get("bb_middle"),
                "bb_lower": data.get("bb_lower"),
                "bb_pctb": data.get("bb_pctb"),
                "bb_bandwidth": data.get("bb_bandwidth"),
            },
            "pivot_points": {
                "pp": data.get("pivot_pp"),
                "r1": data.get("pivot_r1"),
                "r2": data.get("pivot_r2"),
                "s1": data.get("pivot_s1"),
                "s2": data.get("pivot_s2"),
            },
            "volume_info": {
                "volume": data.get("volume"),
                "avg_volume_20d": data.get("avg_volume_20d"),
                "volume_ratio": data.get("volume_ratio"),
                "vol_normalized": data.get("vol_normalized", False),
                "value_b": data.get("value_b", 0),
            },
        })

    # Screen — use small cap rules if applicable
    if is_smallcap:
        rules, rule_score, max_rules = bsjp_mod.screen_smallcap(data, mode)
        quality = bsjp_mod.calc_quality_score_smallcap(data)
        smallcap_mode = f"{mode}_smallcap"
        entry_data = bsjp_mod.calc_entry_sl_tp(data, smallcap_mode)
    elif mode == "bsjp":
        rules, rule_score, max_rules = bsjp_mod.screen_bsjp(data)
        quality = bsjp_mod.calc_quality_score(data, mode)
        entry_data = bsjp_mod.calc_entry_sl_tp(data, mode)
    else:
        rules, rule_score, max_rules = bsjp_mod.screen_intraday(data)
        quality = bsjp_mod.calc_quality_score(data, mode)
        entry_data = bsjp_mod.calc_entry_sl_tp(data, mode)

    # R:R validation — downgrade label if R:R is too low
    rr1 = entry_data.get("rr1") if entry_data else None
    effective_mode = f"{mode}_smallcap" if is_smallcap else mode
    q_label = _quality_label(quality, effective_mode)
    if rr1 is not None:
        q_label = _downgrade_label_by_rr(q_label, rr1, mode)
    rr_grade_label, _ = _rr_grade(rr1)

    # Sanitize rules (rename "pass" key)
    clean_rules = []
    for r in rules:
        clean_rules.append({
            "rule": r["rule"],
            "passed": r["pass"],
            "value": r["value"],
        })

    # Timeframe & Risk — always include entry_data (BUY must have SL/TP)
    timeframe = _get_timeframe(mode)
    risk = _calc_risk_label(
        entry_data,
        data["pct_change"],
        mode,
        vol_ratio=data.get("volume_ratio"),
    )

    # Small cap: force minimum HIGH RISK, max alloc 2%
    if is_smallcap:
        if risk["risk_color"] == "green":  # MODERATE → force HIGH RISK
            risk["risk_label"] = "HIGH RISK"
            risk["risk_color"] = "orange"
            risk["risk_score"] = max(risk["risk_score"], 4)
        risk["max_alloc"] = "2%"

    return _sanitize({
        "ticker": ticker,
        "close": data["close"],
        "pct_change": data["pct_change"],
        "rule_score": rule_score,
        "max_rules": max_rules,
        "quality": quality,
        "status": _status_label(rule_score, max_rules),
        "q_label": q_label,
        "rr_grade": rr_grade_label,
        "timeframe": timeframe,
        "risk": risk,
        "fundamental": _get_fundamental_class(ticker),
        "is_smallcap": is_smallcap,
        "hard_reject": None,
        "rules": clean_rules,
        "entry_data": entry_data,
        "indicators": {
            "rsi": data["rsi"],
            "macd_line": data["macd_line"],
            "macd_signal": data["macd_signal"],
            "macd_hist": data["macd_hist"],
            "adx": data["adx"],
            "stoch_k": data["stoch_k"],
            "stoch_d": data["stoch_d"],
            "mfi": data["mfi"],
            "atr": data["atr"],
            "atr_pct": data["atr_pct"],
            "ema20": data["ema20"],
            "ema50": data["ema50"],
            "bb_upper": data["bb_upper"],
            "bb_middle": data["bb_middle"],
            "bb_lower": data["bb_lower"],
            "bb_pctb": data["bb_pctb"],
            "bb_bandwidth": data["bb_bandwidth"],
        },
        "pivot_points": {
            "pp": data["pivot_pp"],
            "r1": data["pivot_r1"],
            "r2": data["pivot_r2"],
            "s1": data["pivot_s1"],
            "s2": data["pivot_s2"],
        },
        "volume_info": {
            "volume": data["volume"],
            "avg_volume_20d": data["avg_volume_20d"],
            "volume_ratio": data["volume_ratio"],
            "vol_normalized": data.get("vol_normalized", False),
            "value_b": data["value_b"],
        },
    })


async def run_bsjp_intraday(mode: str, stocks: list[str], progress_cb=None, smallcap_enabled: bool = False, result_cb=None) -> dict:
    """
    Run BSJP or Intraday screening on stock list.
    When smallcap_enabled=True, small cap stocks are added to the list
    and small-cap stocks use stricter screening rules.
    """
    from .market import get_market_status

    market_status = get_market_status()
    market_progress = market_status["progress"] if market_status["is_open"] else None

    # If smallcap enabled, merge small cap stocks into list
    if smallcap_enabled:
        all_tickers = sorted(set(stocks + bsjp_mod.SMALLCAP_RISKY))
    else:
        all_tickers = stocks

    results = []
    errors = []

    for i, ticker in enumerate(all_tickers):
        if progress_cb:
            await progress_cb(i + 1, len(all_tickers), ticker)

        result = await asyncio.to_thread(_scan_one_bsjp, ticker, mode, market_progress, smallcap_enabled)

        if result is None:
            errors.append(ticker)
        else:
            results.append(result)
            if result_cb:
                await result_cb(result)

        await asyncio.sleep(0.3)  # Rate limit

    results.sort(key=lambda x: x["quality"], reverse=True)

    strong = [r for r in results if not r.get("hard_reject") and r["quality"] >= 60 and r["rule_score"] >= r["max_rules"] - 2]
    watch = [r for r in results if not r.get("hard_reject") and (40 <= r["quality"] < 60 or (r["quality"] >= 60 and r["rule_score"] < r["max_rules"] - 2))]

    return {
        "mode": mode,
        "timestamp": datetime.now().isoformat(),
        "market_status": market_status,
        "total_scanned": len(results),
        "total_errors": len(errors),
        "errors": errors,
        "results": results,
        "strong": strong,
        "watch": watch,
    }


# ============================================================
# ARA HUNTER
# ============================================================

def _get_ara_limit_pct(prev_close: float) -> float:
    """Get ARA limit percentage based on BEI rules.
    - Harga < 50    → 35%
    - Harga 50-200  → 25%
    - Harga > 200   → 20%
    """
    if prev_close < 50:
        return 0.35
    elif prev_close <= 200:
        return 0.25
    else:
        return 0.20


def _calc_ara_potential_score(data: dict) -> tuple[int, str]:
    """Calculate ARA potential score (0-100) and label.

    Scoring breakdown (max 100):
      1. CHG% momentum        : 0-25 pts
      2. Volume explosion      : 0-20 pts
      3. Buying pressure (MFI) : 0-12 pts
      4. MACD momentum         : 0-8 pts
      5. RSI strength          : 0-8 pts
      6. Distance to ARA       : 0-7 pts
      7. Consecutive up days   : 0-8 pts
      8. Price vs high of day  : -15 to +7 pts (PENALTY if distribution)
      9. Small float / mcap    : 0-5 pts
    """
    score = 0
    chg = data.get("pct_change", 0)
    vol_ratio = data.get("volume_ratio", 0) or 0

    # 1. CHG% momentum (0-25 pts)
    if chg >= 15:
        score += 25
    elif chg >= 10:
        score += 22
    elif chg >= 7:
        score += 18
    elif chg >= 5:
        score += 14
    elif chg >= 3:
        score += 8

    # 2. Volume explosion (0-20 pts)
    if vol_ratio >= 5:
        score += 20
    elif vol_ratio >= 3:
        score += 16
    elif vol_ratio >= 2:
        score += 12
    elif vol_ratio >= 1.5:
        score += 8

    # 3. Buying pressure — MFI (0-12 pts)
    mfi = data.get("mfi") or 50
    if mfi >= 80:
        score += 12
    elif mfi >= 70:
        score += 9
    elif mfi >= 60:
        score += 6

    # 4. MACD bullish momentum (0-8 pts)
    if (data.get("macd_hist") or 0) > 0:
        score += 4
    if (data.get("macd_line") or 0) > (data.get("macd_signal") or 0):
        score += 4

    # 5. RSI strength (0-8 pts)
    rsi = data.get("rsi") or 50
    if 60 <= rsi <= 80:
        score += 8
    elif rsi > 80:
        score += 4  # overbought, slight penalty

    # 6. Distance to ARA — still has room (0-7 pts)
    dist_to_ara = data.get("dist_to_ara_pct", 0)
    if dist_to_ara >= 15:
        score += 7
    elif dist_to_ara >= 10:
        score += 5
    elif dist_to_ara >= 5:
        score += 3

    # 7. Consecutive up days (0-8 pts) — multi-day momentum
    consec_up = data.get("consecutive_up_days", 0)
    if consec_up >= 3:
        score += 8
    elif consec_up >= 2:
        score += 5
    elif consec_up >= 1:
        score += 2

    # 8. Price near high of day — buyer dominan vs distribusi
    #    Bonus jika dekat high, PENALTY jika jauh (morning spike → dump)
    high_pct = data.get("price_vs_high_pct", 0)
    if high_pct >= 98:    # harga = high (very bullish)
        score += 7
    elif high_pct >= 95:
        score += 5
    elif high_pct >= 90:
        score += 3
    elif high_pct < 85:   # DISTRIBUSI: close jauh dari high → seller dominan
        score -= 15
    elif high_pct < 90:
        score -= 8

    # 9. Small float / market cap bonus (0-5 pts) — easier to ARA
    mcap = data.get("market_cap_t", 0)
    if 0 < mcap < 0.5:       # < 500M (micro cap)
        score += 5
    elif mcap < 2:            # < 2T (small cap)
        score += 3
    elif mcap < 5:            # < 5T (mid cap)
        score += 1

    score = max(0, min(score, 100))

    if score >= 70:
        label = "HOT"
    elif score >= 40:
        label = "WARM"
    else:
        label = "WATCH"

    return score, label


def _scan_one_ara(ticker: str, market_progress) -> Optional[dict]:
    """Scan a single stock for ARA potential. Returns dict or None."""
    import logging
    import yfinance as yf

    df = bsjp_mod.fetch_stock_data(ticker)
    if df is None:
        return None

    try:
        data = bsjp_mod.calculate_indicators(df)
        data["ticker"] = ticker

        # Market cap
        _yf_logger = logging.getLogger("yfinance")
        _prev_level = _yf_logger.level
        _yf_logger.setLevel(logging.CRITICAL)
        try:
            info = yf.Ticker(f"{ticker}.JK").info
            data["market_cap_t"] = info.get("marketCap", 0) / 1e12
        except Exception:
            data["market_cap_t"] = 0
        finally:
            _yf_logger.setLevel(_prev_level)

        data["value_b"] = (data["close"] * data["volume"]) / 1e9
        bsjp_mod.normalize_volume(data, market_progress)

        # --- Extra ARA fields from DataFrame ---

        # Consecutive up days: hitung berapa hari berturut close > prev close
        closes = df["Close"]
        consec = 0
        for i in range(len(closes) - 1, 0, -1):
            if closes.iloc[i] > closes.iloc[i - 1]:
                consec += 1
            else:
                break
        data["consecutive_up_days"] = consec

        # Price vs high of day: seberapa dekat harga ke high hari ini (%)
        if data["high"] > 0:
            data["price_vs_high_pct"] = (data["close"] / data["high"]) * 100
        else:
            data["price_vs_high_pct"] = 0

    except Exception:
        return None

    chg = data.get("pct_change", 0)
    vol_ratio = data.get("volume_ratio") or 0

    # Pre-filter: only interested in rising stocks with strong volume
    if chg < 3 or vol_ratio < 1.5:
        return None  # skip — not a candidate

    # Previous close for ARA limit calculation (sesuai aturan BEI)
    prev_close = data["close"] / (1 + chg / 100) if chg != -100 else data["close"]
    data["prev_close"] = prev_close
    ara_pct = _get_ara_limit_pct(prev_close)
    ara_limit_price = prev_close * (1 + ara_pct)
    dist_to_ara_pct = ((ara_limit_price - data["close"]) / data["close"]) * 100 if data["close"] > 0 else 0
    data["dist_to_ara_pct"] = dist_to_ara_pct
    data["ara_pct"] = ara_pct

    # Already at/above ARA — skip
    if dist_to_ara_pct <= 0:
        return None

    # ARA potential score
    ara_score, ara_label = _calc_ara_potential_score(data)

    # Pass ARA limit price to data for SL/TP calculation
    data["ara_limit_price"] = ara_limit_price

    # Calculate entry/SL/TP using ARA momentum mode (wider SL: 3-5%)
    # Small cap juga pakai ara_momentum — saham momentum butuh SL longgar
    is_smallcap = data["market_cap_t"] < 0.5 or ticker in SMALLCAP_RISKY_SET
    entry_data = bsjp_mod.calc_entry_sl_tp(data, "ara_momentum")

    rr1 = entry_data.get("rr1") if entry_data else None
    rr_grade_label, _ = _rr_grade(rr1)

    # === ENTRY RECOMMENDATION ===
    # Hanya rekomendasikan saham yang memenuhi SEMUA kriteria:
    rr_ok = (rr1 or 0) >= 1.5         # R:R minimal 1.5 (worth the risk)
    score_ok = ara_score >= 50          # Score cukup tinggi
    vol_ok = vol_ratio >= 2.0           # Volume confirmed (bukan noise)
    room_ok = dist_to_ara_pct >= 3      # Masih ada ruang ke ARA
    momentum_ok = chg >= 5              # Momentum clear

    # SL depth check — ARA play harus SL ketat, max -5%
    sl_pct = entry_data.get("sl_pct", 0) if entry_data else 0
    sl_ok = abs(sl_pct) <= 5            # SL tidak boleh > 5% (TOSK case: -12%)

    # Distribution check — close harus dekat high (buyer masih dominan)
    price_high_pct = data.get("price_vs_high_pct", 0)
    no_distribution = price_high_pct >= 90  # close >= 90% of high

    entry_checks = sum([rr_ok, score_ok, vol_ok, room_ok, momentum_ok, sl_ok, no_distribution])

    if entry_checks == 7:
        ara_rekom = "ENTRY"
    elif entry_checks >= 5 and score_ok and no_distribution:
        ara_rekom = "WAIT"    # Belum ideal, pantau dulu
    else:
        ara_rekom = "SKIP"

    return _sanitize({
        "ticker": ticker,
        "close": data["close"],
        "pct_change": chg,
        "rule_score": 0,
        "max_rules": 0,
        "quality": ara_score,
        "status": ara_label,
        "q_label": ara_label,
        "rr_grade": rr_grade_label,
        "timeframe": {"label": "Momentum", "hold": "Intraday", "color": "purple"},
        "risk": {
            "risk_label": "EXTREME" if chg >= 10 else "HIGH RISK",
            "risk_color": "red" if chg >= 10 else "orange",
            "risk_score": min(100, int(chg * 5)),
            "max_alloc": "2%",
        },
        "fundamental": _get_fundamental_class(ticker),
        "is_smallcap": is_smallcap,
        "hard_reject": None,
        "rules": [],
        "entry_data": entry_data,
        "ara_rekom": ara_rekom,
        "indicators": {
            "rsi": data.get("rsi"),
            "macd_line": data.get("macd_line"),
            "macd_signal": data.get("macd_signal"),
            "macd_hist": data.get("macd_hist"),
            "adx": data.get("adx"),
            "stoch_k": data.get("stoch_k"),
            "stoch_d": data.get("stoch_d"),
            "mfi": data.get("mfi"),
            "atr": data.get("atr"),
            "atr_pct": data.get("atr_pct"),
            "ema20": data.get("ema20"),
            "ema50": data.get("ema50"),
            "bb_upper": data.get("bb_upper"),
            "bb_middle": data.get("bb_middle"),
            "bb_lower": data.get("bb_lower"),
            "bb_pctb": data.get("bb_pctb"),
            "bb_bandwidth": data.get("bb_bandwidth"),
        },
        "pivot_points": {
            "pp": data.get("pivot_pp"),
            "r1": data.get("pivot_r1"),
            "r2": data.get("pivot_r2"),
            "s1": data.get("pivot_s1"),
            "s2": data.get("pivot_s2"),
        },
        "volume_info": {
            "volume": data.get("volume"),
            "avg_volume_20d": data.get("avg_volume_20d"),
            "volume_ratio": data.get("volume_ratio"),
            "vol_normalized": data.get("vol_normalized", False),
            "value_b": data.get("value_b", 0),
        },
        # ARA-specific fields
        "ara_score": ara_score,
        "ara_label": ara_label,
        "dist_to_ara_pct": round(dist_to_ara_pct, 1),
        "ara_limit": round(ara_limit_price),
        "ara_pct": round(ara_pct * 100),  # 20, 25, or 35
        "prev_close": round(prev_close),
        # New scoring fields
        "consecutive_up_days": data.get("consecutive_up_days", 0),
        "price_vs_high_pct": round(data.get("price_vs_high_pct", 0), 1),
    })


async def run_ara_hunter(stocks: list[str], progress_cb=None, result_cb=None) -> dict:
    """Run ARA Hunter scan — find stocks with ARA potential."""
    from .market import get_market_status

    market_status = get_market_status()
    market_progress = market_status["progress"] if market_status["is_open"] else None

    # Always include small cap stocks (ARA most common in small/mid cap)
    all_tickers = sorted(set(stocks + bsjp_mod.SMALLCAP_RISKY))

    results = []
    errors = []
    scanned = 0

    for i, ticker in enumerate(all_tickers):
        if progress_cb:
            await progress_cb(i + 1, len(all_tickers), ticker)

        result = await asyncio.to_thread(_scan_one_ara, ticker, market_progress)

        scanned += 1
        if result is None:
            # Not an error — just didn't pass the pre-filter (chg < 3% or vol < 1.5x)
            pass
        else:
            results.append(result)
            if result_cb:
                await result_cb(result)

        await asyncio.sleep(0.3)

    # Sort: ENTRY first, then by ARA score descending. Keep top 10.
    rekom_order = {"ENTRY": 0, "WAIT": 1, "SKIP": 2}
    results.sort(key=lambda x: (rekom_order.get(x.get("ara_rekom", "SKIP"), 2), -x.get("ara_score", 0)))
    total_passed = len(results)
    results = results[:10]

    hot = [r for r in results if r.get("ara_label") == "HOT"]
    warm = [r for r in results if r.get("ara_label") == "WARM"]
    entry_count = sum(1 for r in results if r.get("ara_rekom") == "ENTRY")

    return {
        "mode": "ara-hunter",
        "timestamp": datetime.now().isoformat(),
        "market_status": market_status,
        "total_scanned": scanned,
        "total_passed": total_passed,
        "total_errors": 0,
        "errors": [],
        "results": results,
        "strong": hot,
        "watch": warm,
        "entry_count": entry_count,
    }


# ============================================================
# NIGHT SCANNER — Predict next-day top gainer candidates
# ============================================================


def _calc_night_score(data: dict, df) -> tuple[int, str]:
    """Calculate Night Scanner score (0-100) and label.

    Scoring breakdown (max 100):
      1. Volume accumulation     : 0-20 pts
      2. Near breakout setup     : 0-18 pts
      3. Momentum build-up       : 0-15 pts
      4. Price action / accum    : 0-15 pts
      5. Consecutive up days     : 0-12 pts
      6. Trend alignment (EMA)   : 0-10 pts
      7. Buying pressure (MFI)   : 0-10 pts
    """
    score = 0
    chg = data.get("pct_change", 0)
    vol_ratio = data.get("volume_ratio", 0) or 0

    # 1. Volume Accumulation (0-20 pts)
    # 3-day increasing volume trend
    try:
        volumes = df["Volume"].iloc[-3:]
        if len(volumes) >= 3:
            if volumes.iloc[0] < volumes.iloc[1] < volumes.iloc[2]:
                score += 10  # clear 3-day escalation
            elif volumes.iloc[1] < volumes.iloc[2]:
                score += 5   # 2-day increasing
    except Exception:
        pass

    # Stealth accumulation: big volume, small price move
    if vol_ratio >= 2.5 and abs(chg) < 3:
        score += 10
    elif vol_ratio >= 2.0 and abs(chg) < 3:
        score += 7
    elif vol_ratio >= 1.5 and abs(chg) < 3:
        score += 4

    # 2. Near Breakout Setup (0-18 pts)
    dist_to_high_20d = data.get("dist_to_high_20d_pct", 99)
    if dist_to_high_20d <= 1:
        score += 10  # at the 20d high
    elif dist_to_high_20d <= 3:
        score += 7
    elif dist_to_high_20d <= 5:
        score += 4

    bb_bw = data.get("bb_bandwidth") or 20
    if bb_bw < 5:
        score += 8   # very tight squeeze
    elif bb_bw < 8:
        score += 5
    elif bb_bw < 12:
        score += 2

    # 3. Momentum Build-up (0-15 pts)
    macd_hist = data.get("macd_hist") or 0
    macd_line = data.get("macd_line") or 0
    macd_signal = data.get("macd_signal") or 0
    if macd_hist > 0 and macd_line > macd_signal:
        score += 8
    elif macd_hist > 0:
        score += 5
    elif macd_line > macd_signal:
        score += 3

    rsi = data.get("rsi") or 50
    if 55 <= rsi <= 65:
        score += 7  # perfect zone
    elif 50 <= rsi <= 70:
        score += 4
    elif 45 <= rsi < 50:
        score += 2

    # 4. Price Action / Accumulation (0-15 pts)
    if 1 <= chg <= 5 and vol_ratio >= 1.5:
        score += 10  # ideal accumulation: small gain, big volume
    elif 0.5 <= chg <= 5 and vol_ratio >= 1.3:
        score += 6
    elif 0 <= chg <= 5:
        score += 3

    close_vs_high = data.get("price_vs_high_pct", 0)
    if close_vs_high >= 95:
        score += 5
    elif close_vs_high >= 90:
        score += 3
    elif close_vs_high < 80:
        score -= 5  # distribution penalty

    # 5. Consecutive Up Days (0-12 pts)
    consec_up = data.get("consecutive_up_days", 0)
    if consec_up >= 4:
        score += 12
    elif consec_up >= 3:
        score += 9
    elif consec_up >= 2:
        score += 6
    elif consec_up >= 1:
        score += 3

    # 6. Trend Alignment (0-10 pts)
    ema20 = data.get("ema20") or 0
    ema50 = data.get("ema50") or 0
    close = data.get("close", 0)
    if close > ema20 > ema50 > 0:
        score += 10
    elif close > ema20 > 0:
        score += 6
    elif close > ema50 > 0:
        score += 3

    # 7. Buying Pressure / MFI (0-10 pts)
    mfi = data.get("mfi") or 50
    if mfi >= 75:
        score += 10
    elif mfi >= 65:
        score += 7
    elif mfi >= 55:
        score += 4

    score = max(0, min(score, 100))

    if score >= 70:
        label = "PRIME"
    elif score >= 50:
        label = "READY"
    else:
        label = "WATCH"

    return score, label


def _get_night_catalyst(data: dict, df) -> str:
    """Generate concise catalyst text for Night Scanner result."""
    reasons = []
    chg = data.get("pct_change", 0)
    vol_ratio = data.get("volume_ratio", 0) or 0

    if vol_ratio >= 2.0 and abs(chg) < 3:
        reasons.append(f"Stealth accum {vol_ratio:.1f}x")
    elif vol_ratio >= 2.0:
        reasons.append(f"Vol spike {vol_ratio:.1f}x")

    dist = data.get("dist_to_high_20d_pct", 99)
    if dist <= 3:
        reasons.append("Near breakout")

    bb_bw = data.get("bb_bandwidth") or 20
    if bb_bw < 8:
        reasons.append("BB squeeze")

    consec = data.get("consecutive_up_days", 0)
    if consec >= 3:
        reasons.append(f"{consec}d rally")
    elif consec >= 2:
        reasons.append(f"{consec}d up")

    ema20 = data.get("ema20") or 0
    ema50 = data.get("ema50") or 0
    close = data.get("close", 0)
    if close > ema20 > ema50 > 0:
        reasons.append("Trend aligned")

    mfi = data.get("mfi") or 50
    if mfi >= 65:
        reasons.append(f"MFI {mfi:.0f}")

    if data.get("vol_trend_3d"):
        reasons.append("Vol trend 3d")

    return " | ".join(reasons[:3]) if reasons else "Low conviction"


def _scan_one_night(ticker: str) -> Optional[dict]:
    """Scan a single stock for Night Scanner. Returns dict or None."""
    df = bsjp_mod.fetch_stock_data(ticker)
    if df is None or len(df) < 20:
        return None

    try:
        data = bsjp_mod.calculate_indicators(df)
        data["ticker"] = ticker
        data["value_b"] = (data["close"] * data["volume"]) / 1e9

        # Consecutive up days
        closes = df["Close"]
        consec = 0
        for i in range(len(closes) - 1, 0, -1):
            if closes.iloc[i] > closes.iloc[i - 1]:
                consec += 1
            else:
                break
        data["consecutive_up_days"] = consec

        # Price vs high of day
        if data["high"] > 0:
            data["price_vs_high_pct"] = (data["close"] / data["high"]) * 100
        else:
            data["price_vs_high_pct"] = 0

        # 20-day high distance
        high_20d = float(df["High"].iloc[-20:].max())
        data["high_20d"] = high_20d
        if data["close"] > 0:
            data["dist_to_high_20d_pct"] = ((high_20d - data["close"]) / data["close"]) * 100
        else:
            data["dist_to_high_20d_pct"] = 99

        # 3-day volume trend
        try:
            vols = df["Volume"].iloc[-3:]
            data["vol_trend_3d"] = bool(len(vols) >= 3 and vols.iloc[0] < vols.iloc[1] < vols.iloc[2])
        except Exception:
            data["vol_trend_3d"] = False

    except Exception:
        return None

    chg = data.get("pct_change", 0)
    vol_ratio = data.get("volume_ratio") or 0

    # Pre-filter (loose — let scoring differentiate)
    if chg < -3:
        return None  # downtrend
    if chg > 25:
        return None  # already ARA, too risky
    if vol_ratio < 0.5:
        return None  # dead stock

    # Night score
    night_score, night_label = _calc_night_score(data, df)

    # Only return if score >= 30
    if night_score < 30:
        return None

    # Catalyst text
    night_catalyst = _get_night_catalyst(data, df)

    return _sanitize({
        "ticker": ticker,
        "close": data["close"],
        "pct_change": chg,
        "rule_score": 0,
        "max_rules": 0,
        "quality": night_score,
        "status": night_label,
        "q_label": night_label,
        "fundamental": _get_fundamental_class(ticker),
        "is_smallcap": ticker in SMALLCAP_RISKY_SET,
        "hard_reject": None,
        "rules": [],
        "entry_data": None,
        "indicators": {
            "rsi": data.get("rsi"),
            "macd_line": data.get("macd_line"),
            "macd_signal": data.get("macd_signal"),
            "macd_hist": data.get("macd_hist"),
            "adx": data.get("adx"),
            "mfi": data.get("mfi"),
            "ema20": data.get("ema20"),
            "ema50": data.get("ema50"),
            "bb_bandwidth": data.get("bb_bandwidth"),
            "bb_pctb": data.get("bb_pctb"),
        },
        "volume_info": {
            "volume": data.get("volume"),
            "avg_volume_20d": data.get("avg_volume_20d"),
            "volume_ratio": vol_ratio,
            "vol_normalized": False,
            "value_b": data.get("value_b", 0),
        },
        # Night-scanner specific fields
        "night_score": night_score,
        "night_label": night_label,
        "night_catalyst": night_catalyst,
        "consecutive_up_days": consec,
        "price_vs_high_pct": round(data.get("price_vs_high_pct", 0), 1),
        "dist_to_high_20d_pct": round(data.get("dist_to_high_20d_pct", 0), 1),
        "vol_trend_3d": data.get("vol_trend_3d", False),
    })


async def run_night_scanner(stocks: list[str], progress_cb=None, result_cb=None) -> dict:
    """Run Night Scanner — predict next-day top gainer candidates.

    Args:
        result_cb: Optional async callback(stock_result_dict) called immediately
                   when a stock passes the filter, for real-time streaming to frontend.
    """
    from .market import get_market_status

    market_status = get_market_status()

    results = []
    scanned = 0

    for i, ticker in enumerate(stocks):
        if progress_cb:
            await progress_cb(i + 1, len(stocks), ticker)

        result = await asyncio.to_thread(_scan_one_night, ticker)

        scanned += 1
        if result is not None:
            results.append(result)
            # Stream this result immediately to frontend
            if result_cb:
                await result_cb(result)

        await asyncio.sleep(0.3)

    # Sort by night_score descending, keep top 15
    results.sort(key=lambda x: -x.get("night_score", 0))
    total_passed = len(results)
    results = results[:15]

    prime = [r for r in results if r.get("night_label") == "PRIME"]
    ready = [r for r in results if r.get("night_label") == "READY"]

    return {
        "mode": "night-scanner",
        "timestamp": datetime.now().isoformat(),
        "market_status": market_status,
        "total_scanned": scanned,
        "total_passed": total_passed,
        "total_errors": 0,
        "errors": [],
        "results": results,
        "strong": prime,
        "watch": ready,
    }


# ============================================================
# SWING SCREENING
# ============================================================

def _scan_one_swing(ticker: str) -> Optional[dict]:
    """Scan a single stock for Swing mode. Returns dict or None on error."""
    import logging
    import yfinance as yf

    df = swing_mod.fetch_data(ticker)
    if df is None:
        return None

    try:
        d = swing_mod.calc_all(df, ticker)

        # Market cap
        _yf_logger = logging.getLogger("yfinance")
        _prev_level = _yf_logger.level
        _yf_logger.setLevel(logging.CRITICAL)
        try:
            info = yf.Ticker(f"{ticker}.JK").info
            d["mcap_t"] = info.get("marketCap", 0) / 1e12
        except Exception:
            d["mcap_t"] = 0
        finally:
            _yf_logger.setLevel(_prev_level)

    except Exception:
        return None

    # Screen
    rules, rule_score, max_rules = swing_mod.screen_swing(d)
    quality = swing_mod.calc_score(d)
    entry_data = swing_mod.calc_entry_swing(d)

    # R:R validation — downgrade label if R:R is too low
    rr1 = entry_data.get("rr1") if entry_data else None
    q_label = _quality_label(quality, "swing")
    if rr1 is not None:
        q_label = _downgrade_label_by_rr(q_label, rr1, "swing")
    rr_grade_label, _ = _rr_grade(rr1)

    # Bug #10: Stage-based label cap (only buy Stage 2)
    stage = d.get("stage")
    if stage in (3, 4):
        q_label = "SKIP"  # Stage 3 TOPPING / Stage 4 DECLINING = never buy
    elif stage == 1 and q_label in ("STRONG BUY", "BUY"):
        q_label = "WATCH"  # Stage 1 BASING = max WATCH (not yet uptrend)

    # Hard reject CHG% outside swing safe zone (-3% to +4%)
    pct_change = d.get("pct_change", 0)
    if pct_change > 4 or pct_change < -3:
        q_label = "SKIP"  # Outside -3% to +4% = auto SKIP for swing

    # Volatility gate — extreme volatility = auto SKIP for swing
    atr_pct = d.get("atr_pct", 0)
    if atr_pct > 6.0 and q_label in ("STRONG BUY", "BUY"):
        q_label = "WATCH"  # Too volatile for swing — cap at WATCH

    # SL% gate — if SL too deep, downgrade for swing
    sl_pct = abs(entry_data.get("sl_pct", 0)) if entry_data else 0
    if sl_pct > 6.0 and q_label in ("STRONG BUY", "BUY"):
        q_label = "WATCH"  # SL too deep for swing — cap at WATCH

    # Market cap gate — small cap = high false breakout risk
    mcap_t = d.get("mcap_t", 0)
    if mcap_t < 5 and q_label in ("STRONG BUY", "BUY"):
        q_label = "WATCH"  # Too small for reliable swing — cap at WATCH

    # Sanitize rules
    clean_rules = []
    for r in rules:
        clean_rules.append({
            "rule": r["rule"],
            "passed": r["pass"],
            "value": r["value"],
        })

    # Fibonacci levels
    fib_levels = None
    if d.get("fib_levels"):
        fib_levels = {
            "0": d.get("fib_0"),
            "0.236": d.get("fib_0236"),
            "0.382": d.get("fib_0382"),
            "0.5": d.get("fib_05"),
            "0.618": d.get("fib_0618"),
            "0.786": d.get("fib_0786"),
            "1": d.get("fib_1"),
            "swing_high": d.get("fib_swing_high"),
            "swing_low": d.get("fib_swing_low"),
            "support": d.get("fib_support"),
            "support_name": d.get("fib_support_name"),
            "resist": d.get("fib_resist"),
            "resist_name": d.get("fib_resist_name"),
        }

    # Timeframe & Risk
    effective_entry = entry_data if rule_score >= max_rules - 6 else None
    timeframe = _get_swing_timeframe(
        stage=stage,
        atr_pct=atr_pct,
        dist_ma50_pct=d.get("dist_ma50_pct", 0),
        is_breakout=d.get("is_breakout", False),
        q_label=q_label,
    )
    risk = _calc_risk_label(
        effective_entry,
        pct_change,
        "swing",
        stage=stage,
        vol_ratio=d.get("vol_ratio"),
    )

    return _sanitize({
        "ticker": ticker,
        "close": d["close"],
        "pct_change": d["pct_change"],
        "rule_score": rule_score,
        "max_rules": max_rules,
        "quality": quality,
        "status": _status_label(rule_score, max_rules),
        "q_label": q_label,
        "rr_grade": rr_grade_label,
        "timeframe": timeframe,
        "risk": risk,
        "fundamental": _get_fundamental_class(ticker),
        "rules": clean_rules,
        # Swing: show entry_data for 7+ rules (max_rules-6), since swing rules are harder
        "entry_data": effective_entry,
        "stage": d.get("stage"),
        "stage_label": d.get("stage_label", ""),
        "stage_desc": d.get("stage_desc", ""),
        "ma50_slope": d.get("ma50_slope"),
        "dist_ma50_pct": d.get("dist_ma50_pct"),
        "is_breakout": d.get("is_breakout", False),
        "chart_pattern": d.get("chart_pattern", ""),
        "has_pattern": d.get("has_pattern", False),
        "vol_label": d.get("vol_label", ""),
        "hist_vol_20d": d.get("hist_vol_20d", 0),
        "mcap_t": d.get("mcap_t", 0),
        "indicators": {
            "rsi": d["rsi"],
            "macd_line": d["macd_line"],
            "macd_signal": d["macd_signal"],
            "macd_hist": d["macd_hist"],
            "adx": d["adx"],
            "stoch_k": d["stoch_k"],
            "stoch_d": d["stoch_d"],
            "mfi": d["mfi"],
            "atr": d["atr"],
            "atr_pct": d["atr_pct"],
            "ema20": d.get("ema20"),
            "ma50": d.get("ma50"),
            "ma200": d.get("ma200"),
            "bb_upper": d["bb_upper"],
            "bb_middle": d["bb_middle"],
            "bb_lower": d["bb_lower"],
            "bb_pctb": d["bb_pctb"],
        },
        "sr": {
            "s1": d.get("sr_s1"),
            "s2": d.get("sr_s2"),
            "r1": d.get("sr_r1"),
            "r2": d.get("sr_r2"),
        },
        "fib_levels": fib_levels,
        "volume_info": {
            "volume": d["volume"],
            "avg_volume_20d": d.get("avg_vol_20d"),
            "volume_ratio": d.get("vol_ratio"),
            "vol_normalized": False,
            "value_b": d.get("value_b", 0),
        },
    })


async def run_swing(stocks: list[str], progress_cb=None, result_cb=None) -> dict:
    """
    Run Swing screening on stock list.
    Returns JSON-safe dict with all results.
    """
    from .market import get_market_status

    market_status = get_market_status()
    results = []
    errors = []

    for i, ticker in enumerate(stocks):
        if progress_cb:
            await progress_cb(i + 1, len(stocks), ticker)

        result = await asyncio.to_thread(_scan_one_swing, ticker)

        if result is None:
            errors.append(ticker)
        else:
            results.append(result)
            if result_cb:
                await result_cb(result)

        await asyncio.sleep(0.3)

    results.sort(key=lambda x: x["quality"], reverse=True)

    strong = [r for r in results if r["q_label"] in ("STRONG BUY", "BUY")]
    watch = [r for r in results if r["q_label"] == "WATCH"]

    return {
        "mode": "swing",
        "timestamp": datetime.now().isoformat(),
        "market_status": market_status,
        "total_scanned": len(results),
        "total_errors": len(errors),
        "errors": errors,
        "results": results,
        "strong": strong,
        "watch": watch,
    }


# ============================================================
# PORTFOLIO ANALYSIS
# ============================================================

def _generate_signal(avg_price: float, current_price: float, d: dict, entry_data: dict) -> dict:
    """
    Generate portfolio signal based on technical analysis.
    Priority order (first match wins):
    1. CUT LOSS — price < SL
    2. CUT LOSS — Stage 4 Declining
    3. JUAL SEMUA — hit TP2
    4. JUAL SEBAGIAN — hit TP1
    5. JUAL/KURANGI — Stage 3 Topping
    6. SIAP JUAL — below MA50 + floating loss
    7. PERTIMBANGKAN JUAL — RSI >75 + profit >10%
    8. HOLD — default
    """
    pnl_pct = ((current_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0
    stage = d.get("stage", 0)
    rsi = d.get("rsi", 50)
    ma50 = d.get("ma50", 0)
    sl = entry_data.get("sl", 0) if entry_data else 0
    tp1 = entry_data.get("tp1", 0) if entry_data else 0
    tp2 = entry_data.get("tp2", 0) if entry_data else 0

    # Rule 1: CUT LOSS — price below SL
    if sl > 0 and current_price < sl:
        return {
            "code": "CUT_LOSS",
            "label": "CUT LOSS",
            "reason": f"Harga ({current_price:.0f}) di bawah Stop Loss ({sl:.0f}).",
            "severity": 1,
            "action_items": [
                "Jual SEMUA posisi (market order)",
                "Jangan averaging down",
                f"Kerugian saat ini: {pnl_pct:.1f}%",
                "Disiplin SL = selamatkan modal",
            ],
            "color": "red",
        }

    # Rule 2: CUT LOSS — Stage 4 Declining
    if stage == 4:
        return {
            "code": "CUT_LOSS",
            "label": "CUT LOSS",
            "reason": "Stage 4 DECLINING — downtrend dikonfirmasi.",
            "severity": 1,
            "action_items": [
                "Jual SEMUA posisi — Stage 4 = downtrend",
                "Jangan averaging down di Stage 4",
                "Tunggu Stage 1 (base) sebelum masuk lagi",
            ],
            "color": "red",
        }

    # Rule 3: JUAL SEMUA — hit TP2
    if tp2 > 0 and current_price >= tp2:
        return {
            "code": "JUAL_SEMUA",
            "label": "JUAL SEMUA",
            "reason": f"Target TP2 ({tp2:.0f}) tercapai! Take profit semua.",
            "severity": 2,
            "action_items": [
                f"Jual semua — profit {pnl_pct:.1f}%",
                "Kunci profit, jangan serakah",
                "Cari peluang baru di saham lain",
            ],
            "color": "orange",
        }

    # Rule 4: JUAL SEBAGIAN — hit TP1
    if tp1 > 0 and current_price >= tp1:
        items = [
            "Jual 50% posisi untuk kunci profit",
            f"Profit saat ini: {pnl_pct:.1f}%",
        ]
        if tp2 > 0:
            items.append(f"Sisanya hold, target TP2: {tp2:.0f}")
        items.append("Geser SL ke harga beli (BEP) untuk sisa posisi")
        return {
            "code": "JUAL_SEBAGIAN",
            "label": "JUAL SEBAGIAN",
            "reason": f"Target TP1 ({tp1:.0f}) tercapai. Jual 50%, hold sisanya.",
            "severity": 3,
            "action_items": items,
            "color": "orange",
        }

    # Rule 5: JUAL/KURANGI — Stage 3 Topping
    if stage == 3:
        return {
            "code": "JUAL_KURANGI",
            "label": "JUAL / KURANGI",
            "reason": "Stage 3 TOPPING — distribusi mulai terjadi.",
            "severity": 4,
            "action_items": [
                "Kurangi posisi 30-50%",
                "Pasang trailing stop ketat",
                "Jika MA50 mulai turun, jual semua",
            ],
            "color": "yellow",
        }

    # Rule 6: SIAP JUAL — below MA50 + floating loss
    if ma50 > 0 and current_price < ma50 and pnl_pct < 0:
        items = [
            f"Harga ({current_price:.0f}) di bawah MA50 ({ma50:.0f})",
            "Pantau apakah bounce kembali di atas MA50",
        ]
        if sl > 0:
            items.append(f"Batas toleransi: SL di {sl:.0f}")
        return {
            "code": "SIAP_JUAL",
            "label": "SIAP JUAL",
            "reason": f"Di bawah MA50 ({ma50:.0f}) + floating loss {pnl_pct:.1f}%.",
            "severity": 5,
            "action_items": items,
            "color": "yellow",
        }

    # Rule 7: PERTIMBANGKAN JUAL — RSI >75 + profit >10%
    if rsi > 75 and pnl_pct > 10:
        return {
            "code": "PERTIMBANGKAN_JUAL",
            "label": "PERTIMBANGKAN JUAL",
            "reason": f"RSI overbought ({rsi:.0f}) + profit +{pnl_pct:.1f}%.",
            "severity": 6,
            "action_items": [
                f"RSI {rsi:.0f} > 75 (overbought)",
                "Pertimbangkan jual sebagian untuk kunci profit",
                "Atau pasang trailing stop di support terdekat",
            ],
            "color": "yellow",
        }

    # Rule 8: HOLD — default
    hold_items = []
    if stage in (2, 12):
        hold_items.append(f"Trend bagus — {d.get('stage_label', 'Stage 2')}")
    hold_items.append(
        f"P&L: {'+' if pnl_pct >= 0 else ''}{pnl_pct:.1f}%"
    )
    if ma50 > 0:
        above = current_price > ma50
        hold_items.append(
            f"MA50: {ma50:.0f} — harga {'di atas' if above else 'di bawah'}"
        )
    if sl > 0:
        hold_items.append(f"SL: {sl:.0f} | TP1: {tp1:.0f} | TP2: {tp2:.0f}")
    hold_items.append("Tetap disiplin — jual HANYA jika hit TP atau SL")

    reason = "Belum ada sinyal jual. Pantau terus."
    if stage in (2, 12):
        reason = "Stage 2 Advancing — tren masih naik, hold sesuai rencana."

    return {
        "code": "HOLD",
        "label": "HOLD",
        "reason": reason,
        "severity": 7,
        "action_items": hold_items,
        "color": "green",
    }


def _analyze_one_stock(ticker: str, lot: int, avg_price: float) -> Optional[dict]:
    """Analyze a single portfolio stock with full entry data (no rule filtering)."""
    df = swing_mod.fetch_data(ticker)
    if df is None:
        return None

    try:
        d = swing_mod.calc_all(df, ticker)
    except Exception:
        return None

    # Always compute entry data — portfolio needs SL/TP regardless of screening rules
    try:
        entry_data = swing_mod.calc_entry_swing(d)
    except Exception:
        entry_data = None

    current_price = d["close"]
    shares = lot * 100
    invested = avg_price * shares
    market_value = current_price * shares
    pnl_rp = market_value - invested
    pnl_pct = ((current_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0

    signal = _generate_signal(avg_price, current_price, d, entry_data)

    return _sanitize({
        "ticker": ticker,
        "lot": lot,
        "shares": shares,
        "avg_price": avg_price,
        "current_price": current_price,
        "pct_change_today": d.get("pct_change", 0),
        "invested": invested,
        "market_value": market_value,
        "pnl_rp": pnl_rp,
        "pnl_pct": pnl_pct,
        "signal": signal,
        "fundamental": _get_fundamental_class(ticker),
        "stage": d.get("stage"),
        "stage_label": d.get("stage_label"),
        "ma50": d.get("ma50"),
        "dist_ma50_pct": d.get("dist_ma50_pct"),
        "rsi": d.get("rsi"),
        "sl": entry_data.get("sl") if entry_data else None,
        "tp1": entry_data.get("tp1") if entry_data else None,
        "tp2": entry_data.get("tp2") if entry_data else None,
        "entry_data": entry_data,
        "indicators": {
            "rsi": d.get("rsi"),
            "macd_line": d.get("macd_line"),
            "macd_signal": d.get("macd_signal"),
            "macd_hist": d.get("macd_hist"),
            "adx": d.get("adx"),
            "stoch_k": d.get("stoch_k"),
            "stoch_d": d.get("stoch_d"),
            "mfi": d.get("mfi"),
            "atr": d.get("atr"),
            "atr_pct": d.get("atr_pct"),
            "ma50": d.get("ma50"),
            "ma200": d.get("ma200"),
            "ema20": d.get("ema20"),
        },
    })


async def run_portfolio_analysis(holdings: list[dict], progress_cb=None, result_cb=None) -> dict:
    """
    Analyze portfolio holdings.
    holdings: list of {"ticker": str, "lot": int, "avg_price": float}
    """
    results = []
    errors = []

    for i, h in enumerate(holdings):
        ticker = h["ticker"]
        lot = h["lot"]
        avg_price = h["avg_price"]

        if progress_cb:
            await progress_cb(i + 1, len(holdings), ticker)

        result = await asyncio.to_thread(_analyze_one_stock, ticker, lot, avg_price)

        if result is None:
            errors.append(ticker)
        else:
            results.append(result)
            if result_cb:
                await result_cb(result)

        await asyncio.sleep(0.3)

    # Sort by signal severity (CUT LOSS first, HOLD last)
    results.sort(key=lambda x: x["signal"]["severity"])

    # Summary
    total_invested = sum(r["invested"] for r in results)
    total_market_value = sum(r["market_value"] for r in results)
    total_pnl_rp = total_market_value - total_invested
    total_pnl_pct = (total_pnl_rp / total_invested * 100) if total_invested > 0 else 0

    signal_counts = {}
    cut_loss_tickers = []
    for r in results:
        code = r["signal"]["code"]
        signal_counts[code] = signal_counts.get(code, 0) + 1
        if code == "CUT_LOSS":
            cut_loss_tickers.append(r["ticker"])

    return {
        "timestamp": datetime.now().isoformat(),
        "total_analyzed": len(results),
        "total_errors": len(errors),
        "errors": errors,
        "holdings": results,
        "summary": {
            "total_invested": round(total_invested),
            "total_market_value": round(total_market_value),
            "total_pnl_rp": round(total_pnl_rp),
            "total_pnl_pct": round(total_pnl_pct, 2),
            "signal_counts": signal_counts,
            "cut_loss_tickers": cut_loss_tickers,
        },
    }
