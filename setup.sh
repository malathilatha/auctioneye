#!/bin/bash
# =============================================================
# AuctionEye — Infrastructure as Code (IaC) Setup Script
# Automates all dependencies and environment verification
# Usage: bash setup.sh
# =============================================================

set -e  # stop on any error

echo ""
echo "🎯 AuctionEye — Automated Setup"
echo "================================"

# ── Step 1: Python version check ──────────────────────────
echo ""
echo "📌 Checking Python version..."
python --version || python3 --version

# ── Step 2: Install all dependencies ──────────────────────
echo ""
echo "📦 Installing dependencies..."

pip install \
  opencv-python \
  opencv-python-headless \
  google-genai \
  requests \
  pillow \
  pyttsx3 \
  google-search-results \
  google-cloud-firestore \
  sounddevice \
  numpy

echo "✅ All dependencies installed."

# ── Step 3: Verify Google Cloud credentials ───────────────
echo ""
echo "☁️  Checking Google Cloud credentials..."
if [ -f "firestore-key.json" ]; then
  echo "✅ firestore-key.json found."
else
  echo "⚠️  firestore-key.json NOT found."
  echo "   Download it from: GCP Console → IAM → Service Accounts → Keys"
fi

# ── Step 4: Verify environment variables ─────────────────
echo ""
echo "🔑 Checking API keys..."

if [ -z "$GEMINI_API_KEY" ]; then
  echo "⚠️  GEMINI_API_KEY not set."
  echo "   Run: export GEMINI_API_KEY=your_key_here"
else
  echo "✅ GEMINI_API_KEY is set."
fi

if [ -z "$SERPAPI_KEY" ]; then
  echo "⚠️  SERPAPI_KEY not set."
  echo "   Run: export SERPAPI_KEY=your_key_here"
else
  echo "✅ SERPAPI_KEY is set."
fi

# ── Step 5: Ready ─────────────────────────────────────────
echo ""
echo "================================"
echo "🚀 Setup complete. Run the app:"
echo "   python ui.py          (full UI)"
echo "   python live_camera.py (terminal)"
echo "================================"
echo ""
