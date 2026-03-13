# AuctionEye 🎯
**AI flea market agent — point your camera, hear the deal.**

[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-blue)](https://aistudio.google.com)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-Firestore-orange)](https://cloud.google.com)
[![Python](https://img.shields.io/badge/Python-3.10+-green)](https://python.org)
[![Hackathon](https://img.shields.io/badge/Gemini%20Live%20Agent%20Challenge-2026-purple)](https://geminiliveagentchallenge.devpost.com)

---

## Demo

[▶ Watch 4-minute demo on YouTube](#) <!-- add your link -->

---

## What It Does

At every flea market, sellers know what their items are worth. Buyers don't.

AuctionEye fixes that. Point your camera at any item, press `SPACE` — within 10 seconds Gemini identifies it, SerpApi finds what it sold for on eBay last week, and a voice whispers the advice in your ear:

> *"Vintage pink Pyrex bowl. Market range $28–$65. Offer $17. Strong buy — pink pattern is collectible."*

Press `Q` at end of day:
> *"You scanned 7 items today. Best deal: cast iron skillet. Potential savings: $89."*

No screen to stare at. No typing. The intelligence is invisible — nobody around you knows it's running.

> **Current form:** Laptop prototype (webcam + earphone). The agent pipeline is phone-ready — mobile UI is the natural next step.

---

## Architecture

![AuctionEye Architecture](architecture.png)

Three focused agents — each does one job, each does it well:

| Agent | Powered By | Responsibility |
|-------|-----------|----------------|
| Vision Agent | Gemini 2.5 Flash | Identifies item name, brand, model from camera frame |
| Price Agent | SerpApi (eBay listings) | Fetches live market prices, filters outliers |
| Strategy Agent | Gemini 2.5 Flash | Combines vision + price → BUY / NEGOTIATE / PASS |

This follows the ADK multi-agent design principle: focused agents outperform monolithic ones.

---

## Multimodal Inputs & Outputs

| Inputs | Outputs |
|--------|---------|
| Live camera video | Voice advice via earphone (audio out) |
| Item image (vision) | On-screen analysis with price + decision |
| Keyboard trigger (`SPACE`) | End-of-day session report (spoken) |

---

## Google Cloud Services

| Service | Role |
|---------|------|
| **Gemini 2.5 Flash** | Vision understanding + strategic reasoning |
| **Google GenAI SDK** | Model access, multimodal prompt handling |
| **Cloud Firestore** | Persistent session memory — every scan saved |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Model | Gemini 2.5 Flash (Google GenAI SDK) |
| Price Data | SerpApi — eBay live listings |
| Memory | Google Cloud Firestore |
| Camera | OpenCV |
| Voice | pyttsx3 TTS |
| UI | Python Tkinter (dark premium) |

---

## Proof of Google Cloud Deployment

Every scan saves live to Firestore. To verify:

1. Run `python ui.py` → scan any item (`SPACE`)
2. Open [Firestore Console](https://console.cloud.google.com/firestore)
3. Check the `scanned_items` collection — data appears instantly

Full integration code in [`memory.py`](memory.py).

---

## Setup

**Requirements:** Python 3.10+ · webcam · [Gemini API key](https://aistudio.google.com/app/apikey) · [SerpApi key](https://serpapi.com) (100 free searches/month) · Google Cloud account

**1. Clone**
```bash
git clone https://github.com/YOUR_USERNAME/auctioneye.git
cd auctioneye
```

**2. Install**
```bash
pip install google-genai google-cloud-firestore opencv-python pillow pyttsx3 google-search-results
```

**3. Add API keys**

In `ui.py` and `live_camera.py`:
```python
GEMINI_KEY = "your_gemini_api_key"
```
In `price_search.py`:
```python
SERPAPI_KEY = "your_serpapi_key"
```

**4. Set up Firestore**

1. [console.cloud.google.com](https://console.cloud.google.com) → Enable Firestore → Native mode → nam5
2. IAM & Admin → Service Accounts → Create → Role: Cloud Datastore User
3. Keys → Add Key → JSON → save as `firestore-key.json` in project root

In `memory.py`:
```python
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/firestore-key.json"
```

**5. Run**
```bash
python ui.py
```

| Key | Action |
|-----|--------|
| `SPACE` | Analyze item in camera view |
| `Q` | Speak session report + quit |

---

## File Structure

```
auctioneye/
├── ui.py               # Main app — dark premium Tkinter UI
├── live_camera.py      # Terminal version
├── price_search.py     # SerpApi market price search
├── memory.py           # Google Cloud Firestore session memory
├── architecture.png    # System architecture diagram
├── .gitignore          # Hides API keys + credentials
└── README.md
```

---

## Why It Works

Real sold prices (not AI guesses) + live vision + strategic reasoning = advice you can act on immediately. The voice output keeps your eyes on the seller. The memory layer turns a single scan into a full shopping companion. Running silently in the background, AuctionEye gives buyers the same information advantage sellers have always had.

---

*Built for the [Gemini Live Agent Challenge 2026](https://geminiliveagentchallenge.devpost.com) · `#GeminiLiveAgentChallenge`*
