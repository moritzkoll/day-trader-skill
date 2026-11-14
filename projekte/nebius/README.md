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

## Test „Start 23:00→7:30, Einstieg 8:00, Ausstieg 21:30“ – Stand 14.11.2026

`test_0800_2130.py` und `ausgabe/UNGUELTIG_test_0800_2130_tage.csv` sind **nicht
verlässlich**: Der L&S-Kurs um 7:30 Uhr folgt dem US-Nachthandel (2:00–10:00 Uhr
deutscher Zeit), der in den Yahoo-Daten fehlt. An rund einem Drittel der Tage
kommt deshalb die falsche Seite (LONG statt SHORT oder umgekehrt) heraus,
z. B. am 13.11.2026. Ein sauberer Test geht nur mit echten L&S-Kursen, die ab
jetzt mit `ls_sammeln.py` gesammelt werden.
