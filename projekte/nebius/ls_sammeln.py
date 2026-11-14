#!/usr/bin/env python3
"""Tageskurse von Lang & Schwarz (L&S Exchange, in Euro) sichern.

L&S zeigt Minutenkurse nur fuer den laufenden Tag. Dieses Skript holt sie und
legt sie pro Tag ab, damit ein eigenes Archiv entsteht:
    ls_daten/<KUERZEL>/<JJJJ-MM-TT>.json

Aufruf (am besten jeden Abend nach 23:00 Uhr):
    python3 ls_sammeln.py                       # Nebius
    python3 ls_sammeln.py --kuerzel CRWV --id <L&S-Instrument-ID>

Die L&S-Instrument-ID findet man ueber die Suche auf ls-tc.de
(Nebius = 55010). Kurse sind Mittelkurse (zwischen Geld und Brief), ohne Volumen.
"""
import argparse, datetime, json, os, sys, urllib.request
from zoneinfo import ZoneInfo

DE = ZoneInfo("Europe/Berlin")
URL = ("https://www.ls-tc.de/_rpc/json/instrument/chart/dataForInstrument"
       "?instrumentId={id}&marketId=1&quotetype=mid&series=intraday&localeId=2")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kuerzel", default="NBIS")
    ap.add_argument("--id", type=int, default=55010)
    a = ap.parse_args()
    with urllib.request.urlopen(URL.format(id=a.id), timeout=30) as r:
        j = json.load(r)
    pts = j["series"]["intraday"]["data"]
    if not pts:
        sys.exit("L&S hat fuer heute keine Kurse geliefert.")
    vortag = next((p["value"] for p in j["info"].get("plotlines", []) if p.get("id") == "previousDay"), None)
    tag = datetime.datetime.fromtimestamp(pts[-1][0] / 1000, DE).date().isoformat()
    os.makedirs(f"ls_daten/{a.kuerzel}", exist_ok=True)
    pfad = f"ls_daten/{a.kuerzel}/{tag}.json"
    alt = []
    if os.path.exists(pfad):
        with open(pfad, encoding="utf-8") as f:
            alt = json.load(f).get("kurse", [])
    zus = {p[0]: p[1] for p in alt}
    zus.update({p[0]: p[1] for p in pts})
    kurse = sorted([t, v] for t, v in zus.items())
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump({"kuerzel": a.kuerzel, "ls_id": a.id, "datum": tag, "vortag_schluss": vortag,
                   "quelle": "Lang & Schwarz Exchange, Mittelkurs in EUR", "kurse": kurse}, f)
    erst = datetime.datetime.fromtimestamp(kurse[0][0] / 1000, DE).strftime("%H:%M")
    letzt = datetime.datetime.fromtimestamp(kurse[-1][0] / 1000, DE).strftime("%H:%M")
    print(f"{a.kuerzel} {tag}: {len(kurse)} Kurse von {erst} bis {letzt} Uhr -> {pfad}")


if __name__ == "__main__":
    main()
