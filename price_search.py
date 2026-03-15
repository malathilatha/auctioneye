from serpapi import GoogleSearch
import os
from dotenv import load_dotenv

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# Known electronics keywords — adds "smartphone used" etc
ELECTRONICS_KEYWORDS = [
    "phone", "iphone", "samsung", "oneplus", "pixel", "xiaomi",
    "redmi", "realme", "oppo", "vivo", "nokia", "motorola",
    "laptop", "macbook", "dell", "hp", "lenovo", "asus",
    "tablet", "ipad", "kindle", "camera", "nikon", "canon"
]

def is_electronics(item_name):
    """Check if item is electronics"""
    name_lower = item_name.lower()
    return any(keyword in name_lower for keyword in ELECTRONICS_KEYWORDS)

def build_search_query(item_name):
    """Build smarter search query"""
    if is_electronics(item_name):
        # Add 'unlocked used' to find actual devices not accessories
        return f"{item_name} unlocked used"
    return item_name

def search_ebay_prices(item_name):
    """Search eBay for real prices — filters outliers"""
    
    search_query = build_search_query(item_name)
    print(f"🔎 Searching eBay for: {search_query}")
    
    params = {
        "engine": "ebay",
        "ebay_domain": "ebay.com",
        "_nkw": search_query,
        "LF": "Sold",
        "api_key": SERPAPI_KEY
    }
    
    search = GoogleSearch(params)
    results = search.get_dict()
    items = results.get("organic_results", [])
    
    if not items:
        params.pop("LF")
        search = GoogleSearch(params)
        results = search.get_dict()
        items = results.get("organic_results", [])
    
    if not items:
        return None, "No price data found on eBay"
    
    prices = []
    for item in items[:10]:
        price_str = item.get("price", {}).get("raw", "")
        clean = price_str.replace("$", "").replace(",", "").strip()
        try:
            price = float(clean.split()[0])
            # ✅ Filter out accessories (under $20 for electronics)
            if is_electronics(item_name) and price < 20:
                continue
            prices.append(price)
        except:
            pass
    
    if not prices:
        return None, "Could not read prices"
    
    # Remove outliers
    prices.sort()
    cut = max(1, len(prices) // 5)
    trimmed = prices[cut:-cut] if len(prices) > 4 else prices
    
    low = min(trimmed)
    high = max(trimmed)
    avg = sum(trimmed) / len(trimmed)
    
    summary = f"eBay prices range from ${low:.0f} to ${high:.0f}, average ${avg:.0f}"
    return avg, summary
