#!/usr/bin/env python3
"""Gesammelte L&S-Tage in 5-Minuten-Kerzen zerlegen und auswerten (Euro, deutsche Zeit).

Aufruf:
    python3 ls_tagesanalyse.py                  # Nebius, alle gesammelten Tage
    python3 ls_tagesanalyse.py --kuerzel CRWV

Schreibt nach ausgabe/:
    LS_<KUERZEL>_tage.csv     eine Zeile pro Tag
    LS_<KUERZEL>_kerzen.csv   alle 5-Minuten-Kerzen
    LS_<KUERZEL>_bericht.md   Zusammenfassung

Abschnitte eines L&S-Tages (deutsche Zeit, Mo-Fr):
    vor US-Start   bis zur US-Eroeffnung (15:30, zur Zeitumstellung 14:30)
    US-Handel      US-Eroeffnung bis US-Schluss (22:00 bzw. 21:00)
    Nachbörse      danach bis 23:00
"""
import argparse, csv, datetime, glob, json, os, statistics as st
from zoneinfo import ZoneInfo

DE = ZoneInfo("Europe/Berlin"); NY = ZoneInfo("America/New_York")
WT = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def us_zeiten(d):
    auf = datetime.datetime(d.year, d.month, d.day, 9, 30, tzinfo=NY).astimezone(DE)
    zu = datetime.datetime(d.year, d.month, d.day, 16, 0, tzinfo=NY).astimezone(DE)
    return auf, zu


def kerzen5(kurse):
    K = {}
    for t, v in kurse:
        dt = datetime.datetime.fromtimestamp(t / 1000, DE)
        k = dt.replace(minute=dt.minute // 5 * 5, second=0, microsecond=0)
        b = K.setdefault(k, {"t": k, "o": v, "h": v, "l": v, "c": v, "n": 0})
        b["h"] = max(b["h"], v); b["l"] = min(b["l"], v); b["c"] = v; b["n"] += 1
    return [K[k] for k in sorted(K)]


def pct(a, b):
    return round((b / a - 1) * 100, 2) if a else ""


def auswerten(dat):
    d = datetime.date.fromisoformat(dat["datum"])
    K = kerzen5(dat["kurse"])
    vs = dat.get("vortag_schluss")
    auf, zu = us_zeiten(d)
    vor = [k for k in K if k["t"] < auf]
    us = [k for k in K if auf <= k["t"] < zu]
    nach = [k for k in K if k["t"] >= zu]
    hi = max(K, key=lambda k: k["h"]); lo = min(K, key=lambda k: k["l"])
    erster, letzter = K[0], K[-1]
    us_start = us[0]["o"] if us else None
    r = {
        "datum": dat["datum"], "tag": WT[d.weekday()], "kerzen_5min": len(K),
        "vortag_schluss": vs or "", "erster_kurs": erster["o"], "erster_kurs_uhrzeit": erster["t"].strftime("%H:%M"),
        "schluss": letzter["c"], "schluss_uhrzeit": letzter["t"].strftime("%H:%M"),
        "tag_pct": pct(vs, letzter["c"]) if vs else "",
        "hoch": hi["h"], "hoch_uhrzeit": hi["t"].strftime("%H:%M"),
        "tief": lo["l"], "tief_uhrzeit": lo["t"].strftime("%H:%M"),
        "spanne_pct": pct(lo["l"], hi["h"]),
        "vor_us_start_pct": pct(vs, vor[-1]["c"]) if (vs and vor) else "",
        "kurs_bei_us_start": us_start or "",
        "us_handel_pct": pct(us_start, us[-1]["c"]) if us else "",
        "nachboerse_pct": pct(us[-1]["c"], nach[-1]["c"]) if (us and nach) else "",
        "us_start_uhrzeit": auf.strftime("%H:%M"),
    }
    if vs and us_start:
        gesamt = us_start / vs - 1
        vorweg = (vor[-1]["c"] / vs - 1) if vor else 0
        r["anteil_luecke_vor_us_start"] = round(100 * vorweg / gesamt) if abs(gesamt) > 0.003 else ""
    else:
        r["anteil_luecke_vor_us_start"] = ""
    return r, K


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kuerzel", default="NBIS")
    a = ap.parse_args()
    dateien = sorted(glob.glob(f"ls_daten/{a.kuerzel}/*.json"))
    if not dateien:
        raise SystemExit("Noch keine L&S-Daten gesammelt: erst ls_sammeln.py laufen lassen.")
    rows, alle = [], []
    for f in dateien:
        with open(f, encoding="utf-8") as fh:
            dat = json.load(fh)
        if not dat.get("kurse"):
            continue
        r, K = auswerten(dat)
        rows.append(r); alle += [(dat["datum"], k) for k in K]
    os.makedirs("ausgabe", exist_ok=True)
    zahl = lambda v: str(v).replace(".", ",") if isinstance(v, float) else v
    with open(f"ausgabe/LS_{a.kuerzel}_tage.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter=";"); w.writeheader()
        for r in rows: w.writerow({k: zahl(v) for k, v in r.items()})
    with open(f"ausgabe/LS_{a.kuerzel}_kerzen.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh, delimiter=";"); w.writerow(["datum", "uhrzeit", "open", "high", "low", "close", "kurse_in_kerze"])
        for d, k in alle: w.writerow([d, k["t"].strftime("%H:%M"), zahl(k["o"]), zahl(k["h"]), zahl(k["l"]), zahl(k["c"]), k["n"]])
    L = [f"# {a.kuerzel} bei Lang & Schwarz (Euro, deutsche Zeit)\n",
         f"{len(rows)} gesammelte Tage. Mittelkurse von ls-tc.de, ohne Volumen. Keine Anlageberatung.\n",
         "| Datum | Tag | Vortag | Tag ges. | vor US-Start | US-Handel | Nachbörse | Hoch (Zeit) | Tief (Zeit) | Spanne |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    f = lambda v: (f"{v:+.2f} %".replace(".", ",") if v != "" else "-")
    for r in reversed(rows):
        L.append(f"| {r['datum']} | {r['tag']} | {zahl(r['vortag_schluss'])} € | {f(r['tag_pct'])} | {f(r['vor_us_start_pct'])} | "
                 f"{f(r['us_handel_pct'])} | {f(r['nachboerse_pct'])} | {zahl(r['hoch'])} € ({r['hoch_uhrzeit']}) | "
                 f"{zahl(r['tief'])} € ({r['tief_uhrzeit']}) | {f(r['spanne_pct'])} |")
    werk = [r for r in rows if r["tag"] not in ("Sa", "So") and r["anteil_luecke_vor_us_start"] != ""]
    if len(werk) >= 3:
        L.append(f"\nIm Median passierte {st.median(r['anteil_luecke_vor_us_start'] for r in werk)} % der Bewegung bis zur "
                 "US-Eröffnung schon vorher bei L&S.")
    with open(f"ausgabe/LS_{a.kuerzel}_bericht.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"{len(rows)} L&S-Tage ausgewertet -> ausgabe/LS_{a.kuerzel}_tage.csv, _kerzen.csv, _bericht.md")


if __name__ == "__main__":
    main()
