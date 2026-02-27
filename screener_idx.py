#!/usr/bin/env python3
"""
=================================================================
IDX STOCK SCREENER — BSJP & INTRADAY
=================================================================
Auto-screening saham Indonesia berdasarkan formula ATR + Pivot +
RSI + MACD + Volume + Bollinger + ADX + MFI + Stochastic

Cara pakai:
1. pip install yfinance pandas ta-lib  (atau: pip install yfinance pandas ta)
2. python screener_idx.py
3. Pilih mode: BSJP atau INTRADAY
4. Tunggu hasil screening + Entry/SL/TP otomatis

Data: Yahoo Finance (gratis, delay 15 menit)
Disclaimer: Untuk edukasi. Bukan ajakan beli/jual.
=================================================================
"""

import json
import os
import sys
import time
import warnings
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")

# ============================================================
# INSTALL CHECK
# ============================================================
try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
except ImportError:
    print("=" * 60)
    print("INSTALL DULU:")
    print("pip install yfinance pandas numpy")
    print("=" * 60)
    sys.exit(1)

# Coba import ta (technical analysis library)
try:
    import ta
    USE_TA_LIB = True
except ImportError:
    USE_TA_LIB = False
    print("⚠️  Library 'ta' tidak ditemukan. Menggunakan kalkulasi manual.")
    print("   Untuk hasil lebih akurat: pip install ta\n")


# ============================================================
# DAFTAR SAHAM IDX
# ============================================================

# LQ45 + IDX80 + Saham Populer (suffix .JK untuk Yahoo Finance)
LQ45 = [
    "ACES", "ADRO", "AKRA", "AMMN", "AMRT", "ANTM", "ASII", "BBCA",
    "BBNI", "BBRI", "BBTN", "BMRI", "BRPT", "BUKA", "CPIN", "EMTK",
    "ERAA", "ESSA", "EXCL", "GGRM", "GOTO", "HRUM", "ICBP", "INCO",
    "INDF", "INKP", "ISAT", "ITMG", "KLBF", "MAPI", "MBMA", "MDKA",
    "MEDC", "MIKA", "PGAS", "PGEO", "PTBA", "SMGR", "SMDR", "TBIG",
    "TINS", "TLKM", "TOWR", "TPIA", "UNTR", "UNVR",
]

IDX80_EXTRA = [
    "ARTO", "BFIN", "BIRD", "BRIS", "BSDE", "CTRA", "DSNG", "FILM",
    "GJTL", "HEAL", "HMSP", "INTP", "JPFA", "JSMR", "LPPF", "MNCN",
    "PNBN", "PWON", "SCMA", "SIDO", "SRTG", "TAPG", "TKIM", "WIKA",
]

SMALLCAP_POPULAR = [
    "AGII", "ALDO", "ASSA", "BEST", "CAMP", "DSSA", "GTRA", "KBLI",
    "KIJA", "RALS", "SKBM", "TALF", "TRIS", "ULTJ", "WTON", "ZATA",
    # Tier A — ex-SMALLCAP_RISKY, fundamental bagus, bisnis nyata
    "MEGA", "ROTI", "DRMA", "CASA", "DOID",
    # Tier B — bisnis nyata, ada revenue, tapi ada risiko
    "KEJU", "KRAS", "FREN", "PSAB",
]

ALL_STOCKS = sorted(set(LQ45 + IDX80_EXTRA + SMALLCAP_POPULAR))

# Saham Small Cap Spekulatif — high volatility, volume spike driven
# HANYA saham yang memang murni spekulatif / tanpa fundamental kuat
SMALLCAP_RISKY = [
    # Tambang/Energi — spekulatif, utang besar, kinerja tidak konsisten
    "BUMI", "ENRG", "DEWA", "FIRE", "BOSS", "ZINC", "SMMT",
    # Properti — shell company / tidak aktif
    "NIRO", "MYRX", "KOTA", "LAND", "POSA",
    # Teknologi/Digital — belum profitable
    "BELI", "EDGE", "WIFI",
    # Industri
    "SLIS",
    # Consumer — bermasalah / micro cap
    "AISA", "KOPI", "FOLK",
    # Finansial/Holding — spekulatif
    "BWPT", "POOL", "ARMY", "DEAL",
    # Lainnya - pure gorengan, micro cap
    "BEKS", "BOLA", "GOLL", "GTBO", "LUCK", "RATU", "RIMO", "TOPS",
    "PPRE", "HILL", "VISI", "ZATA", "LAPD", "INET",
    # Top gainer / ARA frequent — pump & dump
    "ASHA", "AIMS", "TFAS", "IKAN", "YELO", "HDIT", "DIVA", "TOSK",
]


# ============================================================
# DAFTAR SEMUA EMITEN IDX (dari file lokal)
# ============================================================

_ALL_IDX_TICKERS_CACHE: list[str] = []
_ALL_IDX_DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "idx_all_tickers.json")


def fetch_all_idx_tickers() -> list[str]:
    """
    Load semua ticker saham yang listing di BEI (IDX) dari file lokal.
    File: data/idx_all_tickers.json (934 emiten)
    Fallback: gabungan semua list hardcoded jika file tidak ada.
    """
    global _ALL_IDX_TICKERS_CACHE

    if _ALL_IDX_TICKERS_CACHE:
        return _ALL_IDX_TICKERS_CACHE

    # Baca dari file lokal
    if os.path.exists(_ALL_IDX_DATA_FILE):
        try:
            with open(_ALL_IDX_DATA_FILE, "r") as f:
                data = json.load(f)
            _ALL_IDX_TICKERS_CACHE = data.get("tickers", [])
            if _ALL_IDX_TICKERS_CACHE:
                return _ALL_IDX_TICKERS_CACHE
        except Exception:
            pass

    # Fallback: gabungan semua list hardcoded
    _ALL_IDX_TICKERS_CACHE = sorted(set(LQ45 + IDX80_EXTRA + SMALLCAP_POPULAR + SMALLCAP_RISKY))
    return _ALL_IDX_TICKERS_CACHE


# ============================================================
# TECHNICAL INDICATOR CALCULATIONS (tanpa library ta)
# ============================================================

def calc_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calc_sma(series, period):
    return series.rolling(window=period).mean()

def calc_rsi(close, period=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calc_macd(close, fast=12, slow=26, signal=9):
    ema_fast = calc_ema(close, fast)
    ema_slow = calc_ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calc_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calc_atr(high, low, close, period=14):
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def calc_bollinger(close, period=20, std_dev=2):
    middle = calc_sma(close, period)
    std = close.rolling(window=period).std()
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)
    return upper, middle, lower

def calc_adx(high, low, close, period=14):
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)
    atr = calc_atr(high, low, close, period)
    plus_di = 100 * calc_ema(plus_dm, period) / atr
    minus_di = 100 * calc_ema(minus_dm, period) / atr
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = calc_ema(dx, period)
    return adx

def calc_stochastic(high, low, close, k_period=14, d_period=3):
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(window=d_period).mean()
    return k, d

def calc_mfi(high, low, close, volume, period=14):
    typical_price = (high + low + close) / 3
    raw_money_flow = typical_price * volume
    delta = typical_price.diff()
    pos_flow = raw_money_flow.where(delta > 0, 0.0)
    neg_flow = raw_money_flow.where(delta < 0, 0.0)
    pos_sum = pos_flow.rolling(window=period).sum()
    neg_sum = neg_flow.rolling(window=period).sum()
    mfi = 100 - (100 / (1 + pos_sum / neg_sum))
    return mfi


# ============================================================
# MARKET HOURS & VOLUME NORMALIZATION
# ============================================================

def get_market_progress():
    """
    Hitung berapa persen hari trading IDX sudah berjalan.

    Jam trading IDX:
      Sesi 1: 09:00 - 12:00 (180 menit)
      Sesi 2: 13:30 - 15:50 (140 menit)
      Total : 320 menit

    Returns:
      float: 0.0-1.0 (fraksi hari trading yang sudah lewat)
      None jika di luar jam trading (market tutup)
    """
    now = datetime.now()

    # Weekend = market tutup
    if now.weekday() >= 5:
        return None

    current_min = now.hour * 60 + now.minute

    SESI1_START = 9 * 60        # 09:00
    SESI1_END = 12 * 60         # 12:00
    SESI2_START = 13 * 60 + 30  # 13:30
    SESI2_END = 15 * 60 + 50    # 15:50

    SESI1_DUR = SESI1_END - SESI1_START  # 180 min
    SESI2_DUR = SESI2_END - SESI2_START  # 140 min
    TOTAL_DUR = SESI1_DUR + SESI2_DUR    # 320 min

    if current_min < SESI1_START:
        return None  # Belum buka
    elif current_min <= SESI1_END:
        elapsed = current_min - SESI1_START
        return max(elapsed / TOTAL_DUR, 0.05)  # Min 5% agar tidak divide by ~0
    elif current_min < SESI2_START:
        # Istirahat siang — sesi 1 sudah selesai
        return SESI1_DUR / TOTAL_DUR
    elif current_min <= SESI2_END:
        elapsed = SESI1_DUR + (current_min - SESI2_START)
        return elapsed / TOTAL_DUR
    else:
        return None  # Market sudah tutup


def normalize_volume(data, market_progress):
    """
    Normalisasi volume saat market masih buka.

    Volume hari ini masih parsial, jadi kita scale up berdasarkan
    berapa persen hari trading yang sudah lewat.

    Contoh: Jam 11:00 (progress=37.5%), volume 5jt → estimasi full day = 13.3jt
    """
    if market_progress is None or market_progress >= 0.95:
        # Market tutup atau hampir tutup — volume sudah cukup akurat
        data["vol_normalized"] = False
        return data

    raw_volume = data["volume"]
    estimated_volume = raw_volume / market_progress

    data["volume_raw"] = raw_volume
    data["volume"] = estimated_volume
    data["vol_normalized"] = True
    data["vol_progress"] = market_progress

    # Recalculate volume-dependent fields
    data["volume_ratio"] = estimated_volume / data["avg_volume_20d"] if data["avg_volume_20d"] > 0 else 0
    data["value_b"] = (data["close"] * estimated_volume) / 1e9

    return data


# ============================================================
# DATA FETCHER
# ============================================================

def fetch_stock_data(ticker, period="3mo"):
    """Fetch data saham dari Yahoo Finance"""
    try:
        stock = yf.Ticker(f"{ticker}.JK")
        df = stock.history(period=period)
        if df.empty or len(df) < 30:
            return None
        return df
    except Exception:
        return None


def calculate_indicators(df):
    """Hitung semua indikator teknikal"""
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    if USE_TA_LIB:
        # Pakai library ta
        ema20 = ta.trend.ema_indicator(close, window=20)
        ema50 = ta.trend.ema_indicator(close, window=50)
        rsi = ta.momentum.rsi(close, window=14)
        macd_obj = ta.trend.MACD(close)
        macd_line = macd_obj.macd()
        macd_signal = macd_obj.macd_signal()
        macd_hist = macd_obj.macd_diff()
        atr = ta.volatility.average_true_range(high, low, close, window=14)
        bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
        bb_upper = bb.bollinger_hband()
        bb_lower = bb.bollinger_lband()
        bb_middle = bb.bollinger_mavg()
        adx = ta.trend.adx(high, low, close, window=14)
        stoch = ta.momentum.StochasticOscillator(high, low, close)
        stoch_k = stoch.stoch()
        stoch_d = stoch.stoch_signal()
        mfi = ta.volume.money_flow_index(high, low, close, volume, window=14)
    else:
        # Kalkulasi manual
        ema20 = calc_ema(close, 20)
        ema50 = calc_ema(close, 50)
        rsi = calc_rsi(close)
        macd_line, macd_signal, macd_hist = calc_macd(close)
        atr = calc_atr(high, low, close)
        bb_upper, bb_middle, bb_lower = calc_bollinger(close)
        adx = calc_adx(high, low, close)
        stoch_k, stoch_d = calc_stochastic(high, low, close)
        mfi = calc_mfi(high, low, close, volume)

    # Ambil nilai terakhir
    last = len(df) - 1
    prev = last - 1

    result = {
        "close": close.iloc[last],
        "open": df["Open"].iloc[last],
        "high": high.iloc[last],
        "low": low.iloc[last],
        "prev_close": close.iloc[prev],
        "prev_high": high.iloc[prev],
        "prev_low": low.iloc[prev],
        "volume": volume.iloc[last],
        "avg_volume_20d": volume.iloc[-20:].mean() if len(df) >= 20 else volume.mean(),
        "ema20": ema20.iloc[last],
        "ema50": ema50.iloc[last],
        "rsi": rsi.iloc[last],
        "macd_line": macd_line.iloc[last],
        "macd_signal": macd_signal.iloc[last],
        "macd_hist": macd_hist.iloc[last],
        "atr": atr.iloc[last],
        "bb_upper": bb_upper.iloc[last],
        "bb_middle": bb_middle.iloc[last],
        "bb_lower": bb_lower.iloc[last],
        "adx": adx.iloc[last],
        "stoch_k": stoch_k.iloc[last],
        "stoch_d": stoch_d.iloc[last],
        "mfi": mfi.iloc[last],
    }

    # Calculated fields
    result["pct_change"] = ((result["close"] - result["prev_close"]) / result["prev_close"]) * 100
    result["volume_ratio"] = result["volume"] / result["avg_volume_20d"] if result["avg_volume_20d"] > 0 else 0
    result["bb_pctb"] = (result["close"] - result["bb_lower"]) / (result["bb_upper"] - result["bb_lower"]) if (result["bb_upper"] - result["bb_lower"]) > 0 else 0.5
    result["bb_bandwidth"] = ((result["bb_upper"] - result["bb_lower"]) / result["bb_middle"]) * 100 if result["bb_middle"] > 0 else 0
    result["atr_pct"] = (result["atr"] / result["close"]) * 100 if result["close"] > 0 else 0

    # Pivot Points (dari data hari sebelumnya)
    pp = (result["prev_high"] + result["prev_low"] + result["prev_close"]) / 3
    result["pivot_pp"] = pp
    result["pivot_r1"] = (2 * pp) - result["prev_low"]
    result["pivot_r2"] = pp + (result["prev_high"] - result["prev_low"])
    result["pivot_r3"] = (2 * pp) + (result["prev_high"] - (2 * result["prev_low"]))
    result["pivot_s1"] = (2 * pp) - result["prev_high"]
    result["pivot_s2"] = pp - (result["prev_high"] - result["prev_low"])
    result["pivot_s3"] = (2 * pp) - ((2 * result["prev_high"]) - result["prev_low"])

    # Swing Lows — untuk confluence SL (struktur harga)
    result["swing_low_3d"] = low.iloc[-3:].min() if len(df) >= 3 else low.iloc[last]
    result["swing_low_5d"] = low.iloc[-5:].min() if len(df) >= 5 else low.iloc[-3:].min()
    result["day_low"] = low.iloc[last]  # Low hari ini

    # Body ratio: abs(close - open) / (high - low) — anti doji palsu
    candle_range = result["high"] - result["low"]
    result["body_ratio"] = abs(result["close"] - result["open"]) / candle_range if candle_range > 0 else 0

    # Market cap & value akan diisi di main() setelah ticker diketahui
    result["market_cap_t"] = 0
    result["value_b"] = (result["close"] * result["volume"]) / 1e9

    return result


# ============================================================
# SCREENING ENGINE
# ============================================================

def screen_bsjp(data):
    """Screening rules untuk BSJP — 16 rules"""
    results = []
    score = 0
    max_score = 16

    est = "~est" if data.get("vol_normalized") else ""
    rules = [
        # Layer 1: Anti Small Cap
        ("Market Cap > 1T", data["market_cap_t"] > 1, f"{data['market_cap_t']:.1f}T"),
        ("Avg Vol 20D > 5jt", data["avg_volume_20d"] > 5_000_000, f"{data['avg_volume_20d']/1e6:.1f}jt"),
        ("Value > 5M", data["value_b"] > 5, f"{data['value_b']:.1f}M{est}"),

        # Layer 2: Momentum
        ("Close > EMA20", data["close"] > data["ema20"], f"{data['close']:.0f} vs {data['ema20']:.0f}"),
        ("EMA20 > EMA50", data["ema20"] > data["ema50"], f"{data['ema20']:.0f} vs {data['ema50']:.0f}"),
        ("MACD Hist > 0", data["macd_hist"] > 0, f"{data['macd_hist']:.2f}"),
        ("ADX > 20", data["adx"] > 20, f"{data['adx']:.1f}"),

        # Layer 3: Anti-Jebakan
        ("RSI 40-70", 40 <= data["rsi"] <= 70, f"{data['rsi']:.1f}"),
        ("Stoch %K < 80", data["stoch_k"] < 80, f"{data['stoch_k']:.1f}"),
        ("BB %B 0.3-0.75", 0.3 <= data["bb_pctb"] <= 0.75, f"{data['bb_pctb']:.2f}"),
        ("Change -3% to +3%", -3 <= data["pct_change"] <= 3, f"{data['pct_change']:+.1f}%"),
        ("MFI > 40", data["mfi"] > 40, f"{data['mfi']:.1f}"),

        # Layer 4: Volatilitas
        ("BB Bandwidth > 5%", data["bb_bandwidth"] > 5, f"{data['bb_bandwidth']:.1f}%"),
        ("ATR% 3-7%", 3 <= data["atr_pct"] <= 7, f"{data['atr_pct']:.1f}%"),
    ]

    for name, passed, value in rules:
        results.append({"rule": name, "pass": passed, "value": value})
        if passed:
            score += 1

    return results, score, max_score


def screen_smallcap(data, mode="bsjp"):
    """
    Screening rules untuk SAHAM SMALL CAP — 13 rules, need 9/13 to pass.
    Rules LEBIH KETAT dari normal (anti pump & dump).
    mode: "bsjp" atau "intraday" — mempengaruhi CHG% range.
    """
    results = []
    score = 0
    max_score = 13

    est = "~est" if data.get("vol_normalized") else ""

    # CHG% range berbeda per mode
    if mode == "intraday":
        chg_rule = ("CHG% -1.5% to +1.5%", -1.5 <= data["pct_change"] <= 1.5, f"{data['pct_change']:+.1f}%")
    else:
        chg_rule = ("CHG% -2% to +2%", -2 <= data["pct_change"] <= 2, f"{data['pct_change']:+.1f}%")

    rules = [
        # Layer 1: Likuiditas Small Cap (harus ramai)
        ("Volume > 5jt lembar", data["volume"] > 5_000_000, f"{data['volume']/1e6:.1f}jt{est}"),
        ("Value > 1 Miliar", data["value_b"] > 1, f"{data['value_b']:.1f}B{est}"),
        ("Market Cap 100B-500B", 0.1 <= data["market_cap_t"] <= 0.5, f"{data['market_cap_t']*1000:.0f}B"),

        # Layer 2: Momentum
        ("Close > EMA20", data["close"] > data["ema20"], f"{data['close']:.0f} vs {data['ema20']:.0f}"),
        ("MACD > Signal", data["macd_line"] > data["macd_signal"], f"{data['macd_line']:.2f} vs {data['macd_signal']:.2f}"),
        ("ADX > 20", data["adx"] > 20, f"{data['adx']:.1f}"),
        ("Vol Ratio >= 1.5x", data["volume_ratio"] >= 1.5, f"{data['volume_ratio']:.1f}x{est}"),

        # Layer 3: Anti-Jebakan (ketat)
        ("RSI 30-65", 30 <= data["rsi"] <= 65, f"{data['rsi']:.1f}"),
        chg_rule,
        ("MFI > 45", data["mfi"] > 45, f"{data['mfi']:.1f}"),
        ("Stoch %K < 80", data["stoch_k"] < 80, f"{data['stoch_k']:.1f}"),

        # Layer 4: Anti-Manipulasi (khusus small cap)
        ("Bukan ARA/ARB", data["pct_change"] > -7 and data["pct_change"] < 10, f"{data['pct_change']:+.1f}%"),
        ("Body > 30% range", data.get("body_ratio", 0) > 0.3, f"{data.get('body_ratio', 0)*100:.0f}%"),
    ]

    for name, passed, value in rules:
        results.append({"rule": name, "pass": passed, "value": value})
        if passed:
            score += 1

    return results, score, max_score


def screen_intraday(data):
    """Screening rules untuk INTRADAY — 16 rules

    Perbaikan vs versi lama:
    - Market Cap diturunkan 5T → 2T (banyak saham liquid di 2-5T)
    - Value diturunkan 10M → 5M
    - CHG% diperlebar -1% to +4% (tangkap early momentum, bukan cuma flat)
    - RSI diperlebar 40-75 (intraday momentum bisa RSI 70+ dan masih jalan)
    - Stoch %K diperlebar 25-80
    - ADX diturunkan 25 → 20 (trend mulai ADX 20)
    - ATR% diperlebar 1.5-7% (large cap bisa ATR 1.5%, momentum bisa 7%)
    - MACD duplikat dihapus (MACD > Signal ≈ Hist > 0)
    - Ditambah: Vol Ratio > 1.0x (KUNCI — volume harus di atas rata-rata)
    - Ditambah: Close/High > 90% (anti-distribusi, buyer masih dominan)
    - Ditambah: Stoch %K > %D (bullish crossover confirmation)
    """
    results = []
    score = 0
    max_score = 16

    est = "~est" if data.get("vol_normalized") else ""
    vr = data.get("volume_ratio", 0)
    high = data.get("high", data["close"])
    price_vs_high = (data["close"] / high * 100) if high > 0 else 100

    rules = [
        # Layer 1: Likuiditas (harus liquid, tapi tidak over-restrictive)
        ("Market Cap > 2T", data["market_cap_t"] > 2, f"{data['market_cap_t']:.1f}T"),
        ("Avg Vol 20D > 7.5jt", data["avg_volume_20d"] > 7_500_000, f"{data['avg_volume_20d']/1e6:.1f}jt"),
        ("Value > 5M", data["value_b"] > 5, f"{data['value_b']:.1f}M{est}"),
        ("Vol Ratio > 1.0x", vr > 1.0, f"{vr:.1f}x{est}"),

        # Layer 2: Momentum Kuat
        ("Close > EMA20", data["close"] > data["ema20"], f"{data['close']:.0f} vs {data['ema20']:.0f}"),
        ("EMA20 > EMA50", data["ema20"] > data["ema50"], f"{data['ema20']:.0f} vs {data['ema50']:.0f}"),
        ("MACD Hist > 0", data["macd_hist"] > 0, f"{data['macd_hist']:.2f}"),
        ("ADX > 20", data["adx"] > 20, f"{data['adx']:.1f}"),

        # Layer 3: Timing + Momentum Sweet Spot
        ("RSI 40-75", 40 <= data["rsi"] <= 75, f"{data['rsi']:.1f}"),
        ("Stoch %K 25-80", 25 <= data["stoch_k"] <= 80, f"{data['stoch_k']:.1f}"),
        ("Stoch %K > %D", data["stoch_k"] > data["stoch_d"], f"{data['stoch_k']:.1f} vs {data['stoch_d']:.1f}"),
        ("MFI > 45", data["mfi"] > 45, f"{data['mfi']:.1f}"),

        # Layer 4: Anti-Jebakan
        ("CHG% -1% to +4%", -1 <= data["pct_change"] <= 4, f"{data['pct_change']:+.1f}%"),
        ("BB %B 0.2-0.85", 0.2 <= data["bb_pctb"] <= 0.85, f"{data['bb_pctb']:.2f}"),
        ("ATR% 1.5-7%", 1.5 <= data["atr_pct"] <= 7, f"{data['atr_pct']:.1f}%"),
        ("Close/High > 90%", price_vs_high > 90, f"{price_vs_high:.0f}%"),
    ]

    for name, passed, value in rules:
        results.append({"rule": name, "pass": passed, "value": value})
        if passed:
            score += 1

    return results, score, max_score


# ============================================================
# ENTRY / STOP LOSS / TARGET PROFIT CALCULATOR
# ============================================================

def calc_entry_sl_tp(data, mode="bsjp"):
    """
    Hitung Entry, Stop Loss, Target Profit berdasarkan riset para ahli.

    BSJP (Overnight):
      SL = MAX(Entry - 1.0×ATR, Pivot S2)
      Min 1.5% dari entry (anti-noise overnight)
      Cap max 3% dari entry (overnight risk)
      Range SL realistis: 1.5% - 3%
      R:R minimum 1:1.5

    INTRADAY:
      SL = MAX(Pivot S1 - 0.5×ATR, Entry - 1.5×ATR, Prev Low - 1%)
      Min 1% dari entry (anti-whipsaw)
      Cap max 2% dari entry
      Range SL realistis: 1% - 2%
      R:R minimum 1:2
    """
    atr = data["atr"]
    close = data["close"]
    s1 = data["pivot_s1"]
    s2 = data["pivot_s2"]
    pp = data["pivot_pp"]
    r1 = data["pivot_r1"]
    r2 = data["pivot_r2"]
    prev_low = data["prev_low"]

    if mode == "bsjp":
        # === BSJP: Entry dekat S1 atau close sore ===
        entry = max(s1, close * 0.98)
        if entry > close:
            entry = close

        # SL metode ahli: MAX(Entry - 1.0×ATR, Pivot S2)
        # ATR sudah menghitung gap overnight (True Range includes gap)
        sl_atr = entry - (1.0 * atr)
        sl_pivot_s2 = s2
        sl = max(sl_atr, sl_pivot_s2)  # Pilih yang lebih ketat (dekat entry)

        # MINIMUM SL jarak 1.5% dari entry
        # Alasan: overnight gap + noise normal bisa 1-2%
        # SL < 1.5% = terlalu ketat, pasti kena stop oleh noise
        MIN_SL_BSJP = 0.015
        sl_ceiling = entry * (1 - MIN_SL_BSJP)
        sl_too_tight = False
        if sl > sl_ceiling:
            sl = sl_ceiling
            sl_too_tight = True

        # Cap max 3% dari entry (overnight risk limit)
        MAX_SL_BSJP = 0.03
        sl_floor = entry * (1 - MAX_SL_BSJP)
        sl_capped = False
        if sl < sl_floor:
            sl = sl_floor
            sl_capped = True

        # SL basis
        if sl_capped:
            sl_basis = f"Max 3% cap (overnight)"
        elif sl_too_tight:
            sl_basis = f"Min 1.5% jarak (anti-noise)"
        elif sl == sl_pivot_s2:
            sl_basis = f"Pivot S2 ({s2:,.0f})"
        else:
            sl_basis = f"Entry - 1.0×ATR"

        tp1 = entry + (0.75 * atr)
        tp2 = min(entry + (1.0 * atr), r1) if r1 > entry else entry + (1.0 * atr)

        # TP basis
        tp1_basis = "Entry + 0.75×ATR"
        tp2_basis = f"Pivot R1 ({r1:,.0f})" if r1 > entry and r1 <= entry + atr else "Entry + 1.0×ATR"

    elif mode == "bsjp_smallcap":
        # === BSJP SMALL CAP: Entry konservatif, SL ketat ===
        entry = close  # Entry di harga close (small cap: jangan kejar)

        # SL ketat — max 2% (small cap volatile, disiplin ketat)
        sl = entry * 0.98  # Flat 2% SL
        sl_too_tight = False
        sl_capped = False
        sl_basis = "Max 2% (small cap — SL ketat wajib)"

        # TP: ambil profit cepat (hit and run)
        tp1 = entry + (1.0 * atr)
        tp2 = entry + (1.5 * atr)
        tp1_basis = "Entry + 1.0×ATR (hit & run)"
        tp2_basis = "Entry + 1.5×ATR"

    elif mode == "intraday_smallcap":
        # === INTRADAY SMALL CAP: Entry di close, SL sangat ketat ===
        entry = close

        # SL sangat ketat — max 1.5% (intraday small cap)
        sl = entry * 0.985  # Flat 1.5% SL
        sl_too_tight = False
        sl_capped = False
        sl_basis = "Max 1.5% (intraday small cap — SL ketat)"

        # TP: ambil profit cepat
        tp1 = entry + (0.7 * atr)
        tp2 = entry + (1.0 * atr)
        tp1_basis = "Entry + 0.7×ATR (hit & run)"
        tp2_basis = "Entry + 1.0×ATR"

    elif mode == "ara_momentum":
        # === ARA MOMENTUM: CONFLUENCE-BASED SL ===
        # Golden rule: SL ditempatkan di level yang jika tersentuh,
        # artinya tesis trading sudah SALAH — bukan sekadar angka random.
        #
        # Confluence layers:
        #   1. STRUCTURE: Swing low / prev close / day low — "di bawah struktur"
        #   2. ATR:       Minimal 1x ATR dari entry — "cukup ruang untuk noise"
        #   3. ROUND NUM: Snap ke bawah angka bulat — "psikologis market"
        #
        # Jika SL tersentuh = momentum sudah mati + struktur tembus = tesis salah → cut.
        entry = close
        prev_close_val = data.get("prev_close", close / 1.05)
        chg = data.get("pct_change", 0)

        # ─── LAYER 1: STRUCTURE (cari level support terkuat) ─────────
        # Kandidat structure level (harus di bawah entry):
        swing_low_5d = data.get("swing_low_5d", prev_close_val)
        swing_low_3d = data.get("swing_low_3d", prev_close_val)
        day_low = data.get("day_low", data.get("low", close))
        pivot_s1 = data.get("pivot_s1", 0)

        # Kumpulkan semua support candidates yang valid (di bawah entry)
        structure_candidates = []
        if prev_close_val < entry:
            structure_candidates.append(("prev_close", prev_close_val))
        if day_low < entry:
            structure_candidates.append(("day_low", day_low))
        if swing_low_3d < entry:
            structure_candidates.append(("swing_low_3d", swing_low_3d))
        if swing_low_5d < entry:
            structure_candidates.append(("swing_low_5d", swing_low_5d))
        if 0 < pivot_s1 < entry:
            structure_candidates.append(("pivot_s1", pivot_s1))

        # Pilih structure level tertinggi (closest support below entry)
        # Karena support terdekat = level paling kuat untuk menjaga momentum
        if structure_candidates:
            structure_candidates.sort(key=lambda x: x[1], reverse=True)
            struct_name, struct_level = structure_candidates[0]
        else:
            struct_name = "prev_close"
            struct_level = prev_close_val

        # SL = di bawah structure level (buffer 1-2% di bawah support)
        struct_buffer = 0.02 if chg >= 10 else 0.01
        sl_structure = struct_level * (1 - struct_buffer)

        # ─── LAYER 2: ATR (minimum distance dari entry) ──────────────
        # SL harus minimal 1x ATR dari entry agar tidak kena noise intraday
        sl_atr_min = entry - (1.0 * atr)
        # Idealnya 1.5x ATR untuk momentum stocks
        sl_atr_ideal = entry - (1.5 * atr)

        # ─── COMBINE: Pilih yang paling longgar (lebih jauh dari entry) ──
        # Logika: SL harus di bawah struktur DAN cukup jauh (ATR).
        # Jika structure sudah jauh → gunakan structure.
        # Jika structure terlalu dekat → perlebar ke ATR minimum.
        sl = min(sl_structure, sl_atr_ideal)  # ambil yang lebih jauh

        # Pastikan SL minimal 1x ATR dari entry (noise filter)
        if sl > sl_atr_min:
            sl = sl_atr_min

        # ─── LAYER 3: ROUND NUMBER (snap ke bawah angka bulat) ────────
        # Psikologis: banyak SL cluster di angka bulat, taruh SL di bawahnya
        def snap_below_round(price):
            """Snap SL ke tepat di bawah angka psikologis terdekat."""
            if price >= 5000:
                base = int(price / 100) * 100  # round ke ratusan
                return base - 25 if price <= base + 25 else price
            elif price >= 500:
                base = int(price / 50) * 50     # round ke 50-an
                return base - 5 if price <= base + 5 else price
            elif price >= 100:
                base = int(price / 25) * 25     # round ke 25-an
                return base - 2 if price <= base + 2 else price
            else:
                base = int(price / 10) * 10     # round ke 10-an
                return base - 1 if price <= base + 1 else price

        sl = snap_below_round(sl)

        # ─── SAFETY CAPS ─────────────────────────────────────────────
        # SL tidak boleh >= entry
        if sl >= entry:
            sl = entry * 0.95

        # Dynamic max cap berdasarkan CHG% (batas bawah SL)
        if chg >= 15:
            max_sl_pct = 0.15
        elif chg >= 10:
            max_sl_pct = 0.12
        elif chg >= 5:
            max_sl_pct = 0.08
        else:
            max_sl_pct = 0.05

        sl_floor = entry * (1 - max_sl_pct)
        sl_capped = False
        if sl < sl_floor:
            sl = sl_floor
            sl_capped = True

        # Minimum SL jarak 3% dari entry (anti-noise / whipsaw)
        MIN_SL_ARA = 0.03
        sl_ceiling = entry * (1 - MIN_SL_ARA)
        sl_too_tight = False
        if sl > sl_ceiling:
            sl = sl_ceiling
            sl_too_tight = True

        # ─── SL BASIS: transparansi metode yang dipakai ──────────────
        sl_dist_pct = abs((sl - entry) / entry * 100)
        confluence_layers = []
        if not sl_capped and not sl_too_tight:
            # Cek layer mana yang dominan
            if abs(sl - sl_structure) < entry * 0.005:
                confluence_layers.append(f"Structure ({struct_name} {struct_level:,.0f})")
            if abs(sl - sl_atr_ideal) < entry * 0.005 or abs(sl - sl_atr_min) < entry * 0.005:
                confluence_layers.append("ATR")

        if sl_capped:
            sl_basis = f"Max {max_sl_pct*100:.0f}% cap (CHG {chg:+.0f}%)"
        elif sl_too_tight:
            sl_basis = "Min 3% (anti-whipsaw)"
        elif confluence_layers:
            sl_basis = " + ".join(confluence_layers)
        else:
            sl_basis = f"Below {struct_name} ({struct_level:,.0f})"

        # ─── TP: target ARA limit ────────────────────────────────────
        ara_limit = data.get("ara_limit_price", close * 1.25)
        tp1 = entry + (1.5 * atr)
        tp2 = min(entry + (3.0 * atr), ara_limit * 0.98)
        if tp2 <= tp1:
            tp2 = tp1 * 1.02

        tp1_basis = "Entry + 1.5×ATR (momentum target)"
        tp2_basis = f"ARA Limit ({ara_limit:,.0f}) - 2%" if tp2 >= ara_limit * 0.95 else "Entry + 3.0×ATR"

    else:  # intraday
        # === INTRADAY: Entry dekat PP atau S1 ===
        entry = max(s1, close * 0.99)
        if entry > close:
            entry = close

        # SL metode ahli: MAX dari 3 kandidat (pilih yang paling ketat)
        # 1. ATR 1.5x (paling direkomendasikan)
        sl_atr = entry - (1.5 * atr)
        # 2. Pivot S1 + buffer ATR
        sl_pivot = s1 - (0.5 * atr)
        # 3. Low candle kemarin - 1% (untuk breakout trade)
        sl_prev_low = prev_low * 0.99

        # Pilih MAX = yang paling dekat entry (tightest)
        sl_candidates = [sl_atr, sl_pivot, sl_prev_low]
        sl = max(c for c in sl_candidates if c < entry) if any(c < entry for c in sl_candidates) else sl_atr

        # MINIMUM SL jarak 1% dari entry
        # Alasan: whipsaw intraday bisa 0.5-1%, SL terlalu ketat = pasti kena
        MIN_SL_INTRA = 0.01
        sl_ceiling = entry * (1 - MIN_SL_INTRA)
        sl_too_tight = False
        if sl > sl_ceiling:
            sl = sl_ceiling
            sl_too_tight = True

        # Cap max 2% dari entry (intraday risk limit)
        MAX_SL_INTRA = 0.02
        sl_floor = entry * (1 - MAX_SL_INTRA)
        sl_capped = False
        if sl < sl_floor:
            sl = sl_floor
            sl_capped = True

        # SL basis
        if sl_capped:
            sl_basis = f"Max 2% cap (intraday)"
        elif sl_too_tight:
            sl_basis = f"Min 1% jarak (anti-whipsaw)"
        elif sl == sl_prev_low:
            sl_basis = f"Prev Low ({prev_low:,.0f}) - 1%"
        elif sl == sl_pivot:
            sl_basis = f"Pivot S1 - 0.5×ATR"
        else:
            sl_basis = f"Entry - 1.5×ATR"

        # TP intraday: ATR-based, TIDAK di-cap oleh pivot
        # Alasan: SL ketat (max 2%), butuh TP agresif untuk R:R >= 1:1.5
        # Pivot hanya sebagai referensi — intraday momentum sering tembus pivot
        tp1 = entry + (0.75 * atr)
        tp2 = entry + (1.5 * atr)

        # TP basis — mention pivot jika nearby sebagai referensi
        if r1 > entry and abs(r1 - tp1) < 0.3 * atr:
            tp1_basis = f"0.75×ATR ≈ Pivot R1 ({r1:,.0f})"
        else:
            tp1_basis = "Entry + 0.75×ATR"
        if r2 > entry and abs(r2 - tp2) < 0.3 * atr:
            tp2_basis = f"1.5×ATR ≈ Pivot R2 ({r2:,.0f})"
        else:
            tp2_basis = "Entry + 1.5×ATR"

    # Entry Area
    entry_area_max = (tp2 + sl) / 2
    if entry_area_max > close:
        entry_area_max = close
    entry_area_min = entry

    risk = entry - sl
    reward1 = tp1 - entry
    reward2 = tp2 - entry
    rr1 = reward1 / risk if risk > 0 else 0
    rr2 = reward2 / risk if risk > 0 else 0

    avg_entry = (entry_area_min + entry_area_max) / 2
    real_gain_tp1 = ((tp1 - avg_entry) / avg_entry) * 100 if avg_entry > 0 else 0
    real_gain_tp2 = ((tp2 - avg_entry) / avg_entry) * 100 if avg_entry > 0 else 0
    real_loss_sl = ((sl - avg_entry) / avg_entry) * 100 if avg_entry > 0 else 0

    p_tp1 = 0.55
    p_tp2_extra = 0.15
    p_sl = 0.40
    expected_return = (p_tp1 * real_gain_tp1) + (p_tp2_extra * real_gain_tp2) + (p_sl * real_loss_sl)

    # === ANALISIS KEKETATAN SL vs ATR ===
    # Bandingkan jarak SL (%) terhadap ATR (%) — volatilitas harian saham
    # Jika SL lebih kecil dari pergerakan harian normal, hampir pasti kena stop
    sl_pct_abs = abs(((sl - entry) / entry) * 100) if entry > 0 else 0
    atr_pct = (atr / close) * 100 if close > 0 else 0
    sl_vs_atr = sl_pct_abs / atr_pct if atr_pct > 0 else 0

    if mode in ("bsjp", "bsjp_smallcap"):
        # BSJP overnight: perlu lebih longgar karena gap overnight
        if sl_vs_atr < 0.50:
            sl_ketat = "SANGAT KETAT"
            sl_ketat_icon = "🔴"
            sl_ketat_note = "SL < 50% ATR, hampir pasti kena stop oleh gap/noise"
        elif sl_vs_atr < 0.75:
            sl_ketat = "KETAT"
            sl_ketat_icon = "🟠"
            sl_ketat_note = "SL < 75% ATR, risiko tinggi kena stop overnight"
        elif sl_vs_atr < 1.0:
            sl_ketat = "CUKUP"
            sl_ketat_icon = "🟡"
            sl_ketat_note = "SL mendekati 1× ATR, borderline"
        else:
            sl_ketat = "AMAN"
            sl_ketat_icon = "🟢"
            sl_ketat_note = "SL >= 1× ATR, ruang cukup untuk noise normal"
    else:
        # Intraday: bisa lebih ketat tapi tetap butuh ruang
        if sl_vs_atr < 0.40:
            sl_ketat = "SANGAT KETAT"
            sl_ketat_icon = "🔴"
            sl_ketat_note = "SL < 40% ATR, hampir pasti kena whipsaw"
        elif sl_vs_atr < 0.60:
            sl_ketat = "KETAT"
            sl_ketat_icon = "🟠"
            sl_ketat_note = "SL < 60% ATR, risiko tinggi kena whipsaw"
        elif sl_vs_atr < 0.80:
            sl_ketat = "CUKUP"
            sl_ketat_icon = "🟡"
            sl_ketat_note = "SL mendekati range intraday, borderline"
        else:
            sl_ketat = "AMAN"
            sl_ketat_icon = "🟢"
            sl_ketat_note = "SL cukup longgar untuk volatilitas intraday"

    return {
        "entry": entry,
        "entry_area_min": entry_area_min,
        "entry_area_max": entry_area_max,
        "avg_entry": avg_entry,
        "sl": sl,
        "sl_basis": sl_basis,
        "tp1": tp1,
        "tp1_basis": tp1_basis,
        "tp2": tp2,
        "tp2_basis": tp2_basis,
        "risk": risk,
        "reward1": reward1,
        "reward2": reward2,
        "rr1": rr1,
        "rr2": rr2,
        "entry_pct": ((entry - close) / close) * 100,
        "sl_pct": ((sl - entry) / entry) * 100,
        "tp1_pct": ((tp1 - entry) / entry) * 100,
        "tp2_pct": ((tp2 - entry) / entry) * 100,
        "real_gain_tp1": real_gain_tp1,
        "real_gain_tp2": real_gain_tp2,
        "real_loss_sl": real_loss_sl,
        "expected_return": expected_return,
        "sl_vs_atr": sl_vs_atr,
        "sl_ketat": sl_ketat,
        "sl_ketat_icon": sl_ketat_icon,
        "sl_ketat_note": sl_ketat_note,
    }


# ============================================================
# QUALITY SCORE (0-100)
# ============================================================

def calc_quality_score(data, mode="bsjp"):
    """Hitung skor kualitas 0-100 — scoring berbeda per mode.

    BSJP: favor stability (overnight hold, butuh saham tenang)
    INTRADAY: favor momentum (butuh saham yang sedang bergerak)
    """
    score = 0

    if mode == "intraday":
        return _calc_quality_score_intraday(data)

    # === BSJP QUALITY SCORE ===

    # RSI sweet spot (20%) — BSJP: favor 50-60 (not overbought)
    rsi = data["rsi"]
    if 50 <= rsi <= 60:
        score += 20
    elif 45 <= rsi <= 65:
        score += 15
    elif 40 <= rsi <= 70:
        score += 10

    # MACD Histogram (15%)
    if data["macd_hist"] > 0:
        if data["macd_hist"] > abs(data["macd_signal"]) * 0.1:
            score += 15
        else:
            score += 10

    # Volume ratio (15%)
    vr = data["volume_ratio"]
    if vr > 2:
        score += 15
    elif vr > 1.5:
        score += 10
    elif vr > 1:
        score += 5

    # ADX strength (10%)
    adx = data["adx"]
    if adx > 30:
        score += 10
    elif adx > 25:
        score += 7
    elif adx > 20:
        score += 4

    # Bollinger %B position (10%) — BSJP: favor center
    bb = data["bb_pctb"]
    if 0.4 <= bb <= 0.6:
        score += 10
    elif 0.3 <= bb <= 0.7:
        score += 7
    elif 0.2 <= bb <= 0.8:
        score += 3

    # MFI strength (10%)
    mfi = data["mfi"]
    if mfi > 60:
        score += 10
    elif mfi > 50:
        score += 7
    elif mfi > 40:
        score += 4

    # EMA alignment (10%)
    if data["close"] > data["ema20"] > data["ema50"]:
        score += 10
    elif data["close"] > data["ema20"]:
        score += 5

    # Change stability (10%) — BSJP: favor tenang (overnight butuh stabil)
    chg = abs(data["pct_change"])
    if chg < 2:
        score += 10
    elif chg < 5:
        score += 5

    return min(score, 100)


def _calc_quality_score_intraday(data):
    """Quality score khusus INTRADAY — favor momentum, bukan stability.

    Perbedaan vs BSJP:
    - RSI sweet spot lebih tinggi (55-70 vs 50-60)
    - Volume ratio bobot lebih besar (20% vs 15%)
    - CHG% reward early momentum (0.5-3%), bukan stability (<2%)
    - BB %B favor upper momentum (0.5-0.8 vs 0.4-0.6)
    - Tambah: Close near high bonus (buyer dominan)
    """
    score = 0

    # RSI momentum zone (18%) — intraday: favor 55-70 (stronger momentum)
    rsi = data["rsi"]
    if 55 <= rsi <= 70:
        score += 18
    elif 50 <= rsi <= 75:
        score += 13
    elif 40 <= rsi <= 80:
        score += 7

    # MACD Histogram (12%)
    if data["macd_hist"] > 0:
        if data["macd_hist"] > abs(data["macd_signal"]) * 0.1:
            score += 12
        else:
            score += 8

    # Volume ratio (20%) — PALING PENTING untuk intraday
    vr = data["volume_ratio"]
    if vr > 2.0:
        score += 20
    elif vr > 1.5:
        score += 15
    elif vr > 1.2:
        score += 10
    elif vr > 1.0:
        score += 5

    # ADX strength (10%)
    adx = data["adx"]
    if adx > 30:
        score += 10
    elif adx > 25:
        score += 7
    elif adx > 20:
        score += 4

    # Bollinger %B position (10%) — intraday: favor upper momentum
    bb = data["bb_pctb"]
    if 0.5 <= bb <= 0.8:
        score += 10
    elif 0.4 <= bb <= 0.85:
        score += 7
    elif 0.3 <= bb <= 0.9:
        score += 3

    # MFI strength (10%)
    mfi = data["mfi"]
    if mfi > 60:
        score += 10
    elif mfi > 50:
        score += 7
    elif mfi > 45:
        score += 4

    # EMA alignment (8%)
    if data["close"] > data["ema20"] > data["ema50"]:
        score += 8
    elif data["close"] > data["ema20"]:
        score += 4

    # CHG% early momentum (7%) — intraday: reward saham yang SUDAH mulai gerak
    chg = data["pct_change"]
    if 0.5 <= chg <= 3:
        score += 7  # Sweet spot: sudah gerak tapi belum terlalu tinggi
    elif 0 < chg <= 4:
        score += 4
    elif -1 <= chg <= 0:
        score += 2  # Flat, bisa jadi akan gerak

    # Close near high (5%) — buyer dominan, bukan distribusi
    high = data.get("high", data["close"])
    if high > 0:
        close_vs_high = data["close"] / high * 100
        if close_vs_high >= 97:
            score += 5
        elif close_vs_high >= 93:
            score += 3
        elif close_vs_high >= 90:
            score += 1

    return min(score, 100)


def calc_quality_score_smallcap(data):
    """Hitung skor kualitas small cap 0-100 — volume & momentum weighted."""
    score = 0

    # Volume Ratio (25% — KEY indicator small cap)
    vr = data["volume_ratio"]
    if vr > 3:
        score += 25
    elif vr > 2:
        score += 20
    elif vr > 1.5:
        score += 15
    elif vr > 1:
        score += 5

    # RSI sweet spot (15%)
    rsi = data["rsi"]
    if 45 <= rsi <= 60:
        score += 15
    elif 35 <= rsi <= 65:
        score += 10
    elif 30 <= rsi <= 70:
        score += 5

    # MACD Histogram (15%)
    if data["macd_line"] > data["macd_signal"]:
        if data["macd_hist"] > abs(data["macd_signal"]) * 0.1:
            score += 15
        else:
            score += 10

    # ADX strength (10%)
    adx = data["adx"]
    if adx > 30:
        score += 10
    elif adx > 25:
        score += 7
    elif adx > 20:
        score += 4

    # MFI strength (10%)
    mfi = data["mfi"]
    if mfi > 60:
        score += 10
    elif mfi > 50:
        score += 7
    elif mfi > 45:
        score += 4

    # EMA alignment (10%)
    if data["close"] > data["ema20"] > data["ema50"]:
        score += 10
    elif data["close"] > data["ema20"]:
        score += 5

    # Body ratio (5% — anti manipulasi)
    br = data.get("body_ratio", 0)
    if br > 0.5:
        score += 5
    elif br > 0.3:
        score += 3

    # Change stability (10% — small cap: stabil = lebih aman)
    chg = abs(data["pct_change"])
    if chg < 1.5:
        score += 10
    elif chg < 3:
        score += 5

    return min(score, 100)


# ============================================================
# DISPLAY FUNCTIONS
# ============================================================

def print_header(mode, market_progress=None):
    mkt_status = "📡 LIVE" if market_progress is not None else "📴 CLOSED"
    print("\n" + "=" * 70)
    print(f"  IDX STOCK SCREENER — {'BSJP (Beli Sore Jual Pagi)' if mode == 'bsjp' else 'INTRADAY (Beli Pagi Jual Sore)'}")
    print(f"  Tanggal: {datetime.now().strftime('%d %B %Y, %H:%M WIB')}  [{mkt_status}]")
    if market_progress is not None:
        print(f"  Volume: dinormalisasi otomatis ({market_progress*100:.0f}% hari trading)")
    print("=" * 70)


def print_stock_result(ticker, data, rules, rule_score, max_rules, quality, entry_data, mode):
    """Tampilkan hasil screening per saham"""
    passed = rule_score >= (max_rules - 3)  # Toleransi 3 rule gagal
    perfect = rule_score == max_rules

    # Status
    if perfect:
        status = "⭐ PERFECT"
    elif rule_score >= max_rules - 1:
        status = "✅ STRONG"
    elif rule_score >= max_rules - 2:
        status = "🟡 MODERATE"
    elif rule_score >= max_rules - 3:
        status = "🟠 WEAK"
    else:
        status = "❌ FAIL"

    # Quality label
    if quality >= 80:
        q_label = "STRONG BUY"
    elif quality >= 60:
        q_label = "BUY"
    elif quality >= 40:
        q_label = "WATCH"
    else:
        q_label = "SKIP"

    print(f"\n{'─' * 70}")
    print(f"  {ticker}  |  Rp {data['close']:,.0f}  ({data['pct_change']:+.1f}%)  |  {status}  |  Skor: {quality}/100 [{q_label}]")
    print(f"  Rules: {rule_score}/{max_rules} passed")
    print(f"{'─' * 70}")

    # Rules detail
    fail_rules = []
    for r in rules:
        icon = "✅" if r["pass"] else "❌"
        line = f"  {icon} {r['rule']:.<30s} {r['value']}"
        if not r["pass"]:
            fail_rules.append(r["rule"])
        print(line)

    if fail_rules:
        print(f"\n  ⚠️  Gagal: {', '.join(fail_rules)}")

    # Entry/SL/TP (hanya jika cukup lolos)
    if rule_score >= max_rules - 3:
        e = entry_data
        print(f"\n  {'─' * 50}")
        print(f"  📊 PIVOT POINTS")
        print(f"     S2: {data['pivot_s2']:,.0f}  |  S1: {data['pivot_s1']:,.0f}  |  PP: {data['pivot_pp']:,.0f}  |  R1: {data['pivot_r1']:,.0f}  |  R2: {data['pivot_r2']:,.0f}")
        print(f"\n  🎯 ENTRY / SL / TP")
        print(f"     Entry  : Rp {e['entry']:>10,.0f}  ({e['entry_pct']:+.1f}% dari close)")
        print(f"     Area   : Rp {e['entry_area_min']:>10,.0f}  —  Rp {e['entry_area_max']:,.0f}  (masih layak entry)")
        print(f"     SL     : Rp {e['sl']:>10,.0f}  ({e['sl_pct']:+.1f}%)  ← {e['sl_basis']}")
        print(f"     SL/ATR : {e['sl_ketat_icon']} {e['sl_ketat']} — SL={abs(e['sl_pct']):.1f}% vs ATR={data['atr_pct']:.1f}% (rasio {e['sl_vs_atr']:.2f}x)")
        if e['sl_ketat'] in ("SANGAT KETAT", "KETAT"):
            print(f"              ⚠️  {e['sl_ketat_note']}")
        print(f"     TP1    : Rp {e['tp1']:>10,.0f}  ({e['tp1_pct']:+.1f}%)  ← {e['tp1_basis']}")
        print(f"     TP2    : Rp {e['tp2']:>10,.0f}  ({e['tp2_pct']:+.1f}%)  ← {e['tp2_basis']}")
        print(f"     R:R    : 1:{e['rr1']:.1f} (TP1)  |  1:{e['rr2']:.1f} (TP2)")
        print(f"     ATR    : Rp {data['atr']:,.0f}  ({data['atr_pct']:.1f}%)")
        print(f"\n  📈 ESTIMASI REALISTIS (dari avg entry Rp {e['avg_entry']:,.0f})")
        print(f"     Jika kena TP1 : +{e['real_gain_tp1']:.1f}%")
        print(f"     Jika kena TP2 : +{e['real_gain_tp2']:.1f}%")
        print(f"     Jika kena SL  : {e['real_loss_sl']:.1f}%")
        print(f"     Expected ret. : {e['expected_return']:+.2f}% per trade")
        if e["expected_return"] > 0:
            print(f"     ✅ Layak — expected return positif")
        else:
            print(f"     ⚠️  Kurang layak — expected return negatif")

        min_rr = 1.5 if mode == "bsjp" else 2.0
        if e["rr1"] < min_rr:
            print(f"     ⚠️  R:R < {min_rr:.1f} untuk {'BSJP' if mode == 'bsjp' else 'Intraday'}")

    return {
        "ticker": ticker,
        "close": data["close"],
        "pct_change": data["pct_change"],
        "rule_score": rule_score,
        "max_rules": max_rules,
        "quality": quality,
        "status": status,
        "q_label": q_label,
        "entry_data": entry_data if rule_score >= max_rules - 3 else None,
    }


def print_summary(results, mode, market_progress=None):
    """Tampilkan ringkasan akhir"""
    # Sort by quality score
    results.sort(key=lambda x: x["quality"], reverse=True)

    print("\n" + "=" * 70)
    print(f"  📋 RINGKASAN SCREENING {'BSJP' if mode == 'bsjp' else 'INTRADAY'}")
    print("=" * 70)
    print(f"\n  Total saham di-scan  : {len(results)}")

    strong = [r for r in results if r["quality"] >= 60 and r["rule_score"] >= r["max_rules"] - 2]
    watch = [r for r in results if 40 <= r["quality"] < 60 or (r["quality"] >= 60 and r["rule_score"] < r["max_rules"] - 2)]
    skip = [r for r in results if r["quality"] < 40]

    print(f"  Lolos (BUY/STRONG)   : {len(strong)} saham")
    print(f"  Watch                : {len(watch)} saham")
    print(f"  Skip                 : {len(skip)} saham")

    w = 160

    if strong:
        print(f"\n  {'─' * w}")
        print(f"  🏆 TOP PICKS (diurutkan dari skor tertinggi)")
        print(f"  {'─' * w}")
        print(f"  {'No':<4}{'Ticker':<7}{'Harga':>8}{'Chg':>7}{'Score':>6}{'Label':>11}{'Entry Area':>22}{'SL':>10}{'%SL':>7}{'SL/ATR':>14}{'TP1':>10}{'%TP1':>7}{'TP2':>10}{'%TP2':>7}{'Exp.Ret':>9}")
        print(f"  {'─' * w}")
        for i, r in enumerate(strong[:10], 1):
            e = r.get("entry_data")
            if e:
                area = f"{e['entry_area_min']:,.0f}-{e['entry_area_max']:,.0f}"
                exp_tag = f"{e['expected_return']:+.1f}%"
                sl_tag = f"{e['sl_ketat_icon']}{e['sl_ketat']}"
                print(f"  {i:<4}{r['ticker']:<7}{r['close']:>8,.0f}{r['pct_change']:>+6.1f}%{r['quality']:>5}/100{r['q_label']:>11}{area:>22}{e['sl']:>10,.0f}{e['sl_pct']:>+6.1f}%{sl_tag:>14}{e['tp1']:>10,.0f}{e['real_gain_tp1']:>+6.1f}%{e['tp2']:>10,.0f}{e['real_gain_tp2']:>+6.1f}%{exp_tag:>9}")
            else:
                print(f"  {i:<4}{r['ticker']:<7}{r['close']:>8,.0f}{r['pct_change']:>+6.1f}%{r['quality']:>5}/100{r['q_label']:>11}{'—':>22}{'—':>10}{'—':>7}{'—':>14}{'—':>10}{'—':>7}{'—':>10}{'—':>7}{'—':>9}")

        # Best pick detail
        best = strong[0]
        if best["entry_data"]:
            e = best["entry_data"]
            print(f"\n  🥇 BEST PICK: {best['ticker']}")
            print(f"     Entry Area : Rp {e['entry_area_min']:,.0f} — Rp {e['entry_area_max']:,.0f}")
            print(f"     SL: Rp {e['sl']:,.0f} ({e['sl_pct']:+.1f}%)  |  TP1: Rp {e['tp1']:,.0f} (+{e['real_gain_tp1']:.1f}%)  |  TP2: Rp {e['tp2']:,.0f} (+{e['real_gain_tp2']:.1f}%)")
            print(f"     SL basis: {e['sl_basis']}")
            print(f"     SL/ATR : {e['sl_ketat_icon']} {e['sl_ketat']} (rasio {e['sl_vs_atr']:.2f}x) — {e['sl_ketat_note']}")
            print(f"     R:R = 1:{e['rr1']:.1f} (TP1)  |  1:{e['rr2']:.1f} (TP2)  |  Expected: {e['expected_return']:+.2f}% per trade")
    else:
        print(f"\n  ⚠️  Tidak ada saham yang lolos filter ketat hari ini.")
        print(f"  Ini normal — filter ketat = sedikit tapi berkualitas.")
        print(f"  Coba lagi besok atau kurangi 1-2 rule jika ingin lebih banyak kandidat.")

    if watch:
        print(f"\n  {'─' * w}")
        print(f"  👀 WATCHLIST (hampir lolos, pantau besok)")
        print(f"  {'─' * w}")
        print(f"  {'No':<4}{'Ticker':<7}{'Harga':>8}{'Chg':>7}{'Score':>6}{'Status':>8}{'Entry Area':>22}{'SL':>10}{'%SL':>7}{'SL/ATR':>14}{'TP1':>10}{'%TP1':>7}{'TP2':>10}{'%TP2':>7}{'Exp.Ret':>9}")
        print(f"  {'─' * w}")
        for i, r in enumerate(watch[:10], 1):
            e = r.get("entry_data")
            if e:
                area = f"{e['entry_area_min']:,.0f}-{e['entry_area_max']:,.0f}"
                exp_tag = f"{e['expected_return']:+.1f}%"
                sl_tag = f"{e['sl_ketat_icon']}{e['sl_ketat']}"
                print(f"  {i:<4}{r['ticker']:<7}{r['close']:>8,.0f}{r['pct_change']:>+6.1f}%{r['quality']:>5}/100{r['status']:>8}{area:>22}{e['sl']:>10,.0f}{e['sl_pct']:>+6.1f}%{sl_tag:>14}{e['tp1']:>10,.0f}{e['real_gain_tp1']:>+6.1f}%{e['tp2']:>10,.0f}{e['real_gain_tp2']:>+6.1f}%{exp_tag:>9}")
            else:
                print(f"  {i:<4}{r['ticker']:<7}{r['close']:>8,.0f}{r['pct_change']:>+6.1f}%{r['quality']:>5}/100{r['status']:>8}{'—':>22}{'—':>10}{'—':>7}{'—':>14}{'—':>10}{'—':>7}{'—':>10}{'—':>7}{'—':>9}")

    print(f"\n  {'─' * 60}")
    if mode == "bsjp":
        print(f"  ⏰ Waktu: Beli sore (14:00-15:30), jual besok pagi (09:00-10:00)")
        print(f"  🛡️  SL: MAX(Entry - 1.0×ATR, Pivot S2), cap 3%")
        print(f"     → Jika open < SL level → langsung jual (gap down)")
        print(f"     → ATR sudah menghitung gap overnight otomatis")
        print(f"  💰 Max risiko per trade: 3% dari modal")
        print(f"  📊 Max posisi bersamaan: 2-3 saham")
        print(f"  📐 R:R minimum: 1:1.5")
    else:
        print(f"  ⏰ Waktu: Beli pagi (09:15-10:00), jual sore (15:00-15:40)")
        print(f"  🛡️  SL: MAX(Pivot S1 - 0.5×ATR, Entry - 1.5×ATR, Prev Low - 1%)")
        print(f"     → 3 metode saling konfirmasi, pilih yang paling ketat")
        print(f"     → Cap max 2% dari entry (disiplin intraday)")
        print(f"  💰 Max risiko per trade: 1.5-2% dari modal")
        print(f"  📊 Max posisi bersamaan: 1-2 saham")
        print(f"  📐 R:R minimum: 1:2")
    print(f"\n  📏 SL/ATR — Analisis Keketatan Stop Loss:")
    print(f"     🟢 AMAN        = SL cukup longgar, tahan noise normal")
    print(f"     🟡 CUKUP       = Borderline, bisa kena jika volatile")
    print(f"     🟠 KETAT       = Risiko tinggi kena stop oleh noise")
    print(f"     🔴 SANGAT KETAT = Hampir pasti kena stop, hindari!")
    print(f"     Rumus: SL% ÷ ATR% → semakin tinggi rasio, semakin aman")
    if market_progress is not None:
        pct = market_progress * 100
        print(f"\n  📡 Volume Normalisasi:")
        print(f"     Market progress: {pct:.0f}% — volume hari ini di-scale ke estimasi full-day")
        print(f"     Value bertanda ~est = estimasi (volume dinormalisasi)")
        if pct < 30:
            print(f"     ⚠️  Akurasi rendah (baru {pct:.0f}%). Jalankan ulang siang/sore untuk konfirmasi")
        elif pct < 60:
            print(f"     🟡 Akurasi sedang ({pct:.0f}%). Hasil cukup bisa diandalkan")
        else:
            print(f"     🟢 Akurasi tinggi ({pct:.0f}%). Volume hampir final")
    print(f"\n  ⚠️  DISCLAIMER: Untuk edukasi. Bukan ajakan beli/jual. DYOR.")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():
    print("\n" + "=" * 70)
    print("  IDX STOCK SCREENER v1.0")
    print("  Berbasis ATR + Pivot + RSI + MACD + Volume + Bollinger")
    print("=" * 70)

    # Mode selection
    print("\n  Pilih mode:")
    print("  1. BSJP  (Beli Sore Jual Pagi)")
    print("  2. INTRADAY (Beli Pagi Jual Sore)")
    print("  3. KEDUA-DUANYA")

    choice = input("\n  Pilihan (1/2/3): ").strip()
    if choice == "1":
        modes = ["bsjp"]
    elif choice == "2":
        modes = ["intraday"]
    elif choice == "3":
        modes = ["bsjp", "intraday"]
    else:
        print("  Pilihan tidak valid. Menggunakan BSJP.")
        modes = ["bsjp"]

    # Stock selection
    print(f"\n  Pilih daftar saham:")
    print(f"  1. LQ45 ({len(LQ45)} saham) — Rekomendasi")
    print(f"  2. LQ45 + IDX80 ({len(LQ45) + len(IDX80_EXTRA)} saham)")
    print(f"  3. SEMUA termasuk SmallCap ({len(ALL_STOCKS)} saham)")
    print(f"  4. Input manual (ketik kode saham)")

    stock_choice = input("\n  Pilihan (1/2/3/4): ").strip()
    if stock_choice == "1":
        stocks = LQ45
    elif stock_choice == "2":
        stocks = LQ45 + IDX80_EXTRA
    elif stock_choice == "3":
        stocks = ALL_STOCKS
    elif stock_choice == "4":
        manual = input("  Ketik kode saham (pisah koma): ").strip().upper()
        stocks = [s.strip() for s in manual.split(",")]
    else:
        stocks = LQ45

    # Deteksi market hours untuk normalisasi volume
    market_progress = get_market_progress()
    if market_progress is not None:
        pct = market_progress * 100
        print(f"\n  📡 MARKET SEDANG BUKA — progress hari ini: {pct:.0f}%")
        print(f"     Volume akan dinormalisasi otomatis (estimasi full-day)")
        if market_progress < 0.30:
            print(f"     ⚠️  Baru {pct:.0f}% hari trading — estimasi volume kurang akurat")
            print(f"     Tip: Jalankan lagi nanti untuk hasil lebih akurat")
    else:
        print(f"\n  📴 Market tutup — data menggunakan closing terakhir")

    print(f"\n  Akan scan {len(stocks)} saham...")
    print(f"  Estimasi waktu: {len(stocks) * 2}-{len(stocks) * 4} detik\n")

    for mode in modes:
        print_header(mode, market_progress)

        results = []
        errors = []
        total = len(stocks)

        for i, ticker in enumerate(stocks, 1):
            progress = f"[{i}/{total}]"
            print(f"  {progress} Scanning {ticker}...", end="", flush=True)

            # Fetch data
            df = fetch_stock_data(ticker)
            if df is None:
                print(f" ⚠️ Data tidak tersedia")
                errors.append(ticker)
                continue

            # Calculate indicators
            try:
                data = calculate_indicators(df)
                data["ticker"] = ticker

                # Get market cap from yfinance info (suppress 404 errors)
                import logging
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

                # Normalisasi volume jika market masih buka
                normalize_volume(data, market_progress)

            except Exception as e:
                print(f" ❌ Error: {e}")
                errors.append(ticker)
                continue

            # Screen
            if mode == "bsjp":
                rules, rule_score, max_rules = screen_bsjp(data)
            else:
                rules, rule_score, max_rules = screen_intraday(data)

            # Quality score
            quality = calc_quality_score(data, mode)

            # Entry/SL/TP
            entry_data = calc_entry_sl_tp(data, mode)

            # Quick status
            if rule_score == max_rules:
                print(f" ⭐ PERFECT ({rule_score}/{max_rules}) Skor:{quality}")
            elif rule_score >= max_rules - 2:
                print(f" ✅ PASS ({rule_score}/{max_rules}) Skor:{quality}")
            elif rule_score >= max_rules - 3:
                print(f" 🟡 PARTIAL ({rule_score}/{max_rules})")
            else:
                print(f" ❌ FAIL ({rule_score}/{max_rules})")

            # Store result
            result = {
                "ticker": ticker,
                "data": data,
                "rules": rules,
                "rule_score": rule_score,
                "max_rules": max_rules,
                "quality": quality,
                "entry_data": entry_data,
            }
            results.append(result)

            time.sleep(0.5)  # Rate limiting

        # Print detailed results for passing stocks
        print(f"\n\n{'=' * 70}")
        print(f"  DETAIL HASIL — {'BSJP' if mode == 'bsjp' else 'INTRADAY'}")
        print(f"{'=' * 70}")

        display_results = []
        for r in results:
            if r["rule_score"] >= r["max_rules"] - 3:  # Show stocks that mostly pass
                res = print_stock_result(
                    r["ticker"], r["data"], r["rules"],
                    r["rule_score"], r["max_rules"],
                    r["quality"], r["entry_data"], mode
                )
                display_results.append(res)

        if not display_results:
            # Show top 5 even if they don't fully pass
            results.sort(key=lambda x: x["rule_score"], reverse=True)
            print(f"\n  Tidak ada yang lolos filter ketat. Menampilkan top 5 terdekat:\n")
            for r in results[:5]:
                res = print_stock_result(
                    r["ticker"], r["data"], r["rules"],
                    r["rule_score"], r["max_rules"],
                    r["quality"], r["entry_data"], mode
                )
                display_results.append(res)

        # Summary
        all_results = []
        for r in results:
            all_results.append({
                "ticker": r["ticker"],
                "close": r["data"]["close"],
                "pct_change": r["data"]["pct_change"],
                "rule_score": r["rule_score"],
                "max_rules": r["max_rules"],
                "quality": r["quality"],
                "status": "✅" if r["rule_score"] >= r["max_rules"] - 2 else "🟡" if r["rule_score"] >= r["max_rules"] - 3 else "❌",
                "q_label": "STRONG BUY" if r["quality"] >= 80 else "BUY" if r["quality"] >= 60 else "WATCH" if r["quality"] >= 40 else "SKIP",
                "entry_data": r["entry_data"],
                "pivot_s1": r["data"]["pivot_s1"],
                "pivot_s2": r["data"]["pivot_s2"],
            })

        print_summary(all_results, mode, market_progress)

        if errors:
            print(f"\n  ⚠️  Gagal fetch data: {', '.join(errors)}")

    print(f"\n  Selesai! 🎉\n")


if __name__ == "__main__":
    main()
