#!/bin/bash
# =============================================================
# AuctionEye — Infrastructure as Code (IaC) Setup Script
# Automates all dependencies and environment verification
# Usage: bash setup.sh
# =============================================================

set -e

echo ""
echo "🎯 AuctionEye — Automated Setup"
echo "================================"

echo ""
echo "📌 Checking Python version..."
python --version || python3 --version

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
  numpy \
  python-dotenv

echo "✅ All dependencies installed."

echo ""
echo "☁️  Checking Google Cloud credentials..."
if [ -f "firestore-key.json" ]; then
  echo "✅ firestore-key.json found."
else
  echo "⚠️  firestore-key.json NOT found."
  echo "   Download from: GCP Console → IAM → Service Accounts → Keys"
fi

echo ""
echo "🔑 Checking .env file..."
if [ -f ".env" ]; then
  echo "✅ .env file found."
else
  echo "⚠️  .env file NOT found. Copy .env.example to .env and fill in your keys:"
  echo "   cp .env.example .env"
fi

echo ""
echo "🔑 Checking API keys (GEMINI_KEY)..."
if [ -z "$GEMINI_KEY" ] && [ -z "$GEMINI_API_KEY" ]; then
  echo "⚠️  GEMINI_KEY not set. Add to your .env file:"
  echo "   GEMINI_KEY=your_key_here"
else
  echo "✅ Gemini API key is set."
fi

if [ -z "$SERPAPI_KEY" ]; then
  echo "⚠️  SERPAPI_KEY not set. Add to your .env file:"
  echo "   SERPAPI_KEY=your_key_here"
else
  echo "✅ SERPAPI_KEY is set."
fi

echo ""
echo "================================"
echo "🚀 Setup complete. Run the app:"
echo "   python ui.py          (full UI)"
echo "   python live_camera.py (terminal)"
echo "================================"
echo ""
