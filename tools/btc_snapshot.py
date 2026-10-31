#!/usr/bin/env python3
"""Fetch BTC market data from CoinGecko and write it as the BTC Paper Desk's db document.

Usage: python3 tools/btc_snapshot.py OUT.json
"""
import json
import sys
import urllib.request

API = "https://api.coingecko.com/api/v3"


def get(path):
    req = urllib.request.Request(API + path, headers={"Accept": "application/json", "User-Agent": "btc-paper/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


spot = get("/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true&include_last_updated_at=true")["bitcoin"]
m5 = get("/coins/bitcoin/market_chart?vs_currency=usd&days=1")["prices"]
h4 = get("/coins/bitcoin/ohlc?vs_currency=usd&days=14")
doc = {
    "price": spot["usd"],
    "change": round(spot["usd_24h_change"], 3),
    "updated": spot["last_updated_at"] * 1000,
    "m5": {"t": [int(t) for t, _ in m5], "p": [round(p, 1) for _, p in m5]},
    "h4": {k: [r[i] if i == 0 else round(r[i], 1) for r in h4] for i, k in enumerate("tohlc")},
}
with open(sys.argv[1], "w") as fh:
    json.dump(doc, fh, separators=(",", ":"))
print("price", doc["price"], "m5", len(m5), "h4", len(h4))
