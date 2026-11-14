#!/usr/bin/env python3
"""Test: Startet Nebius morgens (L&S, 7:30) im Minus -> SHORT, im Plus -> LONG.
Einstieg 8:00, Ausstieg 21:30 deutscher Zeit. Letzte N Handelstage.

L&S-Minutenkurse gibt es rueckwirkend nicht. Daher eine Naeherung mit US-Daten
(Yahoo, Stundenkerzen inkl. Vor- und Nachboerse, in USD):
  - L&S-Schluss am Vorabend (23:00 DE)  = US-Kurs zur selben Uhrzeit (Nachboerse)
  - L&S-Start/Einstieg am Morgen (8:00) = letzter US-Nachboersenkurs des Vortags,
    denn zwischen 20:00 NY und 4:00 NY handelt in den USA niemand
  - Ausstieg 21:30 DE                   = US-Kurs zur selben Uhrzeit
Ohne Waehrungseffekt EUR/USD, ohne Kosten (optional --kosten).
"""
import argparse, datetime, json, statistics as st, urllib.request
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York"); DE = ZoneInfo("Europe/Berlin")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="NBIS")
    ap.add_argument("--tage", type=int, default=100)
    ap.add_argument("--kosten", type=float, default=0.0, help="Kosten je Trade in %, z. B. 0.2")
    a = ap.parse_args()
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{a.symbol}?range=1y&interval=60m&includePrePost=true"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; day-trader-skill test)"})
    res = json.load(urllib.request.urlopen(req, timeout=30))["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    tage = {}
    for t, o, c in zip(res["timestamp"], q["open"], q["close"]):
        if c is None:
            continue
        s = datetime.datetime.fromtimestamp(t, NY)
        tage.setdefault(s.date(), []).append((s, o, c))
    D = sorted(tage)

    def kurs(d, t):
        B = tage[d]
        for s, o, c in B:
            if s == t:
                return o
        vor = [(s, o) for s, o, c in B if s <= t]
        return vor[-1][1] if vor else None

    zeilen = []
    for d0, d1 in zip(D, D[1:]):
        vorabend = kurs(d0, datetime.datetime.combine(d0, datetime.time(23, 0), DE).astimezone(NY))
        einstieg = tage[d0][-1][2]
        aus = kurs(d1, datetime.datetime.combine(d1, datetime.time(21, 30), DE).astimezone(NY))
        if not vorabend or not aus:
            continue
        seite = "LONG" if einstieg > vorabend else "SHORT" if einstieg < vorabend else "-"
        r = (aus / einstieg - 1) * 100
        erg = (r if seite == "LONG" else -r if seite == "SHORT" else 0) - (a.kosten if seite != "-" else 0)
        zeilen.append((d1, seite, (einstieg / vorabend - 1) * 100, einstieg, aus, erg))
    zeilen = zeilen[-a.tage:]
    T = [z for z in zeilen if z[1] != "-"]
    kette = 1
    for z in T:
        kette *= 1 + z[5] / 100
    print(f"{a.symbol}: {len(zeilen)} Tage ({zeilen[0][0]} bis {zeilen[-1][0]}), {len(T)} Trades")
    for seite in ("LONG", "SHORT", None):
        L = [z[5] for z in T if seite in (None, z[1])]
        print(f"  {seite or 'GESAMT':6s} n={len(L):3d}  Schnitt {st.mean(L):+.2f} %  Gewinner {sum(x > 0 for x in L)}/{len(L)}")
    print(f"  Kette (jeden Trade voll reinvestiert): {100 * (kette - 1):+.1f} %  (Kosten je Trade {a.kosten} %)")
    print("\nDatum       Seite  Start   Einstieg  Ausstieg  Ergebnis")
    for d, s, sig, e, x, r in zeilen:
        print(f"{d}  {s:5s}  {sig:+5.2f}%  {e:8.2f}  {x:8.2f}  {r:+6.2f}%")


if __name__ == "__main__":
    main()
