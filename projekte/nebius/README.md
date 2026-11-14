# Nebius Tag für Tag

Zerlegt jeden Handelstag einer US-Aktie (Standard: Nebius, NBIS) in
5-Minuten-Kerzen und wertet ihn aus: Lücke zur Eröffnung, Hoch und Tief mit
Uhrzeit, Ausbruch aus den ersten 15 Minuten, VWAP, Volumen und das
Tagesmuster.

```bash
cd projekte/nebius
python3 tagesanalyse.py                 # NBIS, ca. 60 Handelstage (mehr hat Yahoo nicht)
python3 tagesanalyse.py --symbol CRWV   # andere Aktie
python3 tagesanalyse.py --tage 10       # nur die letzten 10 Tage
```

Ergebnisse in `ausgabe/`:

| Datei | Inhalt |
|---|---|
| `NBIS_bericht.md` | Zusammenfassung, Muster und eine Zeile pro Tag |
| `NBIS_tage.csv` | alle Kennzahlen pro Tag (Excel, Semikolon) |
| `NBIS_kerzen.csv` | jede 5-Minuten-Kerze mit deutscher und New Yorker Uhrzeit |

Nur Python-Standardbibliothek. Kurse: Yahoo Finance (kostenlos, inoffiziell,
leicht verzögert). Keine Anlageberatung.

## Lang & Schwarz (Euro, ab 14.11.2026)

L&S (ls-tc.de) zeigt Minutenkurse nur für den laufenden Tag. Deshalb wird ab
jetzt jeden Abend gesammelt:

```bash
python3 ls_sammeln.py        # holt den heutigen Tag nach ls_daten/NBIS/<Datum>.json
python3 ls_tagesanalyse.py   # wertet alle gesammelten Tage aus -> ausgabe/LS_NBIS_*
```

- Kurse sind **Mittelkurse in Euro** (zwischen Geld- und Briefkurs), ohne Volumen.
- Jeder Tag wird in drei Abschnitte geteilt: **vor US-Start** (L&S-Handel ab
  7:30), **US-Handel** (15:30–22:00, zur Zeitumstellung eine Stunde früher)
  und **Nachbörse** (bis 23:00).
- Daraus sieht man z. B., wie viel der Kurslücke zur US-Eröffnung bei L&S
  schon vorher passiert ist.
- Tagesschlusskurse bei L&S reichen bis 2011 zurück, Minutenkurse nur ab dem
  ersten Sammeltag.
