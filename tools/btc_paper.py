#!/usr/bin/env python3
"""BTC paper trader with leverage. Live prices from CoinGecko, no real orders.

Usage:
  python3 tools/btc_paper.py                     # live breakdown (both sides, all scenarios)
  python3 tools/btc_paper.py open long|short     # open a paper position at the live price
  python3 tools/btc_paper.py status              # mark the open position to the live price
  python3 tools/btc_paper.py close               # close it and log the result
Options: --margin 100 --lev 10 --fee 0.0005 --mmr 0.005
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.request

API = "https://api.coingecko.com/api/v3"
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "trader", "paper_btc.json")


def get(path):
    req = urllib.request.Request(API + path, headers={"Accept": "application/json", "User-Agent": "btc-paper/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def ema(xs, n):
    k, out = 2 / (n + 1), [xs[0]]
    for x in xs[1:]:
        out.append(x * k + out[-1] * (1 - k))
    return out


def rsi(xs, n=14):
    gains = losses = 0.0
    for i in range(1, n + 1):
        d = xs[i] - xs[i - 1]
        gains, losses = gains + max(d, 0), losses + max(-d, 0)
    ag, al = gains / n, losses / n
    for i in range(n + 1, len(xs)):
        d = xs[i] - xs[i - 1]
        ag = (ag * (n - 1) + max(d, 0)) / n
        al = (al * (n - 1) + max(-d, 0)) / n
    return 100.0 if al == 0 else 100 - 100 / (1 + ag / al)


def atr(candles, n=14):
    trs = [max(h - l, abs(h - candles[i - 1][4]), abs(l - candles[i - 1][4]))
           for i, (_, o, h, l, c) in enumerate(candles) if i > 0]
    a = sum(trs[:n]) / n
    for t in trs[n:]:
        a = (a * (n - 1) + t) / n
    return a


def market():
    spot = get("/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
               "&include_24hr_vol=true&include_last_updated_at=true")["bitcoin"]
    m5 = [p[1] for p in get("/coins/bitcoin/market_chart?vs_currency=usd&days=1")["prices"]]
    h4 = get("/coins/bitcoin/ohlc?vs_currency=usd&days=14")
    return spot, m5, h4


def liq_price(entry, side, lev, mmr):
    return entry * (1 - 1 / lev + mmr) if side == "long" else entry * (1 + 1 / lev - mmr)


def pnl(entry, exit_, side, notional, fee):
    qty = notional / entry
    gross = (exit_ - entry) * qty * (1 if side == "long" else -1)
    return gross - notional * fee - exit_ * qty * fee


def money(x):
    return ("-$" if x < 0 else "+$") + "%.2f" % abs(x)


def breakdown(a):
    spot, m5, h4 = market()
    px = spot["usd"]
    closes4 = [c[4] for c in h4]
    e20_4, e50_4 = ema(closes4, 20)[-1], ema(closes4, 50)[-1]
    e20_5, e50_5 = ema(m5, 20)[-1], ema(m5, 50)[-1]
    r4, r5 = rsi(closes4), rsi(m5)
    a4 = atr(h4)
    hi24, lo24 = max(m5), min(m5)
    hi7 = max(c[2] for c in h4[-42:])
    lo7 = min(c[3] for c in h4[-42:])

    votes = [
        ("price vs 4h EMA20", px > e20_4),
        ("4h EMA20 vs EMA50", e20_4 > e50_4),
        ("price vs 5m EMA20", px > e20_5),
        ("5m EMA20 vs EMA50", e20_5 > e50_5),
    ]
    score = sum(1 if up else -1 for _, up in votes)
    if r4 > 70:
        score -= 1
    elif r4 < 30:
        score += 1
    bias = "LONG" if score >= 2 else "SHORT" if score <= -2 else "WAIT (no clear edge)"

    notional = a.margin * a.lev
    when = dt.datetime.fromtimestamp(spot["last_updated_at"], dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print("=" * 66)
    print("BTC/USD  $%s   (%+.2f%% 24h)   CoinGecko, %s" % (f"{px:,.0f}", spot["usd_24h_change"], when))
    print("24h range $%s - $%s   7d range $%s - $%s" % (f"{lo24:,.0f}", f"{hi24:,.0f}", f"{lo7:,.0f}", f"{hi7:,.0f}"))
    print("=" * 66)
    print("SIGNALS")
    for name, up in votes:
        print("  %-20s %s" % (name, "bullish" if up else "bearish"))
    print("  RSI(14) 4h %.0f, 5m %.0f   (>70 overbought, <30 oversold)" % (r4, r5))
    print("  ATR(14) 4h $%s = %.2f%% typical 4h move" % (f"{a4:,.0f}", a4 / px * 100))
    print("  Score %+d  ->  BIAS: %s" % (score, bias))

    print("\nPOSITION: $%.0f margin x %dx = $%s notional (%.5f BTC)" % (a.margin, a.lev, f"{notional:,.0f}", notional / px))
    print("  Fees ~%s round trip (%.2f%% per side)" % (money(-2 * notional * a.fee), a.fee * 100))
    for side in ("long", "short"):
        s = 1 if side == "long" else -1
        stop = px - s * a4
        liq = liq_price(px, side, a.lev, a.mmr)
        print("\n  %s %s" % ("LONG (buy) " if side == "long" else "SHORT (sell)", "<- bias" if bias.lower().startswith(side) else ""))
        print("    entry      $%s" % f"{px:,.0f}")
        print("    stop       $%s  (1 ATR, %.2f%%)  loss %s" % (f"{stop:,.0f}", a4 / px * 100, money(pnl(px, stop, side, notional, a.fee))))
        for r in (1, 2, 3):
            t = px + s * a4 * r
            print("    target %dR  $%s  gain %s" % (r, f"{t:,.0f}", money(pnl(px, t, side, notional, a.fee))))
        print("    LIQUIDATION $%s  (%.2f%% against you = whole $%.0f gone)" % (f"{liq:,.0f}", abs(liq / px - 1) * 100, a.margin))

    print("\nEVERY OUTCOME (P&L on $%.0f margin, fees included)" % a.margin)
    print("  %-8s %-10s %-16s %-16s" % ("move", "BTC price", "LONG", "SHORT"))
    for mv in (-10, -8, -5, -3, -2, -1, -0.5, 0, 0.5, 1, 2, 3, 5, 8, 10):
        p = px * (1 + mv / 100)
        row = []
        for side in ("long", "short"):
            liq = liq_price(px, side, a.lev, a.mmr)
            dead = (side == "long" and p <= liq) or (side == "short" and p >= liq)
            v = -a.margin if dead else pnl(px, p, side, notional, a.fee)
            row.append("%s (%+.0f%%)%s" % (money(v), v / a.margin * 100, " LIQ" if dead else ""))
        print("  %+5.1f%%   $%-9s %-16s %-16s" % (mv, f"{p:,.0f}", row[0], row[1]))
    print("\nPaper only. Not financial advice.")


def load():
    try:
        with open(STATE) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"open": None, "closed": []}


def save(st):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w") as fh:
        json.dump(st, fh, indent=2)


def mark(pos, px, a):
    notional = pos["margin"] * pos["lev"]
    liq = liq_price(pos["entry"], pos["side"], pos["lev"], a.mmr)
    dead = (pos["side"] == "long" and px <= liq) or (pos["side"] == "short" and px >= liq)
    v = -pos["margin"] if dead else pnl(pos["entry"], px, pos["side"], notional, a.fee)
    return v, liq, dead


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", nargs="?", default="breakdown", choices=["breakdown", "open", "status", "close"])
    p.add_argument("side", nargs="?", choices=["long", "short"])
    p.add_argument("--margin", type=float, default=100)
    p.add_argument("--lev", type=int, default=10)
    p.add_argument("--fee", type=float, default=0.0005)
    p.add_argument("--mmr", type=float, default=0.005)
    a = p.parse_args()
    if a.cmd == "breakdown":
        return breakdown(a)
    st = load()
    px = get("/simple/price?ids=bitcoin&vs_currencies=usd")["bitcoin"]["usd"]
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if a.cmd == "open":
        if st["open"]:
            sys.exit("A paper position is already open. Run status or close first.")
        if not a.side:
            sys.exit("Say long or short.")
        st["open"] = {"side": a.side, "entry": px, "margin": a.margin, "lev": a.lev, "opened": now}
        save(st)
        print("OPENED paper %s %dx at $%s, margin $%.0f, liquidation $%s" % (
            a.side.upper(), a.lev, f"{px:,.0f}", a.margin, f"{liq_price(px, a.side, a.lev, a.mmr):,.0f}"))
        return
    pos = st["open"]
    if not pos:
        sys.exit("No open paper position.")
    v, liq, dead = mark(pos, px, a)
    print("%s %dx  entry $%s  now $%s  liq $%s  P&L %s (%+.0f%%)%s" % (
        pos["side"].upper(), pos["lev"], f"{pos['entry']:,.0f}", f"{px:,.0f}", f"{liq:,.0f}",
        money(v), v / pos["margin"] * 100, "  LIQUIDATED" if dead else ""))
    if a.cmd == "close" or dead:
        pos.update(exit=px, closed=now, pnl=round(v, 2))
        st["closed"].append(pos)
        st["open"] = None
        save(st)
        total = sum(t["pnl"] for t in st["closed"])
        print("CLOSED. Paper trades: %d, total P&L %s" % (len(st["closed"]), money(total)))


if __name__ == "__main__":
    main()
