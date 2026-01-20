####################################################################
#--- Forex Candle Continuity Theory Simulation---
# von Jerzy E. Samp
# bitte readme.txt lesen!
####################################################################

import pandas as pd

# --- Konfiguration ---
filename = "EUR_CHF_1.csv"  # Dateiname der CSV mit den historischen Kursdaten
pip_value = 0.0001          
# Umrechnungsfaktor: 1 PIP (Price Interest Point) = 4. Nachkommastelle
# Hinweis: Die kleinste Bewegung wäre ein "Pipette" (0.00001), wir rechnen hier aber in Pips.

# --- Trading Parameter ---
take_profit_bull = 20  # Ziel-Gewinn (Take Profit) für Long-Trades in Pips
stop_loss_bull   = 10  # Maximaler Verlust (Stop Loss) für Long-Trades in Pips

take_profit_bear = 20  # Ziel-Gewinn (Take Profit) für Short-Trades in Pips
stop_loss_bear   = 10  # Maximaler Verlust (Stop Loss) für Short-Trades in Pips


# --- Historische Daten einlesen ---
df = pd.read_csv(filename) # Lädt die CSV in einen Pandas DataFrame
df = df.iloc[::-1].reset_index(drop=True) # Dreht die Daten um (älteste zuerst) und repariert den Index

# --- Statistik-Variablen ---

win  = 0  # Zähler für alle Trades, die im Gewinn (Take Profit) geschlossen wurden
loss = 0  # Zähler für alle Trades, die im Verlust (Stop Loss) geschlossen wurden
count = 0 # Iterations-Zähler (zählt die durchlaufenen Kerzen/Zeitschritte)

bear_signal = 0 # Zähler für erkannte Short-Einstiegssignale (Verkauf)
bull_signal = 0 # Zähler für erkannte Long-Einstiegssignale (Kauf)

# Diese Variablen summieren die Pips, um später den Durchschnitt zu berechnen

total_pips_win_bull  = 0 # Summe aller gewonnenen Pips aus Long-Trades
total_pips_loss_bull = 0 # Summe aller verlorenen Pips aus Long-Trades

total_pips_win_bear  = 0 # Summe aller gewonnenen Pips aus Short-Trades
total_pips_loss_bear = 0 # Summe aller verlorenen Pips aus Short-Trades

high_crv_trades = 0  # Zähler für Trades mit hohem Chance-Risiko-Verhältnis (risk-reward-ratio)(Gewinn > 3x Verlust)


# --- Strategie-Parameter ("Candle Continuity Theory") ---
min_continuous_candles = 5  # Wie viele Kerzen müssen gleiche Farbe haben? (Hier: 5)
min_body_size = 0.0010      # Mindestgröße des Körpers (0.0010 = 10 Pips), um Rauschen zu filtern

# --- Feature Engineering (Kerzen-Attribute) ---
# Berechnet die absolute Größe des Kerzenkörpers (Differenz Open vs Close)
df['Candle_Body'] = abs(df['Close'] - df['Open'])

# Bestimmt die Richtung: True = Grün (Bullish), False = Rot (Bearish)
df['Candle_Direction'] = df['Close'] > df['Open']

# --- Vektorisierte Streak-Berechnung ---
# Diese Logik zählt, wie oft hintereinander die gleiche Kerzenfarbe auftritt,
# OHNE eine langsame Schleife zu benutzen (Pandas GroupBy-Trick).

# 1. (df['Candle_Direction'] != df['Candle_Direction'].shift()) erkennt Farbwechsel.
# 2. .cumsum() erstellt für jeden Block gleicher Farben eine eigene Gruppen-ID.
# 3. .groupby(...) gruppiert diese Blöcke.
# 4. .cumsum() zählt dann innerhalb des Blocks hoch (1, 2, 3, 4, 5...).
df['Bullish_Streak'] = (df['Candle_Direction']).astype(int).groupby((df['Candle_Direction'] != df['Candle_Direction'].shift()).cumsum()).cumsum()

df['Bearish_Streak'] = (~df['Candle_Direction']).astype(int).groupby((df['Candle_Direction'] != df['Candle_Direction'].shift()).cumsum()).cumsum()


# --- Simulationslauf ---
for i in range(len(df) - 1):
    count += 1
    
    # Nächste Kerze definieren (Das ist die Kerze, in der wir traden)
    entry_price = df['Open'].iloc[i + 1]
    high_price  = df['High'].iloc[i + 1]
    low_price   = df['Low'].iloc[i + 1]

    # ---------------------------------------------------------
    # LONG SZENARIO (Wir wetten auf steigende Kurse)
    # ---------------------------------------------------------
    if df['Bullish_Streak'].iloc[i] >= min_continuous_candles and df['Candle_Body'].iloc[i] >= min_body_size:
        bull_signal += 1
        
        # Berechne die maximale Bewegung, die in dieser Kerze möglich war
        # (Wichtig für die Statistik: Wie viel "Potenzial" hatte das Signal?)
        potential_profit = (high_price - entry_price) / pip_value
        potential_loss   = (entry_price - low_price) / pip_value

        # Statistik aktualisieren (Summe der Bewegungen)
        total_pips_win_bull += potential_profit
        total_pips_loss_bull += potential_loss
        
        # Hatte dieser Trade ein extrem gutes Chance-Risiko-Verhältnis? (> 3:1)
        if potential_profit > potential_loss * 3:
            high_crv_trades += 1
        
        # --- Ergebnis-Prüfung (Win oder Loss?) ---
        # Logik: Haben wir den Take Profit (TP) erreicht, OHNE vorher den Stop Loss (SL) zu berühren?
        # Hinweis: Da wir OHLC (OPEN, HIGH, LOW, ClOSE) Daten nutzen, nehmen wir im Best-Case an, dass SL nicht zuerst getroffen wurde.
        
        tp_hit = potential_profit >= take_profit_bull
        sl_hit = potential_loss >= stop_loss_bull
        
        if tp_hit and not sl_hit:
            win += 1
        elif sl_hit:
            loss += 1
        else:
            # Weder TP noch SL erreicht -> Trade läuft weiter (oder wird am Ende der Kerze geschlossen)
            # In dieser einfachen Simulation ignorieren wir "Unentschieden" oder werten es als neutral.
            pass 

        # Debugging (Nur ent-kommentieren, wenn man einzelne Trades prüfen will)
        # print(f'Long Signal! Max Profit: {potential_profit:.1f}, Max Loss: {potential_loss:.1f}')


    # ---------------------------------------------------------
    # SHORT SZENARIO (Wir wetten auf fallende Kurse)
    # ---------------------------------------------------------
    elif df['Bearish_Streak'].iloc[i] >= min_continuous_candles and df['Candle_Body'].iloc[i] >= min_body_size:
        bear_signal += 1
        
        # Bei Short ist Gewinn, wenn der Preis fällt (Entry - Low)
        potential_profit = (entry_price - low_price) / pip_value
        potential_loss   = (high_price - entry_price) / pip_value

        total_pips_win_bear += potential_profit
        total_pips_loss_bear += potential_loss
        
        # CRV Check
        if potential_profit > potential_loss * 3:
            high_crv_trades += 1
            
        # --- Ergebnis-Prüfung ---
        tp_hit = potential_profit >= take_profit_bear
        sl_hit = potential_loss >= stop_loss_bear
        
        if tp_hit and not sl_hit:
            win += 1
        elif sl_hit:
            loss += 1
        else:
            pass
            
        # print(f'Short Signal! Max Profit: {potential_profit:.1f}, Max Loss: {potential_loss:.1f}')


# --- REPORTING ---

# Überschrift für bessere Lesbarkeit im Terminal
print("\n" + "="*40)
print(f"   BACKTEST REPORT: {filename}")
print("="*40)

# Gesamtzahlen
total_trades = win + loss
win_ratio = win / total_trades if total_trades > 0 else 0.0

# Realisierten Gewinn/Verlust berechnen
# Logik: Anzahl Gewinne * 20 Pips MINUS Anzahl Verluste * 10 Pips
net_pips = (win * take_profit_bull) - (loss * stop_loss_bull)

print(f"Gesamt Trades:      {total_trades}")
print(f"Gewinn-Trades (TP): {win}")
print(f"Verlust-Trades (SL):{loss}")
print(f"Win-Rate:           {win_ratio:.2%}")
print(f"Netto-Ergebnis:     {net_pips} Pips")

print("-" * 40)

# --- Bullish Statistik ---
# Wir prüfen erst, ob es überhaupt Signale gab, um "Teilen durch Null" zu verhindern.
if bull_signal > 0:
    avg_win_bull  = total_pips_win_bull / bull_signal
    avg_loss_bull = total_pips_loss_bull / bull_signal
    
    print(f"Long-Signale:       {bull_signal}")
    print(f"Durchschnittliches Gewinnpotential (Long):    {avg_win_bull:.1f} Pips")  # .1f heißt: 1 Nachkommastelle
    print(f"Durchschnittliches Verlustpotential (Long):   {avg_loss_bull:.1f} Pips")
else:
    print("Keine Long-Signale generiert.")

print("-" * 40)

# --- Bearish Statistik ---
if bear_signal > 0:
    avg_win_bear  = total_pips_win_bear / bear_signal
    avg_loss_bear = total_pips_loss_bear / bear_signal
    
    print(f"Short-Signale:      {bear_signal}")
    print(f"Durchschnittliches Gewinnpotential (Short):   {avg_win_bear:.1f} Pips")
    print(f"Durchschnittliches Verlustpotential (Short):  {avg_loss_bear:.1f} Pips")
else:
    print("Keine Short-Signale generiert.")

print("-" * 40)

# --- High Quality Trades (CRV > 3) ---
# Hier nutzen wir unsere umbenannte Variable "high_crv_trades" (statt "yes")
quality_ratio = high_crv_trades / total_trades if total_trades > 0 else 0.0

print(f"Trades mit CRV > 3: {high_crv_trades}")
print(f"Anteil der dicken Fische: {quality_ratio:.2%}")
print("="*40)