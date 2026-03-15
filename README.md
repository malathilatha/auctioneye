# AuctionEye 🎯

**Real-time flea market AI — point your camera, hear the deal.**

[![Gemini Live API](https://img.shields.io/badge/Gemini-Live%20API-34A853?logo=google)](https://ai.google.dev/gemini-api/docs/live)
[![Google Cloud Firestore](https://img.shields.io/badge/Google%20Cloud-Firestore-FF6D00?logo=googlecloud)](https://cloud.google.com/firestore)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Submitted to the **Gemini Live Agent Challenge 2026 – Live Agents category**

---

# Overview

AuctionEye is a **real-time AI assistant for flea market shopping**.

At flea markets and thrift stores, sellers usually know the real value of items, while buyers often do not. This information gap leads to buyers overpaying.

AuctionEye solves this by using AI vision, real-time price lookup, and voice interaction to give buyers instant negotiation advice.

The user simply points the camera at an object and the system:

1. Identifies the item using AI vision
2. Fetches real market prices from eBay listings
3. Analyzes the value using an AI strategy model
4. Provides voice advice to **buy, negotiate, or walk away**

---

# Demo

Watch the demo video here:
(Add your YouTube link)

---

# App in Action

![AuctionEye Application](screenshot.png)

---

# Architecture

![AuctionEye Architecture](AuctionEye Architecture.png)

---

# System Workflow

1. Camera frame captured using OpenCV
2. Image analyzed using Gemini vision model
3. Product name extracted
4. eBay sold listings retrieved through SerpApi
5. Price range calculated
6. AI determines negotiation strategy
7. Voice advice delivered to the user
8. Scan result stored in Firestore

---

# Agent Architecture

AuctionEye uses a simple **multi-agent pipeline**.

| Agent          | Technology       | Role                                      |
| -------------- | ---------------- | ----------------------------------------- |
| Vision Agent   | Gemini 2.5 Flash | Identifies the item from the camera image |
| Price Agent    | SerpApi          | Retrieves eBay sold listings              |
| Strategy Agent | Gemini 2.5 Flash | Determines BUY / NEGOTIATE / PASS         |
| Voice Agent    | Gemini Live API  | Handles real-time voice interaction       |

---

# Key Project Files

| File              | Purpose                                                               |
| ----------------- | --------------------------------------------------------------------- |
| `ui.py`           | Main application interface handling camera feed, scan actions, and UI |
| `live_camera.py`  | Terminal-based version of the application                             |
| `memory.py`       | Handles session storage in Firestore                                  |
| `price_search.py` | Fetches eBay price data through SerpApi                               |

---

# Google Cloud Services Used

| Service          | Purpose                          |
| ---------------- | -------------------------------- |
| Gemini 2.5 Flash | Vision recognition and reasoning |
| Gemini Live API  | Real-time voice interaction      |
| Google GenAI SDK | Model access                     |
| Cloud Firestore  | Session data storage             |

---

# Proof of Google Cloud Deployment

Firestore integration is implemented in **`memory.py`**.

To verify the cloud integration:

1. Run the application

```
python ui.py
```

2. Point the camera at an item and press **SPACE** to scan.

3. The scan result will be saved automatically to **Cloud Firestore**.

4. Open the Firestore console in Google Cloud and check the collection:

```
scanned_items
```

You will see a new document containing:

* item name
* price range
* AI decision (BUY / NEGOTIATE / PASS)
* timestamp
* interaction source

This confirms the application is actively storing data in Google Cloud.

---

# Setup

## Clone the Repository

```
git clone https://github.com/YOUR_USERNAME/auctioneye.git
cd auctioneye
```

---

# Install Dependencies

```
pip install google-genai google-cloud-firestore opencv-python pillow pyttsx3 google-search-results sounddevice numpy
```

---

# Environment Variables

Windows:

```
set GEMINI_API_KEY=your_key
set SERPAPI_KEY=your_key
```

Mac / Linux:

```
export GEMINI_API_KEY=your_key
export SERPAPI_KEY=your_key
```

---

# Firestore Setup

1. Open Google Cloud Console
2. Enable **Cloud Firestore**
3. Create a Service Account
4. Download the credentials JSON file

Save it as:

```
firestore-key.json
```

---

# Run the Application

UI version:

```
python ui.py
```

Terminal version:

```
python live_camera.py
```

Controls:

| Key   | Action                  |
| ----- | ----------------------- |
| SPACE | Scan item               |
| V     | Voice interaction       |
| Q     | Session report and exit |

---

# Project Structure

```
auctioneye/
├── ui.py
├── live_camera.py
├── price_search.py
├── memory.py
├── setup.sh
├── auction_eye_ui.png
├── architecture.png
├── .gitignore
└── README.md
```

Built for the **Gemini Live Agent Challenge 2026**
