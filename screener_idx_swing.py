#!/usr/bin/env python3
"""
=================================================================
IDX SYARIAH STOCK SCREENER v3.0 — SWING TRADING
=================================================================
Screening saham Syariah Indonesia (JII / JII70 / ISSI)

Metode: Swing Trading (Stage Analysis + Fibonacci + Minervini SL)
1. Stage Analysis (Stan Weinstein) — fokus Stage 1→2 Breakout
2. Fibonacci Retracement — S/R + entry zone
3. MA50 Bounce / Breakout detection
4. Chart Pattern (Double Bottom, Inv H&S, Higher Low, Asc Triangle)
5. Minervini-style SL — di bawah pivot/swing low, max 8%
6. Max 5% alokasi per saham

Install: pip install yfinance pandas ta
Jalankan: python screener_idx_v3.py

Disclaimer: Untuk edukasi. Bukan ajakan beli/jual. DYOR.
=================================================================
"""

import sys, time, warnings
from datetime import datetime
warnings.filterwarnings("ignore")

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
except ImportError:
    print("INSTALL: pip install yfinance pandas numpy ta")
    sys.exit(1)

try:
    import ta
    USE_TA = True
except ImportError:
    USE_TA = False
    print("⚠️  pip install ta (untuk hasil lebih akurat)\n")


# ============================================================
# SAHAM SYARIAH — JII, JII70, ISSI Populer
# ============================================================

# JII (Jakarta Islamic Index) — 30 saham syariah paling likuid
JII = [
    "ADRO","AKRA","AMMN","AMRT","ANTM","ASII","BRPT","CPIN",
    "ESSA","EXCL","HRUM","ICBP","INCO","INDF","INKP","ISAT",
    "ITMG","KLBF","MAPI","MBMA","MDKA","MEDC","PGAS","PTBA",
    "SMGR","TBIG","TINS","TLKM","TPIA","UNTR",
]

# JII70 — Tambahan saham syariah likuid di luar JII
JII70_EXTRA = [
    "ACES","AGII","BSDE","CTRA","DSNG","ERAA","GJTL","GOTO",
    "INTP","JPFA","JSMR","KRAS","MNCN","PGEO","PWON","SCMA",
    "SIDO","SMDR","SRTG","TAPG","TKIM","TOWR","UNVR","WIKA",
]

# ISSI Populer — Saham syariah small-mid cap populer
ISSI_EXTRA = [
    "ALDO","ASSA","BEST","BUKA","CAMP","DSSA","EMTK","FILM",
    "GTRA","HEAL","KBLI","KIJA","LPPF","RALS","SKBM","TALF",
    "TRIS","ULTJ","WTON",
]

ALL_STOCKS = sorted(set(JII + JII70_EXTRA + ISSI_EXTRA))


# ============================================================
# MANUAL INDICATOR FALLBACKS
# ============================================================

def _ema(s, p): return s.ewm(span=p, adjust=False).mean()
def _sma(s, p): return s.rolling(window=p).mean()

def _rsi(c, p=14):
    d = c.diff(); g = d.where(d>0,0.0); l = -d.where(d<0,0.0)
    ag = g.ewm(alpha=1/p, min_periods=p).mean()
    al = l.ewm(alpha=1/p, min_periods=p).mean()
    return 100 - (100/(1+ag/al))

def _macd(c, f=12, s=26, sig=9):
    ml = _ema(c,f) - _ema(c,s); sl = _ema(ml,sig)
    return ml, sl, ml-sl

def _atr(h, l, c, p=14):
    tr = pd.concat([h-l, abs(h-c.shift(1)), abs(l-c.shift(1))], axis=1).max(axis=1)
    return tr.rolling(window=p).mean()

def _bb(c, p=20, sd=2):
    m = _sma(c,p); s = c.rolling(p).std()
    return m+sd*s, m, m-sd*s

def _adx(h, l, c, p=14):
    pdm = h.diff().where((h.diff()>-l.diff())&(h.diff()>0),0.0)
    ndm = (-l.diff()).where((-l.diff()>h.diff())&(-l.diff()>0),0.0)
    atr = _atr(h,l,c,p)
    pdi = 100*_ema(pdm,p)/atr; ndi = 100*_ema(ndm,p)/atr
    dx = 100*abs(pdi-ndi)/(pdi+ndi)
    return _ema(dx,p), pdi, ndi

def _stoch(h, l, c, kp=14, dp=3):
    ll = l.rolling(kp).min(); hh = h.rolling(kp).max()
    k = 100*(c-ll)/(hh-ll)
    return k, k.rolling(dp).mean()

def _mfi(h, l, c, v, p=14):
    tp = (h+l+c)/3; rmf = tp*v; d = tp.diff()
    pf = rmf.where(d>0,0.0).rolling(p).sum()
    nf = rmf.where(d<0,0.0).rolling(p).sum()
    return 100-(100/(1+pf/nf))


# ============================================================
# SUPPORT / RESISTANCE FINDER (Metode Teknikal)
# ============================================================

def find_swing_highs(high, window=10):
    """Cari swing high (puncak lokal) dalam data"""
    highs = []
    arr = high.values
    for i in range(window, len(arr) - window):
        if arr[i] == max(arr[i-window:i+window+1]):
            highs.append({"idx": i, "price": arr[i], "date": high.index[i]})
    return highs

def find_swing_lows(low, window=10):
    """Cari swing low (lembah lokal) dalam data"""
    lows = []
    arr = low.values
    for i in range(window, len(arr) - window):
        if arr[i] == min(arr[i-window:i+window+1]):
            lows.append({"idx": i, "price": arr[i], "date": low.index[i]})
    return lows

def find_support_resistance(high, low, close, window=10):
    """
    Cari Support & Resistance horizontal terdekat
    Metode: dari swing highs & swing lows
    """
    current = close.iloc[-1]
    s_highs = find_swing_highs(high, window)
    s_lows = find_swing_lows(low, window)

    # Resistance = swing highs DI ATAS harga saat ini
    resistances = sorted([h["price"] for h in s_highs if h["price"] > current * 1.02])
    # Support = swing lows DI BAWAH harga saat ini
    supports = sorted([l["price"] for l in s_lows if l["price"] < current * 0.98], reverse=True)

    r1 = resistances[0] if resistances else current * 1.10
    r2 = resistances[1] if len(resistances) > 1 else current * 1.20
    s1 = supports[0] if supports else current * 0.92
    s2 = supports[1] if len(supports) > 1 else current * 0.85

    return {"s2": s2, "s1": s1, "r1": r1, "r2": r2}


# ============================================================
# CHART PATTERN DETECTION (Konfirmasi Breakout)
# ============================================================

def detect_chart_patterns(high, low, close, window=5):
    """
    Deteksi chart pattern untuk konfirmasi breakout:
    - Double Bottom (W): Dua lembah di level mirip, lalu naik
    - Inverse Head & Shoulders: Tiga lembah, tengah paling dalam
    - Higher Low: Lembah terakhir lebih tinggi dari sebelumnya
    """
    patterns = []
    swing_lows = find_swing_lows(low, window)

    if len(swing_lows) < 2:
        return {"patterns": patterns, "has_pattern": False, "label": ""}

    # Ambil 3-4 swing low terakhir
    recent = swing_lows[-4:] if len(swing_lows) >= 4 else swing_lows
    prices = [s["price"] for s in recent]
    current = close.iloc[-1]

    # === DOUBLE BOTTOM (W pattern) ===
    # Dua swing low terakhir di level mirip (selisih < 3%), lalu harga naik
    if len(prices) >= 2:
        l1, l2 = prices[-2], prices[-1]
        diff_pct = abs(l1 - l2) / min(l1, l2) * 100
        if diff_pct < 3 and current > max(l1, l2) * 1.03:
            patterns.append("Double Bottom (W) ✅")

    # === INVERSE HEAD & SHOULDERS ===
    # 3 swing low: kiri & kanan mirip, tengah lebih rendah
    if len(prices) >= 3:
        left, head, right = prices[-3], prices[-2], prices[-1]
        # Head lebih rendah dari kedua shoulder
        if head < left * 0.97 and head < right * 0.97:
            # Shoulders mirip level (selisih < 5%)
            shoulder_diff = abs(left - right) / min(left, right) * 100
            if shoulder_diff < 5 and current > max(left, right) * 1.02:
                patterns.append("Inv. Head & Shoulders ✅")

    # === HIGHER LOW (Uptrend confirmation) ===
    if len(prices) >= 2:
        if prices[-1] > prices[-2]:
            patterns.append("Higher Low ✅")

    # === ASCENDING TRIANGLE ===
    # Higher lows + resistance di level mirip
    swing_highs = find_swing_highs(high, window)
    if len(swing_highs) >= 2 and len(prices) >= 2:
        h_prices = [s["price"] for s in swing_highs[-3:]]
        # Highs di level mirip (flat resistance)
        if len(h_prices) >= 2:
            h_diff = abs(h_prices[-1] - h_prices[-2]) / min(h_prices[-1], h_prices[-2]) * 100
            if h_diff < 3 and prices[-1] > prices[-2]:
                patterns.append("Ascending Triangle ✅")

    has = len(patterns) > 0
    label = " + ".join(patterns) if patterns else "Tidak ada pattern"

    return {
        "patterns": patterns,
        "has_pattern": has,
        "label": label,
    }


# ============================================================
# FIBONACCI RETRACEMENT
# ============================================================

def calc_fibonacci(high, low, close, lookback=60):
    """
    Hitung Fibonacci Retracement dari swing high/low terakhir.
    Seperti di chart: 0 (high), 0.236, 0.382, 0.5, 0.618, 0.786, 1 (low)

    Jika harga dalam uptrend (close > midpoint), Fib dihitung dari
    swing low ke swing high (retrace ke bawah).
    """
    h_arr = high.iloc[-lookback:]
    l_arr = low.iloc[-lookback:]

    swing_high = h_arr.max()
    swing_low = l_arr.min()
    current = close.iloc[-1]

    diff = swing_high - swing_low
    if diff <= 0:
        return None

    # Fib levels (retrace dari high ke low)
    levels = {
        "0": swing_high,                       # 0% retracement = high
        "0.236": swing_high - 0.236 * diff,
        "0.382": swing_high - 0.382 * diff,
        "0.5": swing_high - 0.5 * diff,
        "0.618": swing_high - 0.618 * diff,
        "0.786": swing_high - 0.786 * diff,
        "1": swing_low,                        # 100% retracement = low
    }

    # Cari level Fib terdekat di bawah harga (support)
    fib_support = None
    fib_support_name = ""
    for name in ["0.382", "0.5", "0.618", "0.786", "1"]:
        if levels[name] < current:
            fib_support = levels[name]
            fib_support_name = name
            break

    # Cari level Fib terdekat di atas harga (resistance)
    fib_resist = None
    fib_resist_name = ""
    for name in ["0.618", "0.5", "0.382", "0.236", "0"]:
        if levels[name] > current:
            fib_resist = levels[name]
            fib_resist_name = name
            break

    # Apakah harga dekat Fib level? (dalam 2%)
    near_fib = False
    near_fib_level = ""
    for name, price in levels.items():
        if abs(current - price) / current < 0.02:
            near_fib = True
            near_fib_level = name
            break

    return {
        "levels": levels,
        "swing_high": swing_high,
        "swing_low": swing_low,
        "fib_support": fib_support,
        "fib_support_name": fib_support_name,
        "fib_resist": fib_resist,
        "fib_resist_name": fib_resist_name,
        "near_fib": near_fib,
        "near_fib_level": near_fib_level,
    }


# ============================================================
# STAGE ANALYSIS (Stage Analysis / Stan Weinstein)
# ============================================================

def detect_stage(close, ma50, ma200=None):
    """
    Stage Analysis (Stan Weinstein):
    Stage 1:   Basing (sideways, MA50 flat, close < MA50)
    Stage 1→2: BREAKOUT — baru breakout dari base ← PELUANG TERBAIK
    Stage 2:   Advancing (uptrend lanjutan, sudah jauh di atas MA50)
    Stage 3:   Topping (mulai flat di puncak)
    Stage 4:   Declining (downtrend) ← HINDARI
    """
    current = close.iloc[-1]
    ma50_now = ma50.iloc[-1]
    ma50_20ago = ma50.iloc[-20] if len(ma50) >= 20 else ma50.iloc[0]
    ma50_slope = (ma50_now - ma50_20ago) / ma50_20ago * 100

    dist_pct = (current - ma50_now) / ma50_now * 100

    # === DETEKSI TRANSISI Stage 1→2 (BREAKOUT) ===
    # Kriteria breakout dari base:
    # 1. Close BARU saja di atas MA50 (dalam 10 hari terakhir)
    # 2. Sebelumnya close di bawah atau dekat MA50 (base/accumulation)
    # 3. MA50 mulai berubah arah (flat → naik)
    # 4. Volume meningkat sebagai konfirmasi

    # Cek apakah close baru menembus MA50 dalam 10 hari terakhir
    recently_crossed = False
    days_above = 0
    if len(close) >= 15 and len(ma50) >= 15:
        for i in range(-10, 0):
            if close.iloc[i] > ma50.iloc[i]:
                days_above += 1
        # 10-15 hari lalu masih di bawah/dekat MA50
        was_below = any(
            close.iloc[j] <= ma50.iloc[j] * 1.01
            for j in range(-15, -8)
        )
        recently_crossed = was_below and current > ma50_now

    # MA50 baru mulai naik (slope 0 s/d 2% = baru berbelok)
    ma50_turning_up = -0.5 <= ma50_slope <= 2.5

    # Close dekat MA50 (belum jauh, masih awal breakout)
    close_near_ma50 = 0 < dist_pct < 8

    # TRANSISI Stage 1→2: Breakout dari base
    is_breakout = recently_crossed and ma50_turning_up and close_near_ma50

    if is_breakout:
        stage = 12  # 12 = Stage 1→2
        label = "Stage 1→2 BREAKOUT 🚀"
        desc = "Baru breakout dari base! PELUANG TERBAIK."
    elif current > ma50_now and ma50_slope > 2.5 and dist_pct > 8:
        # Sudah jauh di atas MA50, uptrend lanjutan
        stage = 2
        label = "Stage 2 — ADVANCING (lanjutan) ✅"
        desc = "Uptrend lanjutan. Sudah naik jauh dari base."
    elif current > ma50_now and ma50_slope > 1.0:
        # Di atas MA50, MA50 naik — early Stage 2
        stage = 2
        label = "Stage 2 — ADVANCING ✅"
        desc = "Uptrend. MA50 naik."
    elif current > ma50_now and -1.0 <= ma50_slope <= 1.0:
        stage = 3
        label = "Stage 3 — TOPPING ⚠️"
        desc = "Di puncak. MA50 mulai flat. HATI-HATI."
    elif current < ma50_now and ma50_slope < -1.0:
        stage = 4
        label = "Stage 4 — DECLINING ❌"
        desc = "Downtrend. MA50 turun. HINDARI."
    elif current < ma50_now and ma50_slope >= -1.0:
        stage = 1
        label = "Stage 1 — BASING 🔄"
        desc = "Bottoming/accumulation. TUNGGU breakout."
    else:
        stage = 0
        label = "Tidak teridentifikasi"
        desc = ""

    return {
        "stage": stage,
        "label": label,
        "desc": desc,
        "ma50_slope": ma50_slope,
        "dist_to_ma50": dist_pct,
        "is_breakout": is_breakout,
        "days_above_ma50": days_above,
    }


# ============================================================
# MA50 BOUNCE DETECTION (Kunci metode MA50 Bounce)
# ============================================================

def detect_ma50_bounce(df, ma50):
    """
    Deteksi apakah harga baru memantul dari MA50
    Seperti pada contoh KRAS:
    - Harga turun mendekati MA50
    - Menyentuh/dekat MA50
    - Lalu mulai naik kembali
    """
    close = df["Close"]
    low = df["Low"]
    high = df["High"]

    current_close = close.iloc[-1]
    current_ma50 = ma50.iloc[-1]

    # Cek 5 hari terakhir: apakah low menyentuh/dekat MA50
    lows_5d = low.iloc[-5:]
    ma50_5d = ma50.iloc[-5:]

    # Toleransi: low dalam 2% dari MA50
    touched_ma50 = any(
        abs(lows_5d.iloc[i] - ma50_5d.iloc[i]) / ma50_5d.iloc[i] < 0.02
        for i in range(len(lows_5d))
    )

    # Low pernah di bawah MA50 lalu close kembali di atas
    dipped_below = any(lows_5d.iloc[i] < ma50_5d.iloc[i] for i in range(len(lows_5d)))
    recovered = current_close > current_ma50

    # Harga sekarang dekat MA50 (dalam 3%)
    near_ma50 = abs(current_close - current_ma50) / current_ma50 < 0.03

    # Candle terakhir bullish (close > open)
    last_bullish = close.iloc[-1] > df["Open"].iloc[-1]

    bounce_detected = (touched_ma50 or dipped_below) and recovered and last_bullish
    near_bounce = near_ma50 and recovered

    return {
        "bounce": bounce_detected,
        "near_bounce": near_bounce,
        "touched_ma50": touched_ma50,
        "dipped_below": dipped_below,
        "recovered": recovered,
        "last_bullish": last_bullish,
        "dist_to_ma50_pct": ((current_close - current_ma50) / current_ma50) * 100,
    }


# ============================================================
# FETCH & CALCULATE
# ============================================================

def fetch_data(ticker, period="1y"):
    """1 tahun data untuk S/R historis dan Stage Analysis"""
    try:
        df = yf.Ticker(f"{ticker}.JK").history(period=period)
        if df.empty or len(df) < 60:
            return None
        return df
    except:
        return None


def calc_all(df, ticker=""):
    """Hitung semua indikator + metode teknikal"""
    c, h, l, v, o = df["Close"], df["High"], df["Low"], df["Volume"], df["Open"]
    last = len(df) - 1

    if USE_TA:
        ema9 = ta.trend.ema_indicator(c, 9)
        ema20 = ta.trend.ema_indicator(c, 20)
        ma50 = ta.trend.sma_indicator(c, 50)  # SMA50 untuk swing analysis
        ma200 = ta.trend.sma_indicator(c, 200) if len(df) >= 200 else _sma(c, min(len(df)-1,200))
        rsi = ta.momentum.rsi(c, 14)
        macd = ta.trend.MACD(c)
        ml, ms, mh = macd.macd(), macd.macd_signal(), macd.macd_diff()
        atr = ta.volatility.average_true_range(h, l, c, 14)
        bb = ta.volatility.BollingerBands(c, 20, 2)
        bbu, bbl, bbm = bb.bollinger_hband(), bb.bollinger_lband(), bb.bollinger_mavg()
        adx_val = ta.trend.adx(h, l, c, 14)
        st = ta.momentum.StochasticOscillator(h, l, c)
        sk, sd = st.stoch(), st.stoch_signal()
        mfi = ta.volume.money_flow_index(h, l, c, v, 14)
    else:
        ema9 = _ema(c,9); ema20 = _ema(c,20)
        ma50 = _sma(c,50)  # SMA50
        ma200 = _sma(c,min(len(df)-1,200))
        rsi = _rsi(c); ml, ms, mh = _macd(c)
        atr = _atr(h,l,c)
        bbu, bbm, bbl = _bb(c)
        adx_val, _, _ = _adx(h,l,c)
        sk, sd = _stoch(h,l,c)
        mfi = _mfi(h,l,c,v)

    # Basic data
    d = {
        "ticker": ticker,
        "close": c.iloc[last], "open": o.iloc[last],
        "high": h.iloc[last], "low": l.iloc[last],
        "prev_close": c.iloc[last-1],
        "volume": v.iloc[last],
        "avg_vol_20d": v.iloc[-20:].mean(),
        "ema9": ema9.iloc[last], "ema20": ema20.iloc[last],
        "ma50": ma50.iloc[last],
        "ma200": ma200.iloc[last] if not pd.isna(ma200.iloc[last]) else ma50.iloc[last],
        "rsi": rsi.iloc[last],
        "macd_line": ml.iloc[last], "macd_signal": ms.iloc[last],
        "macd_hist": mh.iloc[last],
        "atr": atr.iloc[last],
        "bb_upper": bbu.iloc[last], "bb_middle": bbm.iloc[last], "bb_lower": bbl.iloc[last],
        "adx": adx_val.iloc[last],
        "stoch_k": sk.iloc[last], "stoch_d": sd.iloc[last],
        "mfi": mfi.iloc[last],
    }

    # Derived
    d["pct_change"] = ((d["close"]-d["prev_close"])/d["prev_close"])*100
    d["vol_ratio"] = d["volume"]/d["avg_vol_20d"] if d["avg_vol_20d"]>0 else 0
    bb_rng = d["bb_upper"]-d["bb_lower"]
    d["bb_pctb"] = (d["close"]-d["bb_lower"])/bb_rng if bb_rng>0 else 0.5
    d["bb_bw"] = (bb_rng/d["bb_middle"])*100 if d["bb_middle"]>0 else 0
    d["atr_pct"] = (d["atr"]/d["close"])*100

    # Historical volatility (20-day rolling stdev of daily returns, in %)
    daily_returns = c.pct_change().dropna()
    d["hist_vol_20d"] = float(daily_returns.iloc[-20:].std() * 100) if len(daily_returns) >= 20 else 0.0
    # Bollinger Band width as volatility proxy
    d["bb_width"] = d["bb_bw"]  # already calculated above
    # Volatility label for frontend
    atr_p = d["atr_pct"]
    if atr_p <= 2.5:
        d["vol_label"] = "RENDAH"
    elif atr_p <= 4.0:
        d["vol_label"] = "NORMAL"
    elif atr_p <= 5.5:
        d["vol_label"] = "TINGGI"
    else:
        d["vol_label"] = "EXTREME"

    # Market cap (suppress 404 errors)
    import logging
    _yf_log = logging.getLogger("yfinance")
    _prev = _yf_log.level
    _yf_log.setLevel(logging.CRITICAL)
    try:
        info = yf.Ticker(f"{ticker}.JK").info
        d["mcap_t"] = info.get("marketCap", 0) / 1e12
    except:
        d["mcap_t"] = 0
    finally:
        _yf_log.setLevel(_prev)
    d["value_b"] = (d["close"]*d["volume"])/1e9

    # === SWING ANALYSIS ===

    # 1. Support/Resistance horizontal
    sr = find_support_resistance(h, l, c, window=10)
    d["sr_s1"] = sr["s1"]; d["sr_s2"] = sr["s2"]
    d["sr_r1"] = sr["r1"]; d["sr_r2"] = sr["r2"]

    # 2. Stage Analysis
    stage = detect_stage(c, ma50)
    d["stage"] = stage["stage"]
    d["stage_label"] = stage["label"]
    d["stage_desc"] = stage["desc"]
    d["ma50_slope"] = stage["ma50_slope"]
    d["dist_to_ma50"] = stage["dist_to_ma50"]
    d["is_breakout"] = stage.get("is_breakout", False)
    d["days_above_ma50"] = stage.get("days_above_ma50", 0)

    # 3. MA50 Bounce Detection
    bounce = detect_ma50_bounce(df, ma50)
    d["ma50_bounce"] = bounce["bounce"]
    d["ma50_near"] = bounce["near_bounce"]
    d["ma50_touched"] = bounce["touched_ma50"]
    d["ma50_dipped"] = bounce["dipped_below"]
    d["ma50_recovered"] = bounce["recovered"]
    d["last_bullish"] = bounce["last_bullish"]
    d["dist_ma50_pct"] = bounce["dist_to_ma50_pct"]

    # 4. Swing low terakhir (untuk SL)
    swing_lows = find_swing_lows(l, window=5)
    recent_lows = [sl for sl in swing_lows if sl["idx"] > len(df) - 40]  # 40 hari terakhir
    d["recent_swing_low"] = recent_lows[-1]["price"] if recent_lows else l.iloc[-20:].min()

    # 5. Chart Pattern Detection (konfirmasi breakout)
    patterns = detect_chart_patterns(h, l, c, window=5)
    d["chart_pattern"] = patterns["label"]
    d["has_pattern"] = patterns["has_pattern"]
    d["pattern_list"] = patterns["patterns"]

    # 6. High 20 hari (untuk context)
    d["high_20d"] = h.iloc[-20:].max()
    d["low_20d"] = l.iloc[-20:].min()

    # 6. Fibonacci Retracement
    fib = calc_fibonacci(h, l, c, lookback=60)
    if fib:
        d["fib_levels"] = fib["levels"]
        d["fib_swing_high"] = fib["swing_high"]
        d["fib_swing_low"] = fib["swing_low"]
        d["fib_0"] = fib["levels"]["0"]
        d["fib_0236"] = fib["levels"]["0.236"]
        d["fib_0382"] = fib["levels"]["0.382"]
        d["fib_05"] = fib["levels"]["0.5"]
        d["fib_0618"] = fib["levels"]["0.618"]
        d["fib_0786"] = fib["levels"]["0.786"]
        d["fib_1"] = fib["levels"]["1"]
        d["fib_support"] = fib["fib_support"]
        d["fib_support_name"] = fib["fib_support_name"]
        d["fib_resist"] = fib["fib_resist"]
        d["fib_resist_name"] = fib["fib_resist_name"]
        d["fib_near"] = fib["near_fib"]
        d["fib_near_level"] = fib["near_fib_level"]
    else:
        d["fib_levels"] = {}
        d["fib_swing_high"] = d["fib_swing_low"] = 0
        d["fib_0"] = d["fib_0236"] = d["fib_0382"] = 0
        d["fib_05"] = d["fib_0618"] = d["fib_0786"] = d["fib_1"] = 0
        d["fib_support"] = d["fib_resist"] = None
        d["fib_support_name"] = d["fib_resist_name"] = ""
        d["fib_near"] = False
        d["fib_near_level"] = ""

    return d


# ============================================================
# SCREENING: SWING TRADING METHOD
# ============================================================

def screen_swing(d):
    """
    Screening fokus Stage 1→2 BREAKOUT:
    Peluang terbaik = saham yang BARU breakout dari base (Stage 1→2)
    Juga terima early Stage 2 yang masih dekat MA50
    """
    is_brk = d.get("is_breakout", False)
    stg = d["stage"]

    rules = [
        # === UTAMA: Stage 1→2 Breakout atau Early Stage 2 ===
        ("Stage 1→2 Breakout ATAU Early Stage 2",
         stg in (12, 2),
         d["stage_label"]),

        ("Close > MA50 (baru menembus atau di atas)",
         d["close"] > d["ma50"],
         f"{d['close']:.0f} vs MA50:{d['ma50']:.0f}"),

        ("MA50 mulai naik (slope > -0.5%)",
         d["ma50_slope"] > -0.5,
         f"Slope: {d['ma50_slope']:+.1f}%"),

        # === KONFIRMASI BREAKOUT ===
        ("Breakout / Bounce dari MA50",
         is_brk or d["ma50_bounce"] or d["ma50_near"],
         f"{'BREAKOUT 🚀' if is_brk else 'BOUNCE ✅' if d['ma50_bounce'] else 'DEKAT' if d['ma50_near'] else 'TIDAK'}"),

        ("Jarak ke MA50 < 8% (belum terlalu jauh)",
         0 <= d["dist_ma50_pct"] < 8,
         f"{d['dist_ma50_pct']:+.1f}%"),

        # === VOLUME KONFIRMASI (penting untuk breakout) ===
        ("Volume >= rata-rata (konfirmasi breakout)",
         d["vol_ratio"] >= 0.8,
         f"{d['vol_ratio']:.1f}x avg"),

        ("Candle terakhir bullish (Close > Open)",
         d["last_bullish"],
         f"{'Bullish ✅' if d['last_bullish'] else 'Bearish ❌'}"),

        # === MOMENTUM (building, belum overbought) ===
        ("RSI 35-65 (momentum building)",
         35 <= d["rsi"] <= 65,
         f"{d['rsi']:.1f}"),

        ("MFI > 35 (uang masuk)",
         d["mfi"] > 35,
         f"{d['mfi']:.1f}"),

        ("ADX > 15 (tren mulai terbentuk)",
         d["adx"] > 15,
         f"{d['adx']:.1f}"),

        # === LIKUIDITAS ===
        ("Avg Vol > 5jt (likuid, spread aman)",
         d["avg_vol_20d"] > 5_000_000,
         f"{d['avg_vol_20d']/1e6:.1f}jt"),

        # === ANTI-JEBAKAN ===
        ("Stoch %K < 85 (belum extreme overbought)",
         d["stoch_k"] < 85,
         f"{d['stoch_k']:.1f}"),

        ("Bukan Stage 3/4 (hindari topping/declining)",
         stg not in (3, 4),
         f"Stage {stg}" if stg in (3,4) else "OK ✅"),

        # === FILTER TAMBAHAN ===
        ("Market Cap ≥ 5T (hindari saham gorengan)",
         d.get("mcap_t", 0) >= 5,
         f"{d.get('mcap_t', 0):.1f}T"),

        ("Change -3% to +4% (bukan pump/crash)",
         -3 <= d["pct_change"] <= 4,
         f"{d['pct_change']:+.1f}%"),

        # === VOLATILITAS ===
        ("Volatilitas terkendali (ATR% ≤ 4.5%)",
         d["atr_pct"] <= 4.5,
         f"{d['atr_pct']:.1f}% [{d.get('vol_label', '')}]"),
    ]

    results = []; score = 0
    for name, passed, val in rules:
        results.append({"rule": name, "pass": passed, "value": val})
        if passed: score += 1
    return results, score, len(rules)


def calc_entry_swing(d):
    """
    Entry/SL/TP dengan Fibonacci + S/R confluence (Minervini-style SL):
    - Entry: Zona Fib 0.382-0.5 confluence dengan Support/MA50
    - SL: Di bawah swing low/pivot terdekat, CAP max 10%
      → Prefer tight SL (terdekat entry), bukan terjauh
      → Jika swing low terlalu jauh (>10%), cap di 10%
    - R1: Resistance horizontal / Fib 0.236
    - R2: Resistance horizontal / Fib 0
    - Max alokasi: 5% modal
    """
    close = d["close"]
    ma50 = d["ma50"]
    sr_s1 = d["sr_s1"]
    sr_r1 = d["sr_r1"]
    sr_r2 = d["sr_r2"]
    swing_low = d["recent_swing_low"]

    fib_0382 = d.get("fib_0382", 0)
    fib_05 = d.get("fib_05", 0)
    fib_0618 = d.get("fib_0618", 0)
    fib_support = d.get("fib_support")
    fib_resist = d.get("fib_resist")

    # === ENTRY ZONE (Fibonacci + S/R confluence) ===
    # Batas bawah: Fib support terdekat atau S/R support atau MA50
    candidates_low = [x for x in [fib_0382, fib_05, sr_s1, ma50 * 0.99] if x > 0 and x < close]
    entry_low = max(candidates_low) if candidates_low else close * 0.97

    # Batas atas: close saat ini
    entry_high = close
    entry_mid = (entry_low + entry_high) / 2

    # Entry basis description
    entry_basis_parts = []
    if fib_support and abs(entry_low - fib_support) / close < 0.03:
        entry_basis_parts.append(f"Fib {d.get('fib_support_name','')}")
    if abs(entry_low - sr_s1) / close < 0.03:
        entry_basis_parts.append("S/R horizontal")
    if abs(entry_low - ma50) / close < 0.03:
        entry_basis_parts.append("MA50")
    entry_basis = " + ".join(entry_basis_parts) if entry_basis_parts else "Support zone"

    # === SL: Multiple candidates, pick tightest (closest to entry) ===
    MAX_SL_PCT = 0.06  # 6% max stop-loss cap (ketat untuk swing)

    # Multiple SL candidates — prefer tightest (Minervini style)
    sl_candidates = []

    # 1. Swing low - 2% buffer
    if swing_low > 0:
        sl_candidates.append(("Swing low", swing_low * 0.98))

    # 2. Fib 0.618 - 2% buffer
    if fib_0618 > 0 and fib_0618 < entry_low:
        sl_candidates.append(("Fib 0.618", fib_0618 * 0.98))

    # 3. S/R Support (sr_s1) - 1% buffer
    if sr_s1 > 0 and sr_s1 < entry_low:
        sl_candidates.append(("Support S1", sr_s1 * 0.99))

    # 4. MA50 - 2% buffer
    if ma50 > 0 and ma50 < entry_low:
        sl_candidates.append(("MA50", ma50 * 0.98))

    # 5. ATR-based fallback: entry - 1.5×ATR
    sl_candidates.append(("ATR 1.5x", entry_low - (d["atr"] * 1.5)))

    # Filter: only candidates below entry
    valid_sl = [(name, val) for name, val in sl_candidates if val < entry_low and val > 0]

    if valid_sl:
        # Pick tightest (closest to entry = highest value)
        sl_name, sl = max(valid_sl, key=lambda x: x[1])
    else:
        sl_name = "ATR fallback"
        sl = entry_low - (d["atr"] * 1.5)

    # Cap SL max 10% dari entry
    sl_floor = entry_mid * (1 - MAX_SL_PCT)
    sl_capped = False
    if sl < sl_floor:
        sl = sl_floor
        sl_capped = True

    # SL basis description
    if sl_capped:
        sl_basis = f"Max SL 6% cap"
    else:
        sl_basis = f"{sl_name} ({sl:.0f})"

    # === TP: Resistance horizontal + Fibonacci ===
    # Minimum TP distance: at least 3% or 2×ATR from entry (whichever is bigger)
    min_tp1_dist = max(entry_mid * 0.03, d["atr"] * 2)
    min_tp2_dist = max(entry_mid * 0.06, d["atr"] * 4)

    tp1 = sr_r1
    tp1_basis = "Resistance 1 (horizontal)"
    # Jika Fib resistance dekat R1, gunakan yang lebih akurat
    if fib_resist and fib_resist > entry_mid:
        if abs(fib_resist - sr_r1) / close < 0.05:
            tp1_basis = f"R1 + Fib {d.get('fib_resist_name','')}"
        elif fib_resist < sr_r1:
            tp1 = fib_resist
            tp1_basis = f"Fib {d.get('fib_resist_name','')}"

    tp2 = sr_r2
    tp2_basis = "Resistance 2 (horizontal)"

    # TP1 must be at least min_tp1_dist above entry
    if tp1 < entry_mid + min_tp1_dist:
        tp1 = entry_mid + min_tp1_dist
        tp1_basis = "Entry + min 3%/2×ATR"
    # TP2 must be at least min_tp2_dist above entry and above TP1
    if tp2 < entry_mid + min_tp2_dist or tp2 <= tp1:
        tp2 = entry_mid + min_tp2_dist
        tp2_basis = "Entry + min 6%/4×ATR"

    risk = entry_mid - sl
    rr1 = (tp1 - entry_mid) / risk if risk > 0 else 0
    rr2 = (tp2 - entry_mid) / risk if risk > 0 else 0

    return {
        "entry_low": entry_low,
        "entry_high": entry_high,
        "entry_mid": entry_mid,
        "entry_basis": entry_basis,
        "sl": sl,
        "sl_basis": sl_basis,
        "tp1": tp1,
        "tp1_basis": tp1_basis,
        "tp2": tp2,
        "tp2_basis": tp2_basis,
        "risk": risk,
        "rr1": rr1,
        "rr2": rr2,
        "entry_pct": ((entry_mid - close) / close) * 100,
        "sl_pct": ((sl - entry_mid) / entry_mid) * 100,
        "tp1_pct": ((tp1 - entry_mid) / entry_mid) * 100,
        "tp2_pct": ((tp2 - entry_mid) / entry_mid) * 100,
        "max_alloc": "5%",
        "hold_short": "Jangka pendek (minggu, target R1)",
        "hold_medium": "Jangka menengah (3-6 bulan, target R2)",
    }




# ============================================================
# QUALITY SCORE
# ============================================================

def calc_score(d):
    s = 0
    # Stage breakout bonus (30%) — Stage 1→2 paling tinggi
    if d["stage"] == 12: s += 30    # BREAKOUT = skor tertinggi
    elif d["stage"] == 2: s += 20   # Stage 2 lanjutan
    elif d["stage"] == 1: s += 5    # Masih base, tunggu
    # MA50 bounce / breakout (20%)
    if d.get("is_breakout"): s += 20
    elif d["ma50_bounce"]: s += 20
    elif d["ma50_near"]: s += 12
    # RSI sweet spot (15%)
    if 40 <= d["rsi"] <= 55: s += 15
    elif 35 <= d["rsi"] <= 65: s += 8
    # Volume (10%)
    if d["vol_ratio"] > 1.5: s += 10
    elif d["vol_ratio"] > 1: s += 5
    # MFI (10%)
    if d["mfi"] > 50: s += 10
    elif d["mfi"] > 35: s += 5
    # MACD direction (5%)
    if d["macd_hist"] > 0 and d["macd_line"] > d["macd_signal"]: s += 5
    elif d["macd_hist"] > 0: s += 3
    # Chart Pattern bonus (10%) — Double Bottom, Inv H&S, etc
    if d.get("has_pattern"):
        pattern_count = len(d.get("pattern_list", []))
        if pattern_count >= 2: s += 10
        else: s += 7
    # Volatility adjustment — prefer calm stocks for swing
    atr_p = d.get("atr_pct", 0)
    if atr_p <= 2.5: s += 8       # Very stable = bonus
    elif atr_p <= 3.5: s += 4     # Normal = small bonus
    elif atr_p > 5.5: s -= 15     # Extreme = heavy penalty
    elif atr_p > 4.5: s -= 8      # High = penalty
    return max(0, min(s, 100))


# ============================================================
# DISPLAY
# ============================================================

MODE_NAME = "SWING TRADING (Stage 1→2 Breakout + Fibonacci + Minervini SL)"

def display_result(ticker, d, rules, rs, mx, quality, entry):
    if rs >= mx-1: status = "⭐ STRONG"
    elif rs >= mx-2: status = "✅ GOOD"
    elif rs >= mx-3: status = "🟡 MODERATE"
    elif rs >= mx-4: status = "🟠 WEAK"
    else: status = "❌ FAIL"

    ql = "STRONG BUY" if quality>=75 else "BUY" if quality>=55 else "WATCH" if quality>=35 else "SKIP"

    print(f"\n{'━'*70}")
    print(f"  {ticker}  |  Rp {d['close']:,.0f}  ({d['pct_change']:+.1f}%)")
    print(f"  {status}  |  Skor: {quality}/100  [{ql}]  |  Rules: {rs}/{mx}")
    print(f"  {d['stage_label']}")
    print(f"{'━'*70}")

    # Rules
    for r in rules:
        icon = "✅" if r["pass"] else "❌"
        print(f"  {icon} {r['rule']:.<45s} {r['value']}")

    fails = [r["rule"] for r in rules if not r["pass"]]
    if fails:
        print(f"\n  ⚠️  Gagal: {', '.join(fails[:3])}")

    # Entry/SL/TP
    if rs >= mx - 4:
        e = entry
        print(f"\n  {'─'*55}")

        print(f"  📊 SWING ANALYSIS (Stage + Fibonacci + Pattern)")
        print(f"     {d['stage_label']}")
        print(f"     MA50: {d['ma50']:,.0f}  |  Jarak: {d['dist_ma50_pct']:+.1f}%  |  Slope: {d['ma50_slope']:+.1f}%")
        if d.get("is_breakout"):
            print(f"     🚀 BREAKOUT Stage 1→2 terdeteksi! ({d.get('days_above_ma50',0)} hari di atas MA50)")
        else:
            print(f"     MA50 Bounce: {'✅ YA' if d['ma50_bounce'] else '🟡 Dekat' if d['ma50_near'] else '❌ Tidak'}")
        # Chart patterns
        if d.get("has_pattern"):
            print(f"     📈 Pattern: {d['chart_pattern']}")
        else:
            print(f"     📈 Pattern: Tidak ada pattern konfirmasi")

        # Fibonacci Levels Table
        print(f"\n  📐 FIBONACCI RETRACEMENT")
        print(f"     ┌────────┬──────────┬────────────────────┐")
        print(f"     │ Level  │   Harga  │ Keterangan         │")
        print(f"     ├────────┼──────────┼────────────────────┤")
        fib_data = [
            ("0",     d.get('fib_0',0),     "Swing High"),
            ("0.236", d.get('fib_0236',0),  ""),
            ("0.382", d.get('fib_0382',0),  "Golden Zone"),
            ("0.5",   d.get('fib_05',0),    "Mid Level"),
            ("0.618", d.get('fib_0618',0),  "Golden Ratio"),
            ("0.786", d.get('fib_0786',0),  "Deep Retrace"),
            ("1",     d.get('fib_1',0),     "Swing Low"),
        ]
        for lvl, price, desc in fib_data:
            if price > 0:
                marker = ""
                if abs(d['close'] - price) / d['close'] < 0.02:
                    marker = " ◄ HARGA"
                if d.get('fib_support') and abs(price - d['fib_support']) < 1:
                    desc = "SUPPORT ▲" if not marker else desc
                print(f"     │ {lvl:<6s} │ {price:>8,.0f} │ {desc:<18s} │{marker}")
        print(f"     └────────┴──────────┴────────────────────┘")

        # Support / Resistance / Entry Table
        eb = e.get('entry_basis', 'Support zone')[:22]
        slb = e['sl_basis'][:22]
        entry_mid = (e['entry_low'] + e['entry_high']) / 2
        pct_r1 = ((e['tp1'] - entry_mid) / entry_mid * 100) if entry_mid > 0 else 0
        pct_r2 = ((e['tp2'] - entry_mid) / entry_mid * 100) if entry_mid > 0 else 0
        pct_sl = ((e['sl'] - entry_mid) / entry_mid * 100) if entry_mid > 0 else 0
        print(f"\n  📊 SUPPORT / RESISTANCE / ENTRY")
        print(f"     ┌──────────┬──────────┬────────┬────────────────────────┐")
        print(f"     │ Level    │   Harga  │   %    │ Basis                  │")
        print(f"     ├──────────┼──────────┼────────┼────────────────────────┤")
        print(f"     │ R2 (TP2) │ {e['tp2']:>8,.0f} │ {pct_r2:>+5.1f}% │ {e['tp2_basis'][:22]:<22s} │")
        print(f"     │ R1 (TP1) │ {e['tp1']:>8,.0f} │ {pct_r1:>+5.1f}% │ {e['tp1_basis'][:22]:<22s} │")
        print(f"     ├──────────┼──────────┼────────┼────────────────────────┤")
        print(f"     │ Close    │ {d['close']:>8,.0f} │        │ Harga saat ini         │")
        print(f"     │ Entry ▲  │ {e['entry_high']:>8,.0f} │        │ Batas atas entry       │")
        print(f"     │ Entry ▼  │ {e['entry_low']:>8,.0f} │        │ {eb:<22s} │")
        print(f"     ├──────────┼──────────┼────────┼────────────────────────┤")
        print(f"     │ S        │ {d['sr_s1']:>8,.0f} │        │ Support horizontal     │")
        print(f"     │ SL       │ {e['sl']:>8,.0f} │ {pct_sl:>+5.1f}% │ {slb:<22s} │")
        print(f"     │ S2       │ {d['sr_s2']:>8,.0f} │        │ Support 2              │")
        print(f"     └──────────┴──────────┴────────┴────────────────────────┘")

        # === OUTPUT REKOMENDASI ===
        print(f"\n  🎯 REKOMENDASI")
        print(f"     ╔═══════════════════════════════════════════════╗")
        print(f"     ║  {ticker:<45s}  ║")
        print(f"     ║  Direkomendasi di {e['entry_low']:,.0f}-{e['entry_high']:,.0f}{' ':>16}║")
        print(f"     ║  Max {e['max_alloc']}{' ':>37}║")
        print(f"     ╠═══════════════════════════════════════════════╣")
        print(f"     ║  S : {d['sr_s1']:>8,.0f}  (Support){' ':>22}║")
        print(f"     ║  SL: {e['sl']:>8,.0f}  ({e['sl_pct']:+.1f}%){' ':>23}║")
        print(f"     ║  R1: {e['tp1']:>8,.0f}  ({e['tp1_pct']:+.1f}%) Jangka Pendek{' ':>9}║")
        print(f"     ║  R2: {e['tp2']:>8,.0f}  ({e['tp2_pct']:+.1f}%) Jangka Menengah{' ':>7}║")
        print(f"     ║  R:R  1:{e['rr1']:.1f} (R1) | 1:{e['rr2']:.1f} (R2){' ':>14}║")
        print(f"     ╚═══════════════════════════════════════════════╝")
        if e.get("entry_basis"):
            print(f"     Entry basis: {e['entry_basis']}")
        print(f"     SL basis  : {e['sl_basis']}")
        print(f"     TP1 basis : {e['tp1_basis']}")
        print(f"     TP2 basis : {e['tp2_basis']}")
        if e.get("hold_short"):
            print(f"     Hold      : {e['hold_short']}")
        if e.get("hold_medium"):
            print(f"                 {e['hold_medium']}")
        print(f"     ATR       : Rp {d['atr']:,.0f} ({d['atr_pct']:.1f}%)")

        if e["rr1"] < 1.5:
            print(f"\n     ⚠️  R:R < 1.5 untuk TP1 — pertimbangkan skip")
        if e["rr2"] >= 2.5:
            print(f"     🏆 R:R >= 2.5 untuk TP2 — setup bagus!")

    return {"ticker": ticker, "close": d["close"], "pct_change": d["pct_change"],
            "rule_score": rs, "max_rules": mx, "quality": quality,
            "status": status, "q_label": ql, "entry": entry, "stage": d.get("stage_label","")}


def print_summary(results):
    results.sort(key=lambda x: x["quality"], reverse=True)
    strong = [r for r in results if r["quality"] >= 55 and r["rule_score"] >= r["max_rules"]-3]

    print(f"\n{'='*70}")
    print(f"  📋 RINGKASAN — {MODE_NAME}")
    print(f"{'='*70}")
    print(f"  Total: {len(results)}  |  Lolos: {len(strong)}  |  Skip: {len(results)-len(strong)}")

    if strong:
        print(f"\n  🏆 TOP PICKS")
        hdr = f"  {'#':<3}{'Ticker':<7}{'Harga':>8}{'Chg':>7}{'Skor':>6} {'Label':>11}{'Entry Area':>20}{'SL':>9}{'%SL':>7}{'R1(TP1)':>9}{'%R1':>7}{'R2(TP2)':>9}{'%R2':>7}{'R:R':>6}"
        print(f"  {'─'*len(hdr)}")
        print(hdr)
        print(f"  {'─'*len(hdr)}")
        for i, r in enumerate(strong[:10], 1):
            e = r.get("entry")
            if e:
                area = f"{e['entry_low']:,.0f}-{e['entry_high']:,.0f}"
                rr = f"1:{e['rr1']:.1f}"
                em = (e['entry_low'] + e['entry_high']) / 2
                p_sl = ((e['sl'] - em) / em * 100) if em > 0 else 0
                p_r1 = ((e['tp1'] - em) / em * 100) if em > 0 else 0
                p_r2 = ((e['tp2'] - em) / em * 100) if em > 0 else 0
                print(f"  {i:<3}{r['ticker']:<7}{r['close']:>8,.0f}{r['pct_change']:>+6.1f}%"
                      f"{r['quality']:>5} {r['q_label']:>11}"
                      f"{area:>20}{e['sl']:>9,.0f}{p_sl:>+6.1f}%"
                      f"{e['tp1']:>9,.0f}{p_r1:>+6.1f}%"
                      f"{e['tp2']:>9,.0f}{p_r2:>+6.1f}%{rr:>6}")
            else:
                print(f"  {i:<3}{r['ticker']:<7}{r['close']:>8,.0f}{r['pct_change']:>+6.1f}%"
                      f"{r['quality']:>5} {r['q_label']:>11}")

        b = strong[0]
        e = b["entry"]
        bm = (e['entry_low'] + e['entry_high']) / 2
        bp_sl = ((e['sl'] - bm) / bm * 100) if bm > 0 else 0
        bp_r1 = ((e['tp1'] - bm) / bm * 100) if bm > 0 else 0
        bp_r2 = ((e['tp2'] - bm) / bm * 100) if bm > 0 else 0
        print(f"\n  🥇 BEST: {b['ticker']}")
        print(f"     Entry: {e['entry_low']:,.0f}-{e['entry_high']:,.0f}")
        print(f"     SL: {e['sl']:,.0f} ({bp_sl:+.1f}%) | S: {b.get('sr_s1',0):,.0f} | R1: {e['tp1']:,.0f} ({bp_r1:+.1f}%) | R2: {e['tp2']:,.0f} ({bp_r2:+.1f}%)")
        print(f"     R:R 1:{e['rr1']:.1f} (R1) | 1:{e['rr2']:.1f} (R2) | Max {e['max_alloc']} modal")
    else:
        print(f"\n  ⚠️  Tidak ada yang lolos filter ketat hari ini.")
        print(f"     Ini NORMAL — tunggu setup yang tepat, sabar.")

    print(f"\n  📖 PRINSIP SWING (Stage Analysis + Minervini SL):")
    print(f"     • Fokus Stage 1→2 BREAKOUT (baru keluar dari base)")
    print(f"     • Stage 1→2 = peluang terbaik, awal uptrend baru")
    print(f"     • Stage 2 lanjutan = masih OK tapi potensi lebih kecil")
    print(f"     • HINDARI Stage 3 (topping) & Stage 4 (declining)")
    print(f"     • Konfirmasi: volume naik + close > MA50 + chart pattern")
    print(f"     • SL di bawah swing low/pivot, MAX 8% (Minervini)")
    print(f"     • Max 5% modal per saham")

    print(f"\n  ⚠️  DISCLAIMER: Edukasi. Bukan ajakan beli/jual. DYOR.")
    print(f"{'='*70}")


# ============================================================
# MAIN
# ============================================================

def main():
    print(f"\n{'='*70}")
    print(f"  IDX SYARIAH SCREENER v3.0 — SWING TRADING")
    print(f"  Saham Syariah | Stage Analysis + Fibonacci + Minervini SL")
    print(f"  {datetime.now().strftime('%d %B %Y %H:%M')}")
    print(f"{'='*70}")

    print(f"\n  Pilih saham syariah:")
    print(f"  1. JII ({len(JII)}) — 30 Saham Syariah Terliquid")
    print(f"  2. JII + JII70 ({len(JII)+len(JII70_EXTRA)}) — Rekomendasi")
    print(f"  3. SEMUA termasuk ISSI ({len(ALL_STOCKS)})")
    print(f"  4. Manual")

    sc = input("\n  Pilihan (1/2/3/4): ").strip()
    stocks = {"1":JII,"2":JII+JII70_EXTRA,"3":ALL_STOCKS}.get(sc, JII)
    if sc == "4":
        stocks = [s.strip().upper() for s in input("  Kode (koma): ").split(",")]

    print(f"\n  📥 Fetching {len(stocks)} saham (1 tahun data)...")

    all_data = {}
    for i, t in enumerate(stocks, 1):
        print(f"  [{i}/{len(stocks)}] {t}...", end="", flush=True)
        df = fetch_data(t)
        if df is None:
            print(f" skip"); continue
        try:
            all_data[t] = calc_all(df, t)
            stg_num = all_data[t]["stage"]
            if stg_num == 12:
                stg_txt = "🚀 BREAKOUT 1→2"
            elif stg_num == 2:
                stg_txt = "✅ Stage 2"
            elif stg_num == 1:
                stg_txt = "🔄 Stage 1 (base)"
            elif stg_num == 3:
                stg_txt = "⚠️ Stage 3 (top)"
            elif stg_num == 4:
                stg_txt = "❌ Stage 4 (down)"
            else:
                stg_txt = ""
            print(f" {all_data[t]['close']:,.0f} | {stg_txt}")
        except Exception as e:
            print(f" ❌ {e}")
        time.sleep(0.3)

    print(f"\n  Data OK: {len(all_data)}/{len(stocks)}\n")

    print(f"\n{'='*70}")
    print(f"  🔍 {MODE_NAME}")
    print(f"{'='*70}")

    all_res = []
    for t, d in all_data.items():
        rules, rs, mx = screen_swing(d)
        entry = calc_entry_swing(d)
        quality = calc_score(d)
        all_res.append({"ticker":t,"data":d,"rules":rules,
                       "rule_score":rs,"max_rules":mx,"quality":quality,"entry":entry})

    # Sort & display
    all_res.sort(key=lambda x: x["quality"], reverse=True)

    display = []
    for r in all_res:
        if r["rule_score"] >= r["max_rules"] - 4 and len(display) < 10:
            res = display_result(r["ticker"],r["data"],r["rules"],
                r["rule_score"],r["max_rules"],r["quality"],r["entry"])
            display.append(res)

    if not display:
        print(f"\n  Menampilkan top 5:")
        for r in all_res[:5]:
            res = display_result(r["ticker"],r["data"],r["rules"],
                r["rule_score"],r["max_rules"],r["quality"],r["entry"])
            display.append(res)

    summary = [{"ticker":r["ticker"],"close":r["data"]["close"],
                "pct_change":r["data"]["pct_change"],"rule_score":r["rule_score"],
                "max_rules":r["max_rules"],"quality":r["quality"],
                "status":"✅","q_label":"BUY" if r["quality"]>=55 else "WATCH",
                "entry":r["entry"],"stage":r["data"].get("stage_label",""),
                "sr_s1":r["data"].get("sr_s1",0)} for r in all_res]
    print_summary(summary)

    print(f"\n  Selesai! 🎉\n")

if __name__ == "__main__":
    main()
