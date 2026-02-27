# IDX Stock Screener

Aplikasi screener saham Indonesia (IDX) dengan analisis teknikal otomatis. SvelteKit frontend + FastAPI backend.

## Fitur

- **BSJP** — Beli Sore Jual Pagi (overnight swing)
- **Intraday** — Screener untuk day trading
- **Swing** — Swing trading (hold 1-8 minggu)
- **Night Scanner** — Prediksi top gainer besok
- **ARA Hunter** — Deteksi saham potensi ARA
- **Portfolio Tracker** — Sinyal HOLD / JUAL / CUT LOSS untuk portfolio kamu
- **Google Sign-In** — Portfolio tersimpan per user di server
- **Telegram Alert** — Notifikasi sinyal jual via Telegram Bot
- **PWA** — Installable di mobile/desktop

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | SvelteKit 5, TypeScript, Tailwind CSS 4 |
| Backend | FastAPI, Python 3.9+ |
| Data | Yahoo Finance (yfinance) |
| Indikator | RSI, MACD, Bollinger Band, ATR, ADX, MFI, Stochastic, Pivot Point |
| Database | SQLite (user + portfolio) |
| Auth | Google Sign-In + JWT |
| Notifikasi | Browser Notification, Telegram Bot |

## Prerequisites

- **Python 3.9+**
- **Node.js 18+** & npm
- (Opsional) Google Cloud OAuth Client ID untuk fitur login
- (Opsional) Telegram Bot Token untuk notifikasi

## Instalasi

```bash
# Clone repo
git clone https://github.com/dimasarmanu84/idx-screener.git
cd idx-screener

# Install backend dependencies
cd api
pip3 install -r requirements.txt

# Install frontend dependencies
cd ../web
npm install
```

## Konfigurasi

### Backend (`api/.env`)

Buat file `api/.env`:

```env
# Telegram Bot (opsional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Google Sign-In (opsional)
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
JWT_SECRET=random-secret-string-kamu
```

### Frontend (`web/.env`)

Buat file `web/.env`:

```env
# Sama dengan GOOGLE_CLIENT_ID di backend
PUBLIC_GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
```

> Tanpa konfigurasi Google/Telegram, app tetap berjalan normal — fitur login dan Telegram saja yang disabled.

## Menjalankan

### Cara cepat (kedua server sekaligus)

```bash
./start.sh
```

Buka http://localhost:5173

### Manual (terpisah)

```bash
# Terminal 1 — Backend (port 8000)
cd api
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend (port 5173)
cd web
npm run dev
```

## Jam Trading IDX

| Sesi | Waktu | Durasi |
|------|-------|--------|
| Sesi 1 | 09:00 - 12:00 | 180 menit |
| Istirahat | 12:00 - 13:30 | - |
| Sesi 2 | 13:30 - 15:50 | 140 menit |

App mendeteksi jam pasar otomatis dan menampilkan status LIVE/CLOSED di navbar.

## Kapan Screening

| Mode | Waktu Terbaik |
|------|---------------|
| BSJP | 14:30 - 15:50 (akhir sesi 2) |
| Intraday | 08:45 - 09:15 (sebelum/awal sesi 1) |
| Swing | Setelah 16:00 (setelah pasar tutup) |
| Night Scanner | 19:00 - 23:00 (malam hari) |
| Portfolio | Kapan saja (auto-scan tiap 5 menit saat pasar buka) |

## Setup Google Sign-In (Opsional)

1. Buka [Google Cloud Console](https://console.cloud.google.com)
2. Buat project → APIs & Services → Credentials
3. Create Credentials → OAuth 2.0 Client IDs → Web application
4. Authorized JavaScript origins: `http://localhost:5173`
5. Copy Client ID → isi di `api/.env` dan `web/.env`

## Setup Telegram Bot (Opsional)

1. Buka Telegram, cari **@BotFather** → `/newbot`
2. Dapat Bot Token
3. Start bot, kirim pesan, buka `https://api.telegram.org/bot<TOKEN>/getUpdates` → cari `chat.id`
4. Isi `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_CHAT_ID` di `api/.env`

## Struktur Project

```
idx-screener/
├── api/                    # FastAPI backend
│   ├── main.py             # Endpoints & app config
│   ├── auth.py             # Google OAuth + JWT
│   ├── database.py         # SQLite CRUD
│   ├── telegram.py         # Telegram Bot notifications
│   ├── requirements.txt
│   └── screener/
│       ├── engine.py       # Core screening logic
│       └── market.py       # IDX market hours
├── web/                    # SvelteKit frontend
│   ├── src/
│   │   ├── lib/
│   │   │   ├── api.ts              # API client
│   │   │   ├── auth.svelte.ts      # Auth state
│   │   │   ├── portfolioScanner.svelte.ts
│   │   │   ├── types.ts
│   │   │   └── components/         # UI components
│   │   └── routes/                 # Pages
│   └── static/                     # PWA icons, manifest
├── start.sh                # Start both servers
└── .gitignore
```

## Build Production

```bash
cd web
npm run build
# Output di web/build/ — serve sebagai static site
```

## License

Private — hanya untuk penggunaan pribadi.
