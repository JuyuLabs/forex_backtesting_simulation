# Forex Backtesting Simulation (Python & Pandas)

Dieses Projekt ist eine Backtesting-Simulation zur Analyse von Handelsstrategien auf historischen Währungsdaten (Forex). Der Fokus liegt auf der performanten Verarbeitung von Zeitreihendaten mittels Pandas, ohne auf langsame Iterationen zurückgreifen zu müssen.

## Die Strategie: "Candle Continuity Theory"

Der Algorithmus basiert auf einer Momentum-Strategie, die Trendfortsetzungen identifiziert.

* **Logik:** Der Code analysiert die historischen Kerzen (Candles) und sucht nach einer **Serie von 5 aufeinanderfolgenden Kerzen** derselben Farbe (z.B. 5x grün/bullish).
* **Annahme:** Eine solche Serie deutet auf einen starken Kauf- oder Verkaufsdruck hin ("Momentum").
* **Ausführung:** Sobald dieses Muster erkannt wird (und der Kerzenkörper eine Mindestgröße hat, um Rauschen zu filtern), wird eine Position in Trendrichtung eröffnet.

## Limitationen & Optimierungspotenzial

Da es sich um einen Prototypen zu Studienzwecken handelt, wurden bewusst vereinfachende Annahmen getroffen. Für den Einsatz im Live-Trading müssten folgende Punkte adressiert werden:

### 1. Zeitliche Auflösung (OHLC vs. Tick-Daten)
**Das Problem:** Die Simulation nutzt OHLC-Daten (Open, High, Low, Close). Innerhalb einer Kerze ist nicht ersichtlich, ob der Preis zuerst das Gewinnziel (Take Profit) oder die Verlustgrenze (Stop Loss) erreicht hat, wenn beide Preise innerhalb der Spanne liegen.
* *Aktuelle Implementierung:* Es wird der **optimistische Fall** angenommen (Best-Case: TP wurde zuerst getroffen).
* *Lösung:* Nutzung von **Tick-Daten** (jede einzelne Preisänderung), um den exakten zeitlichen Verlauf innerhalb der Kerze zu simulieren.

### 2. Trade-Management (Carry-Over)
**Das Problem:** Wenn innerhalb einer Kerze weder Take Profit noch Stop Loss ausgelöst werden, wird der Trade aktuell ignoriert ("Time-Exit" ohne Wertung).
* *Aktuelle Implementierung:* Der Trade taucht nicht in der Statistik auf.
* *Lösung A:* Schließung der Position am Ende der Kerze (Close-Preis), was zu kleinen Gewinnen oder Verlusten führt.
* *Lösung B:* **Carry-Over Logik**: Die Position wird in die nächste Kerze "mitgenommen" und bleibt offen, bis TP oder SL getroffen wird.

### 3. Transaktionskosten
**Das Problem:** Broker berechnen für jeden Trade Gebühren (Spread oder Commission). Diese schmälern den realen Gewinn erheblich.
* *Aktuelle Implementierung:* Berechnung der Brutto-Ergebnisse (ohne Gebühren).
* *Lösung:* Implementierung eines Kostenmodells (z.B. Abzug von 1-2 Pips pro Trade), um die Netto-Profitabilität realistisch zu bewerten.
