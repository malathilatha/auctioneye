# AuctionEye 🎯
**Real-time flea market AI — point your camera, hear the deal.**

[![Gemini Live API](https://img.shields.io/badge/Gemini-Live%20API-34A853?logo=google)](https://ai.google.dev/gemini-api/docs/live)
[![Google Cloud Firestore](https://img.shields.io/badge/Google%20Cloud-Firestore-FF6D00?logo=googlecloud)](https://cloud.google.com/firestore)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Gemini Live Agent Challenge](https://img.shields.io/badge/Gemini%20Live%20Agent%20Challenge-2026-blueviolet)](https://geminiliveagentchallenge.devpost.com)

> Submitted to the [Gemini Live Agent Challenge 2026](https://geminiliveagentchallenge.devpost.com) — **Live Agents** category.
> Built with Gemini Live API · Google GenAI SDK · Google Cloud Firestore · `#GeminiLiveAgentChallenge`

---

## 🎬 Demo

[▶ Watch 4-minute demo on YouTube](#)

---

## The Problem

At every flea market, sellers know exactly what their items are worth. Buyers never do. That information gap costs buyers money on every single transaction.

**AuctionEye closes that gap — invisibly, in real time, through your earphone.**

---

## What It Does

### `SPACE` — Scan Mode
Point camera at any item → Gemini identifies it → SerpApi fetches real eBay prices → voice whispers advice:
> *"Vintage Pyrex bowl. eBay range $28–$65. Offer $17. Strong buy."*

### `V` — Live Voice Mode
Gemini Live API — fully bidirectional voice + vision. Speak naturally, agent watches camera:
> *You: "Is $40 fair for this bracelet?"*
> *Agent: "Gold-plated. $8–$10 is fair. Walk away at $25."*

### `Q` — Session Report
> *"You scanned 4 items and had 2 voice conversations. Best deal: cast iron skillet. Potential savings: $89."*

No typing. No screen-staring. Invisible to everyone around you.

---

## App in Action

<!-- ============================================================
  SCREENSHOT INSTRUCTIONS — READ BEFORE PUSHING TO GITHUB
  ============================================================
  Take this screenshot WHILE the app is running:
    1. Run: python ui.py
    2. Point camera at any item (bracelet, watch, figurine)
    3. Press SPACE and wait for analysis to complete
    4. When you see: item name + eBay range + offer price
       + BUY/NEGOTIATE/PASS badge all showing on screen
    5. Screenshot the full window (Win+Shift+S on Windows)
    6. Save as: screenshot.png in project root
  The live camera feed WILL be visible — that is fine and good.
  It shows the app working in real time which is exactly what judges want.
  ============================================================ -->

![AuctionEye in action — scan result with live camera feed](screenshot.png)

*Live camera feed · Item identified by Gemini · eBay price range · Offer price · BUY/NEGOTIATE/PASS verdict*

---

## Architecture

<!-- ============================================================
  SCREENSHOT INSTRUCTIONS
  ============================================================
  This is the system architecture diagram.
  Screenshot it from the chat where it was generated.
  Save as: architecture.png in project root.
  ============================================================ -->

![AuctionEye Architecture](architecture.png)

---

## Agent Design

Four focused agents — each does exactly one job:

| Agent | Powered By | Job |
|-------|-----------|-----|
| **Vision Agent** | Gemini 2.5 Flash | Identifies item name, brand, model from camera frame |
| **Price Agent** | SerpApi → eBay listings | Fetches real sold prices, filters outliers |
| **Strategy Agent** | Gemini 2.5 Flash | Decides BUY / NEGOTIATE / PASS |
| **Voice Agent** | Gemini Live API (bidi) | Real-time voice + vision, fully conversational |

---

## Google Cloud Services

| Service | Role |
|---------|------|
| **Gemini 2.5 Flash** | Vision identification + strategy reasoning |
| **Gemini Live API** (`gemini-2.5-flash-native-audio-preview-12-2025`) | Real-time bidirectional voice + vision streaming |
| **Google GenAI SDK** | Model access, multimodal prompt construction |
| **Cloud Firestore** | Persistent session memory — every scan saved with timestamp |

---

## Proof of Google Cloud Deployment

All Firestore integration is in [`memory.py`](memory.py).

To verify live:
1. Run `python ui.py` → press `SPACE` on any item
2. Open [Firestore Console](https://console.cloud.google.com/firestore) → `scanned_items`
3. New record appears instantly — timestamped, tagged `source: "scan"` or `source: "voice"`

---

## Setup

### Option A — Automated (IaC)
```bash
bash setup.sh
```

### Option B — Manual

**1. Clone**
```bash
git clone https://github.com/YOUR_USERNAME/auctioneye.git
cd auctioneye
```

**2. Install**
```bash
pip install google-genai google-cloud-firestore opencv-python \
            pillow pyttsx3 google-search-results sounddevice numpy
```

**3. API Keys**

Windows:
```cmd
set GEMINI_API_KEY=your_gemini_key
set SERPAPI_KEY=your_serpapi_key
```
Mac/Linux:
```bash
export GEMINI_API_KEY=your_gemini_key
export SERPAPI_KEY=your_serpapi_key
```

**4. Firestore Credentials**
1. [GCP Console](https://console.cloud.google.com) → Firestore → Enable → Native mode → `nam5`
2. IAM & Admin → Service Accounts → Create → Role: Cloud Datastore User
3. Keys → Add Key → JSON → save as `firestore-key.json` in project root

**5. Run**
```bash
python ui.py           # Full UI
python live_camera.py  # Terminal version
```

| Key | Action |
|-----|--------|
| `SPACE` | Scan item — eBay prices + voice advice |
| `V` | Live Voice — speak freely, agent sees camera |
| `Q` | Session report + quit |

> Use earphones to prevent mic feedback.

---

## Third-Party Integrations

| Tool | Purpose |
|------|---------|
| [SerpApi](https://serpapi.com) | eBay listing search — 100 free/month |
| [OpenCV](https://opencv.org) | Camera capture |
| [sounddevice](https://pypi.org/project/sounddevice/) | Audio I/O, Python 3.14 compatible |
| [pyttsx3](https://pypi.org/project/pyttsx3/) | Offline TTS for session report |

---

## File Structure

```
auctioneye/
├── live_camera.py      # Terminal app — SPACE + V voice + Q report
├── ui.py               # Dark premium Tkinter UI
├── price_search.py     # SerpApi eBay price search
├── memory.py           # Google Cloud Firestore session memory
├── setup.sh            # IaC — one-command automated setup
├── architecture.png    # System architecture diagram  ← screenshot from chat
├── screenshot.png      # App running with scan result ← screenshot from ui.py
├── .gitignore          # Hides API keys + credentials
└── README.md
```

---

*Built for the [Gemini Live Agent Challenge 2026](https://geminiliveagentchallenge.devpost.com) · `#GeminiLiveAgentChallenge`*


done
