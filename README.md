# AuctionEye 🎯

> **Real-time flea market AI — point your camera, hear the deal.**

[![Gemini Live API](https://img.shields.io/badge/Gemini-Live%20API-34A853?logo=google&logoColor=white)](https://ai.google.dev/gemini-api/docs/live)
[![Gemini 2.5 Flash](https://img.shields.io/badge/Gemini-2.5%20Flash-4285F4?logo=google&logoColor=white)](https://aistudio.google.com)
[![Google Cloud Firestore](https://img.shields.io/badge/Google%20Cloud-Firestore-FF6D00?logo=googlecloud&logoColor=white)](https://cloud.google.com/firestore)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Hackathon](https://img.shields.io/badge/Gemini%20Live%20Agent%20Challenge-2026-blueviolet)](https://geminiliveagentchallenge.devpost.com)

Submitted to the **[Gemini Live Agent Challenge 2026](https://geminiliveagentchallenge.devpost.com)** — Live Agents category · `#GeminiLiveAgentChallenge`

---

## 🎬 Demo

> ▶ **[Watch 4-minute demo on YouTube](#)** ← _Replace `#` with your YouTube URL before submitting_

---

## 📸 App in Action

> **How to take this screenshot:**
> 1. Run `python ui.py`
> 2. Point camera at any item (bracelet, figurine, watch)
> 3. Press `SPACE` — wait for the full result to load
> 4. When item name + eBay range + offer price + BUY/NEGOTIATE badge are all visible → take screenshot
> 5. Save as `screenshot.png` in the project root and push to GitHub
> 6. **Delete these instructions after adding the image**

![AuctionEye scanning a flea market item — live camera, price analysis, verdict](screenshot.png)

---

## The Problem

Sellers at flea markets always know what their items are worth. Buyers almost never do. That one-sided information gap costs buyers money on every single transaction — because by the time you've pulled out your phone and searched, the moment is gone and the seller has seen you do it.

**AuctionEye fixes this. Invisibly. In real time. Through your earphone.**

---

## What It Does

| Key | Mode | What Happens |
|-----|------|-------------|
| `SPACE` | **Scan** | Camera → Gemini identifies item → SerpApi fetches real eBay prices → voice whispers advice |
| `V` | **Live Voice** | Gemini Live API activates — fully bidirectional voice + vision. Speak naturally. |
| `Q` | **Session Report** | Spoken end-of-day summary — items scanned, best deal, potential savings |

### Scan Mode — Example Output
> *"Vintage pink Pyrex bowl. eBay range $28–$65. Offer $17. Strong buy — pink pattern is collectible."*

### Live Voice Mode — Example Conversation
> **You:** *"They want $40 for this bracelet — is that fair?"*
> **AuctionEye:** *"Gold-plated fashion piece. $8 to $10 is fair. Walk away at $25."*

No typing. No screen-staring. The seller has no idea it's running.

---

## Architecture

![AuctionEye System Architecture](AuctionEye_Architecture.png)

### Agent Design

Four focused agents — each does exactly one job:

| Agent | Powered By | Responsibility |
|-------|-----------|----------------|
| **Vision Agent** | Gemini 2.5 Flash (multimodal) | Identifies item name, brand, model from live camera frame |
| **Price Agent** | SerpApi → eBay live listings | Fetches real sold prices, trims outliers for a tight range |
| **Strategy Agent** | Gemini 2.5 Flash | Combines vision + price → BUY / NEGOTIATE / PASS |
| **Voice Agent** | Gemini Live API (bidi streaming) | Real-time voice conversation — sees camera, hears user simultaneously |

---

## Google Cloud Services

| Service | How It's Used |
|---------|--------------|
| **Gemini 2.5 Flash** | Vision identification + strategic reasoning |
| **Gemini Live API** (`gemini-2.5-flash-native-audio-preview-12-2025`) | Real-time bidirectional voice + vision streaming |
| **Google GenAI SDK** | Model access and multimodal prompt handling |
| **Cloud Firestore** | Persistent session memory — every scan and voice turn saved with timestamp |

---

## Proof of Google Cloud Deployment

Every scan and every voice conversation writes live to Firestore.

**Verify with code:** See [`memory.py`](memory.py) — uses `google-cloud-firestore` SDK, `firestore.Client()`, and `FieldFilter` queries against GCP.

**Verify live:**
1. Run `python ui.py` → press `SPACE` on any item
2. Open [Firestore Console](https://console.cloud.google.com/firestore) → `scanned_items` collection
3. Your record appears instantly — timestamped, tagged `source: "scan"` or `source: "voice"`

---

## Setup

### Quick Start
```bash
git clone https://github.com/malathilatha/auctioneye.git
cd auctioneye
bash setup.sh
```

### Step-by-Step

**1. Install dependencies**
```bash
pip install google-genai google-cloud-firestore opencv-python \
            pillow pyttsx3 google-search-results sounddevice numpy
```

**2. Configure environment variables**

Copy the example file and fill in your keys:
```bash
cp .env.example .env
```

Or set directly:

_Windows:_
```cmd
set GEMINI_API_KEY=your_gemini_api_key
set SERPAPI_KEY=your_serpapi_key
```

_Mac / Linux:_
```bash
export GEMINI_API_KEY=your_gemini_api_key
export SERPAPI_KEY=your_serpapi_key
```

Get your keys:
- Gemini API key → [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- SerpApi key → [serpapi.com](https://serpapi.com) (100 free searches/month)

**3. Set up Firestore**

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Enable **Cloud Firestore** → Native mode → `nam5` region
3. IAM & Admin → Service Accounts → Create → Role: **Cloud Datastore User**
4. Keys → Add Key → JSON → save as `firestore-key.json` in project root

**4. Run**

```bash
python ui.py           # Full dark-theme UI (recommended)
python live_camera.py  # Terminal version
```

| Key | Action |
|-----|--------|
| `SPACE` | Scan item — eBay price analysis + voice advice |
| `V` | Toggle Live Voice — speak freely, agent watches camera |
| `Q` | Speak session report + quit |

> ⚠️ **Use earphones** — prevents mic picking up speaker output.

---

## Third-Party Integrations

Per contest rules, all third-party integrations are listed explicitly:

| Tool | Version | Purpose | License |
|------|---------|---------|---------|
| [SerpApi](https://serpapi.com) | Latest | eBay listing search — real sold prices | Commercial (100 free/month) |
| [OpenCV](https://opencv.org) | 4.x | Live camera capture | Apache 2.0 |
| [sounddevice](https://pypi.org/project/sounddevice/) | Latest | Audio I/O — Python 3.14 compatible | MIT |
| [pyttsx3](https://pypi.org/project/pyttsx3/) | Latest | Offline TTS for session report | MIT |
| [Pillow](https://python-pillow.org) | Latest | Image preprocessing for Gemini | HPND |

---

## File Structure

```
auctioneye/
├── live_camera.py          # Terminal app — SPACE scan + V voice + Q report
├── ui.py                   # Dark premium Tkinter UI
├── price_search.py         # SerpApi eBay price search with outlier filter
├── memory.py               # Google Cloud Firestore — session memory
├── setup.sh                # IaC — automated one-command setup
├── .env.example            # Environment variable template
├── AuctionEye_Architecture.png   # System architecture diagram
├── screenshot.png          # App screenshot — add before submitting ← TODO
├── .gitignore              # Hides API keys and credentials
└── README.md
```

---

## Why It Works

**Real prices, not guesses.** SerpApi pulls actual eBay sold listings — not AI estimates. An outlier filter trims the top and bottom 20% of results, giving a tight and actionable price range.

**Two modes for every situation.** The scan mode gives a calculated offer price in under 10 seconds. Live voice lets you ask follow-up questions and negotiate in real time while your eyes stay on the seller.

**Invisible intelligence.** No screen to check. No typing required. Voice in, voice out — the agent is a whisper in your ear that nobody else can hear.

**Memory that compounds.** Every scan and voice conversation saves to Firestore. The end-of-day report turns individual decisions into a complete picture of your savings.

---

*Built for the [Gemini Live Agent Challenge 2026](https://geminiliveagentchallenge.devpost.com) · `#GeminiLiveAgentChallenge`*
