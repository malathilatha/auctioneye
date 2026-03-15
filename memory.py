from google.cloud import firestore
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
db = firestore.Client()

def save_item(item_name, price_summary, avg_price, advice):
    doc = {
        "item": item_name,
        "price_summary": price_summary,
        "avg_price": avg_price,          # None for voice items — that's fine
        "advice": advice,
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source": "voice" if str(item_name).startswith("[voice]") else "scan"
    }
    db.collection("scanned_items").add(doc)
    print(f"💾 Saved: {item_name}")

def get_todays_items():
    today = datetime.now().strftime("%Y-%m-%d")
    items = db.collection("scanned_items")\
              .where(filter=firestore.FieldFilter("date", "==", today))\
              .stream()
    return list(items)

def get_session_report():
    items = get_todays_items()
    if not items:
        return "No items scanned today."

    all_items   = []
    scan_items  = []   # SPACE key — have price data
    voice_items = []   # V mode — no price data

    for item in items:
        data = item.to_dict()
        all_items.append(data)
        if data.get("source") == "voice" or data.get("avg_price") is None:
            voice_items.append(data)
        else:
            scan_items.append(data)

    total_scans  = len(scan_items)
    total_voice  = len(voice_items)
    total        = len(all_items)

    # Best deal = lowest-priced scanned item
    best_deal  = None
    best_price = 999999
    prices     = []
    for d in scan_items:
        p = d.get("avg_price")
        if p:
            prices.append(p)
            if p < best_price:
                best_price = p
                best_deal  = d["item"]

    avg        = sum(prices) / len(prices) if prices else 0
    savings    = avg * total_scans * 0.6 if prices else 0

    # Build spoken report
    parts = []
    parts.append(f"Today you scanned {total_scans} item{'s' if total_scans != 1 else ''}")

    if total_voice > 0:
        parts.append(f"and had {total_voice} voice conversation{'s' if total_voice != 1 else ''}")

    if best_deal:
        parts.append(f"Best deal: {best_deal}")

    if savings > 0:
        parts.append(f"Potential savings: ${savings:.0f} versus retail prices")

    return ". ".join(parts) + "."