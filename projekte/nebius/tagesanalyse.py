#!/usr/bin/env python3
"""Nebius (oder jede andere US-Aktie) Tag fuer Tag in 5-Minuten-Kerzen zerlegen.

Aufruf:
    python3 tagesanalyse.py                 # NBIS, alle Tage, die Yahoo hat (ca. 60)
    python3 tagesanalyse.py --symbol CRWV   # andere Aktie
    python3 tagesanalyse.py --tage 10       # nur die letzten 10 Handelstage

Schreibt nach ausgabe/:
    <SYMBOL>_tage.csv        eine Zeile pro Handelstag (Semikolon, fuer Excel)
    <SYMBOL>_kerzen.csv      alle 5-Minuten-Kerzen
    <SYMBOL>_bericht.md      Zusammenfassung mit Mustern
Nur Python-Standardbibliothek. Kurse von Yahoo Finance (kostenlos, inoffiziell).
"""
import argparse, csv, datetime, json, os, statistics as st, sys, time, urllib.request
from collections import Counter
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
DE = ZoneInfo("Europe/Berlin")
UA = "Mozilla/5.0 (compatible; day-trader-skill tagesanalyse)"
WT = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def hole(symbol):
    last = None
    for host in ("https://query2.finance.yahoo.com", "https://query1.finance.yahoo.com"):
        try:
            url = f"{host}/v8/finance/chart/{symbol}?range=60d&interval=5m&includePrePost=false"
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)["chart"]["result"][0]
        except Exception as e:  # naechsten Host versuchen
            last = e
            time.sleep(2)
    sys.exit(f"Yahoo hat nicht geantwortet: {last}")


def kerzen(res):
    q = res["indicators"]["quote"][0]
    tage = {}
    for i, t in enumerate(res["timestamp"]):
        o, h, l, c, v = (q[k][i] for k in ("open", "high", "low", "close", "volume"))
        if None in (o, h, l, c):
            continue
        ny = datetime.datetime.fromtimestamp(t, NY)
        if not ((9, 30) <= (ny.hour, ny.minute) < (16, 0)):
            continue
        tage.setdefault(ny.date(), []).append(dict(ny=ny, o=o, h=h, l=l, c=c, v=v or 0))
    return tage


def de(ny):
    return ny.astimezone(DE).strftime("%H:%M")


def tag_auswerten(d, K, vorschluss):
    o, c = K[0]["o"], K[-1]["c"]
    hi = max(K, key=lambda k: k["h"]); lo = min(K, key=lambda k: k["l"])
    or_ = K[:3]
    orh, orl = max(k["h"] for k in or_), min(k["l"] for k in or_)
    aus_hoch = next((k for k in K[3:] if k["c"] > orh), None)
    aus_tief = next((k for k in K[3:] if k["c"] < orl), None)
    vol = sum(k["v"] for k in K)
    vwap = sum((k["h"] + k["l"] + k["c"]) / 3 * k["v"] for k in K) / vol if vol else c
    c30 = K[min(5, len(K) - 1)]["c"]
    pos = (c - lo["l"]) / (hi["h"] - lo["l"]) if hi["h"] > lo["l"] else 0.5
    gap = (o / vorschluss - 1) * 100 if vorschluss else None
    o2c = (c / o - 1) * 100
    # Muster
    if gap is not None and gap >= 1.5:
        muster = "Gap hoch & weiter" if o2c > 0.5 and pos > 0.7 else ("Gap hoch, abverkauft" if o2c < -0.5 else "Gap hoch, seitwaerts")
    elif gap is not None and gap <= -1.5:
        muster = "Gap tief, zurueckgekauft" if o2c > 0.5 else ("Gap tief & weiter runter" if o2c < -0.5 and pos < 0.3 else "Gap tief, seitwaerts")
    elif o2c > 0.5 and pos > 0.7:
        muster = "Trendtag hoch"
    elif o2c < -0.5 and pos < 0.3:
        muster = "Trendtag runter"
    else:
        muster = "Seitwaerts / unentschieden"
    zuerst = None
    if aus_hoch and (not aus_tief or aus_hoch["ny"] < aus_tief["ny"]):
        zuerst = "hoch"
    elif aus_tief:
        zuerst = "tief"
    # Ergebnis eines ORB-Long (erster Schluss ueber Range-Hoch -> Tagesschluss)
    orb_long = (c / aus_hoch["c"] - 1) * 100 if aus_hoch else None
    stunden = {}
    for k in K:
        stunden.setdefault(k["ny"].hour, []).append(k)
    return {
        "datum": d.isoformat(), "tag": WT[d.weekday()], "kerzen": len(K),
        "vortag_schluss": round(vorschluss, 2) if vorschluss else "",
        "eroeffnung": round(o, 2), "schluss": round(c, 2),
        "luecke_pct": round(gap, 2) if gap is not None else "",
        "tag_pct": round((c / vorschluss - 1) * 100, 2) if vorschluss else "",
        "eroeff_bis_schluss_pct": round(o2c, 2),
        "erste_30min_pct": round((c30 / o - 1) * 100, 2),
        "hoch": round(hi["h"], 2), "hoch_uhrzeit_de": de(hi["ny"]), "hoch_uhrzeit_ny": hi["ny"].strftime("%H:%M"),
        "tief": round(lo["l"], 2), "tief_uhrzeit_de": de(lo["ny"]), "tief_uhrzeit_ny": lo["ny"].strftime("%H:%M"),
        "spanne_pct": round((hi["h"] / lo["l"] - 1) * 100, 2),
        "schluss_position": round(pos, 2),
        "or15_hoch": round(orh, 2), "or15_tief": round(orl, 2),
        "ausbruch_hoch_de": de(aus_hoch["ny"]) if aus_hoch else "",
        "ausbruch_tief_de": de(aus_tief["ny"]) if aus_tief else "",
        "zuerst_gebrochen": zuerst or "keins",
        "orb_long_bis_schluss_pct": round(orb_long, 2) if orb_long is not None else "",
        "vwap": round(vwap, 2), "schluss_ueber_vwap": "ja" if c > vwap else "nein",
        "volumen": vol, "vol_erste_30min_pct": round(100 * sum(k["v"] for k in K[:6]) / vol, 1) if vol else "",
        "muster": muster,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="NBIS")
    ap.add_argument("--tage", type=int, default=0)
    a = ap.parse_args()
    sym = a.symbol.upper()
    os.makedirs("ausgabe", exist_ok=True)
    res = hole(sym)
    T = kerzen(res)
    heute = datetime.datetime.now(NY)
    tage = sorted(d for d, K in T.items() if len(K) >= 70 and not (d == heute.date() and heute.hour < 16))
    rows = []
    for i, d in enumerate(tage):
        vs = T[tage[i - 1]][-1]["c"] if i else None
        rows.append(tag_auswerten(d, T[d], vs))
    if a.tage:
        rows = rows[-a.tage:]
    with open(f"ausgabe/{sym}_tage.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter=";")
        w.writeheader()
        for r in rows:
            w.writerow({k: (str(v).replace(".", ",") if isinstance(v, float) else v) for k, v in r.items()})
    with open(f"ausgabe/{sym}_kerzen.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["datum", "uhrzeit_de", "uhrzeit_ny", "open", "high", "low", "close", "volumen"])
        for d in tage[-len(rows):]:
            for k in T[d]:
                w.writerow([d.isoformat(), de(k["ny"]), k["ny"].strftime("%H:%M")] +
                           [str(round(k[x], 3)).replace(".", ",") for x in "ohlc"] + [k["v"]])
    bericht(sym, rows)
    print(f"{len(rows)} Handelstage ({rows[0]['datum']} bis {rows[-1]['datum']}) -> ausgabe/{sym}_tage.csv, _kerzen.csv, _bericht.md")


def bericht(sym, rows):
    L = []
    n = len(rows)
    def pct(x): return f"{x:+.2f} %".replace(".", ",")
    L.append(f"# {sym}: Tagesanalyse in 5-Minuten-Kerzen\n")
    L.append(f"{n} Handelstage, {rows[0]['datum']} bis {rows[-1]['datum']}. Uhrzeiten in deutscher Zeit. Daten: Yahoo Finance.\n")
    tg = [r["tag_pct"] for r in rows if r["tag_pct"] != ""]
    L.append("## Ueberblick\n")
    L.append(f"- Tage im Plus: {sum(x > 0 for x in tg)} von {len(tg)}")
    L.append(f"- Typische Tagesspanne (Median Hoch zu Tief): {st.median(r['spanne_pct'] for r in rows):.1f} %".replace(".", ","))
    L.append(f"- Typische Luecke zur Eroeffnung (Median, Betrag): {st.median(abs(r['luecke_pct']) for r in rows if r['luecke_pct'] != ''):.1f} %".replace(".", ","))
    L.append(f"- Schluss ueber VWAP: {sum(r['schluss_ueber_vwap'] == 'ja' for r in rows)} von {n} Tagen")
    gl = sum((r["erste_30min_pct"] > 0) == (r["eroeff_bis_schluss_pct"] > 0) for r in rows)
    L.append(f"- Richtung der ersten 30 Minuten = Richtung bis Schluss: {gl} von {n} Tagen")
    lu = [r for r in rows if r["luecke_pct"] != "" and abs(r["luecke_pct"]) >= 1.5]
    if lu:
        weiter = sum((r["luecke_pct"] > 0) == (r["eroeff_bis_schluss_pct"] > 0) for r in lu)
        L.append(f"- Luecke ab 1,5 % lief in dieselbe Richtung weiter: {weiter} von {len(lu)}")
    L.append("\n## Muster\n")
    L.append("| Muster | Tage | Schnitt Tag |\n|---|---|---|")
    for m, k in Counter(r["muster"] for r in rows).most_common():
        v = [r["tag_pct"] for r in rows if r["muster"] == m and r["tag_pct"] != ""]
        L.append(f"| {m} | {k} | {pct(st.mean(v)) if v else '-'} |")
    L.append("\n## Ausbruch ueber die ersten 15 Minuten (9:30-9:45 NY = 15:30-15:45 DE)\n")
    z = Counter(r["zuerst_gebrochen"] for r in rows)
    L.append(f"- Zuerst nach oben gebrochen: {z['hoch']}, zuerst nach unten: {z['tief']}, keins: {z['keins']}")
    ol = [r["orb_long_bis_schluss_pct"] for r in rows if r["orb_long_bis_schluss_pct"] != ""]
    if ol:
        L.append(f"- Long beim ersten Schluss ueber dem Range-Hoch, Ausstieg zum Schluss: {len(ol)} Trades, "
                 f"Schnitt {pct(st.mean(ol))}, Gewinner {sum(x > 0 for x in ol)} von {len(ol)} (ohne Kosten)")
    L.append("\n## Wann liegen Hoch und Tief?\n")
    B = ("erste 30 Min (15:30-16:00 DE)", "2. Stunde (16:00-17:00 DE)", "Mittag (17:00-20:00 DE)", "letzte 2 Std (20:00-22:00 DE)")
    def blk(t):  # nach New Yorker Uhrzeit, damit die Zeitumstellung nicht stoert
        h, m = map(int, t.split(":")); x = h * 60 + m
        return B[0] if x < 600 else B[1] if x < 660 else B[2] if x < 840 else B[3]
    L.append("Zeiten im Normalfall; in den Wochen der Zeitumstellung eine Stunde frueher.\n")
    L.append("| Abschnitt | Tageshoch | Tagestief |\n|---|---|---|")
    hb = Counter(blk(r["hoch_uhrzeit_ny"]) for r in rows); tb = Counter(blk(r["tief_uhrzeit_ny"]) for r in rows)
    for b in B:
        L.append(f"| {b} | {hb[b]} | {tb[b]} |")
    L.append("\n## Jeder Tag\n")
    L.append("| Datum | Tag | Luecke | Tag ges. | Hoch (Zeit) | Tief (Zeit) | Spanne | Ausbruch | Muster |\n|---|---|---|---|---|---|---|---|---|")
    for r in reversed(rows):
        aus = f"oben {r['ausbruch_hoch_de']}" if r["zuerst_gebrochen"] == "hoch" else (f"unten {r['ausbruch_tief_de']}" if r["zuerst_gebrochen"] == "tief" else "-")
        L.append(f"| {r['datum']} | {r['tag']} | {pct(r['luecke_pct']) if r['luecke_pct'] != '' else '-'} | "
                 f"{pct(r['tag_pct']) if r['tag_pct'] != '' else '-'} | {r['hoch']} ({r['hoch_uhrzeit_de']}) | "
                 f"{r['tief']} ({r['tief_uhrzeit_de']}) | {str(r['spanne_pct']).replace('.', ',')} % | {aus} | {r['muster']} |")
    L.append("\nKeine Anlageberatung. Gebuehren und Spread sind nicht eingerechnet.")
    with open(f"ausgabe/{sym}_bericht.md", "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
