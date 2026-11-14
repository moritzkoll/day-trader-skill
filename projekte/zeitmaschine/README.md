# Zeitmaschine – Testlabor

Eigenes Projekt, um Trade-Pläne mit der Zeitmaschine durchzuspielen,
unabhängig vom Rest des Repos.

Die Zeitmaschine nimmt einen Plan (Aktie, Tag, Einstieg, Stop, Ziel) und

1. spielt den Rest des Handelstags **10.000-mal** nach, Kerze für Kerze aus
   den echten 5-Minuten-Kerzen der Aktie der letzten rund 60 Handelstage, und
2. prüft, wie dieselbe Regel an jedem dieser echten Tage ausgegangen wäre.

Am Ende steht, wie oft zuerst das Ziel und wie oft zuerst der Stop erreicht
wurde, das durchschnittliche Ergebnis in R und ein Urteil
(z. B. „Close to break-even“).

Das ist eine Simulation aus der Vergangenheit, keine Vorhersage und keine
Anlageberatung.

## Ordner

| Pfad | Inhalt |
|---|---|
| `timemachine.py` | Kopie der Zeitmaschine aus `trader-timemachine/`, nur Python-Standardbibliothek |
| `start.sh` | startet einen Plan und speichert das Ergebnis |
| `plaene/` | ein Plan pro Datei (`.json`) |
| `plaene/VORLAGE.json` | Vorlage zum Kopieren |
| `ergebnisse/` | Ergebnisse, gleicher Name wie der Plan |

## So geht's

```bash
cd projekte/zeitmaschine

# 1. Vorlage kopieren und ausfüllen
cp plaene/VORLAGE.json plaene/nvda-2026-11-13.json

# 2. Zeitmaschine starten
./start.sh plaene/nvda-2026-11-13.json

# optional: früher aussteigen, andere Zufallszahl, weniger Durchläufe
./start.sh plaene/nvda-2026-11-13.json --until 15:55 --seed 7 --replays 5000
```

Ohne Plan-Datei geht es auch direkt:

```bash
python3 timemachine.py run --symbol NVDA --date 2026-11-13 \
  --entry 190.50 --stop 189.20 --target 193.10 --entry-time "10:15 AM"
```

## Felder im Plan

| Feld | Bedeutung |
|---|---|
| `symbol` | US-Ticker, z. B. `GLD`, `CRWV`, `NVDA` |
| `side` | `buy` (long) oder `sell` (short) |
| `date` | Handelstag, `JJJJ-MM-TT` |
| `entry` | Einstiegskurs |
| `entry_time` | Schlusszeit der Einstiegskerze in New Yorker Zeit, auf 5 Minuten genau (`10:15 AM`) |
| `stop` | Stop-Kurs (bei `buy` unter dem Einstieg) |
| `target` | Ziel-Kurs (bei `buy` über dem Einstieg) |
| `opening_range.minutes` | Länge der Eröffnungsspanne, Standard 15 |
| `stop_rule` | Regel für die Prüfung an vergangenen Tagen: `or_mid`, `or_low`, `pct` oder `auto` |
| `setup` | `orb` (Ausbruch über die Eröffnungsspanne); bei anderen Setups gibt es nur die 10.000 Durchläufe |

## Wichtig

- **Nur die letzten rund 60 Tage:** Yahoo liefert 5-Minuten-Kerzen nur für etwa
  60 Tage. Der Tag im Plan muss darin liegen, und der Vergleichszeitraum
  verschiebt sich mit jedem Tag. Ein alter Plan liefert später deshalb andere
  Zahlen.
- **Gleicher Seed = gleiche Zahlen**, solange die Kursdaten gleich sind.
  Standard ist `--seed 19`.
- **Uhrzeiten** im Plan sind New Yorker Zeit (US-Börse 9:30–16:00).
- Gebühren, Spread und Kurslücken über Nacht sind nicht eingerechnet.

## Beispiel im Ordner

`plaene/gld-2026-10-26.json`: Ausbruch von GLD über die ersten 15 Minuten am
26.10.2026, Einstieg 367,86 $ um 10:20 Uhr, Stop 367,02 $, Ziel 369,54 $ (2R).
Ergebnis in `ergebnisse/gld-2026-10-26.json`, Urteil: ungefähr Break-even.
