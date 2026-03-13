# AuctionEye 🎯
### AI Flea Market Agent — Gemini Live Agent Challenge 2026

> At flea markets, sellers know what items are worth. Buyers don't.  
> AuctionEye fixes that — point your camera at any item and an AI agent  
> whispers the real eBay market price in your ear before you negotiate.

**Built for:** Gemini Live Agent Challenge 2026 — Live Agents Category  
**Hashtag:** `#GeminiLiveAgentChallenge`

---

## 🎬 Demo

[▶ Watch 4-minute demo on YouTube](#) <!-- Add your YouTube link here -->

---

## The Problem

Every flea market is an information war. Sellers research their items. Buyers guess. The person who paid $2 at an estate sale is confidently asking $45 from someone who has no idea if that's fair.

AuctionEye puts real market intelligence in the buyer's ear — silently, instantly, at the exact moment it's needed.

---

## How It Works

AuctionEye runs as a live agent — point your camera at any item and press SPACE.

The current version runs on laptop as a proof of concept. The agent architecture (Gemini vision + eBay pricing + Firestore memory) is fully portable and designed for a mobile form factor as the natural next step. For the demo: laptop nearby, earphone in ear, camera facing items. The AI whispers. Nobody around you knows what just happened.

**Step 1 — See**
Gemini's vision reads the camera frame and identifies the item precisely — brand, model, era, condition. Not "a bowl." Exactly "vintage pink Pyrex mixing bowl."

**Step 2 — Price**
The price agent searches eBay's live listings for that exact item. An outlier filter removes junk listings, leaving a tight, trustworthy range — what real people paid last week.

**Step 3 — Decide**
The strategy agent receives the item image, the eBay range, and thinks like an expert: Is the condition good? Is the asking price fair? It returns a direct BUY, NEGOTIATE, or PASS with reasoning.

**Step 4 — Remember**
Every scan is saved to Google Cloud Firestore. Press Q at end of day — AuctionEye speaks your full session report: *"Today you scanned 7 items. Best deal: cast iron skillet. Potential savings: $89 versus retail."*

---

## Agent Architecture (ADK Design Principles)

AuctionEye is built following Google's **Agent Development Kit (ADK)** multi-agent design pattern — three specialized agents, each with a single responsibility, coordinated in a pipeline.

This follows ADK's core philosophy: focused agents outperform monolithic ones. A single agent trying to identify items, search prices, AND reason about value makes worse decisions than three agents each doing one thing perfectly.

```
┌─────────────────────────────────────────────────────┐
│                 LIVE CAMERA FEED                    │
│            OpenCV — 30fps continuous                │
└────────────────────┬────────────────────────────────┘
                     │ SPACE pressed — frame captured
┌────────────────────▼────────────────────────────────┐
│               VISION AGENT                         │
│             Gemini 2.5 Flash                       │
│   Reads item name, brand, model from camera        │
│   Output: "vintage pyrex bowl" / "OnePlus 9 Pro"   │
└────────────────────┬────────────────────────────────┘
                     │ Clean, specific item name
          ┌──────────┴───────────┐
          │                      │
┌─────────▼────────┐   ┌─────────▼──────────────────┐
│   PRICE AGENT    │   │      STRATEGY AGENT        │
│   SerpApi eBay   │   │     Gemini 2.5 Flash       │
│  Real sold data  │   │  Image + price → decision  │
│  Outlier filter  │   │  BUY / NEGOTIATE / PASS    │
│  Tight range     │   │  Condition + reasoning     │
└─────────┬────────┘   └─────────┬──────────────────┘
          └──────────┬───────────┘
                     │ Combined result
┌────────────────────▼────────────────────────────────┐
│            GOOGLE CLOUD FIRESTORE                  │
│    Saves item name, price, advice, timestamp       │
│    Generates end-of-day session savings report     │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│               VOICE OUTPUT                         │
│             pyttsx3 TTS engine                     │
│   Whispers advice through earphone — hands free    │
└─────────────────────────────────────────────────────┘
```

### Agent Breakdown

| Agent | Model | Single Responsibility |
|-------|-------|----------------------|
| Vision Agent | Gemini 2.5 Flash | Identify item precisely from camera frame |
| Price Agent | SerpApi + eBay | Fetch real market prices, filter outliers |
| Strategy Agent | Gemini 2.5 Flash | Combine vision + price → actionable decision |

---

## Google Cloud Services

| Service | Role in AuctionEye |
|---------|-------------------|
| **Gemini 2.5 Flash** | Vision + reasoning for every scan |
| **Google GenAI SDK** | Model access, multimodal inputs, prompt engineering |
| **Cloud Firestore** | Session memory — saves every item, generates reports |
| **Cloud Storage** | Saves scanned item images with session data |

AuctionEye is Google Cloud native — every scan touches at least three Google Cloud services simultaneously.

---

## Multimodal Inputs & Outputs

| Input | Output |
|-------|--------|
| Live camera video (vision) | Voice advice through speakers (audio) |
| Item image (multimodal) | Text analysis on screen (visual) |
| SPACE key trigger | Session report spoken at end of day |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| AI Model | Gemini 2.5 Flash |
| Agent SDK | Google GenAI SDK (ADK principles) |
| Memory | Google Cloud Firestore |
| Image Storage | Google Cloud Storage |
| Price Data | SerpApi — eBay live listings |
| Camera | OpenCV |
| Voice | pyttsx3 TTS |
| UI | Python Tkinter (dark premium) |

---

## Setup & Run

### Prerequisites

- Python 3.10+
- Laptop with webcam
- Google Cloud account (Firestore + Storage enabled)
- Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))
- SerpApi account ([Free tier](https://serpapi.com) — 100 searches/month)

### Step 1 — Clone

```bash
git clone https://github.com/YOUR_USERNAME/auctioneye.git
cd auctioneye
```

### Step 2 — Install dependencies

```bash
pip install google-genai google-cloud-firestore google-cloud-storage opencv-python pillow pyttsx3 google-search-results
```

### Step 3 — Configure API keys

In `ui.py` and `live_camera.py`:
```python
GEMINI_KEY = "your_gemini_api_key_here"
```

In `price_search.py`:
```python
SERPAPI_KEY = "your_serpapi_key_here"
```

### Step 4 — Set up Google Cloud Firestore

```
1. Go to console.cloud.google.com
2. Enable Firestore → Native mode → nam5 region
3. IAM & Admin → Service Accounts → Create
4. Role: Cloud Datastore User
5. Keys → Add Key → JSON → save as firestore-key.json
6. Place firestore-key.json in project folder
```

In `memory.py` update:
```python
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/firestore-key.json"
```

### Step 5 — Run

```bash
python ui.py
```

| Key | Action |
|-----|--------|
| `SPACE` | Analyze item in camera view |
| `Q` | Speak session report + quit |

---

## Proof of Google Cloud Deployment

AuctionEye saves every scanned item live to Google Cloud Firestore.

To verify:
1. Run `python ui.py`
2. Scan any item (press SPACE)
3. Open [Firestore Console](https://console.cloud.google.com/firestore)
4. See live data appear in `scanned_items` collection

See `memory.py` for the complete Firestore integration code.

---

## What Makes It Different

Most AI camera apps identify objects. AuctionEye acts on what it sees.

Three focused ADK-style agents work together: one identifies the item precisely, one fetches real eBay sold prices from last week (not AI guesses), one combines both to give a specific buying decision. The offer price (40% of eBay average) is the flea market sweet spot — low enough for negotiation room, high enough to close on genuinely valuable items.

The memory layer turns a single-scan tool into a full shopping companion. The voice output keeps your eyes on the seller, not on a screen. The background operation means nobody around you knows you just ran a live AI analysis.

AuctionEye is intentionally designed as a background agent — it never draws attention to itself. No screen to stare at. No typing. Just a whisper in your ear at the moment you need it most.

---

## File Structure

```
auctioneye/
├── ui.py               # Main app — dark premium UI
├── live_camera.py      # Terminal version
├── price_search.py     # eBay price search (SerpApi)
├── memory.py           # Google Cloud Firestore + Storage
├── test.py             # Gemini text test
├── test_vision.py      # Vision test
├── .gitignore          # Hides API keys and firestore-key.json
└── README.md
```

---

## Roadmap

The agent architecture is already phone-ready. The natural next step is a mobile version — same Gemini pipeline, same Firestore memory synced across devices, phone camera instead of webcam. Only the UI needs adapting.

---

Built by **[Your Name]** — created during the Gemini Live Agent Challenge contest period, February–March 2026.  
`#GeminiLiveAgentChallenge`
