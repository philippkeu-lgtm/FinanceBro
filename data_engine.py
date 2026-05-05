import yfinance as yf
from pytrends.request import TrendReq
import pandas as pd
import os
import time

class FinancialDataEngine:
    def __init__(self, ticker, keyword):
        self.ticker = ticker
        self.keyword = keyword
        self.cache_file = f"data_cache_{ticker}.csv"

    def fetch_all(self):
        # 1. Preisdaten holen (YFinance ist meistens stabil)
        print(f"Lade Kurse für {self.ticker}...")
        try:
            price_data = yf.download(self.ticker, period="6mo", interval="1d")
            if isinstance(price_data.columns, pd.MultiIndex):
                price_data.columns = price_data.columns.get_level_values(0)
            price_df = price_data[['Close']].copy()
        except Exception as e:
            print(f"Fehler beim Laden der Kurse: {e}")
            return pd.DataFrame()

        # 2. Google Trends holen (mit "Notfall-Plan")
        print(f"Lade Trends für '{self.keyword}'...")
        trend_df = pd.DataFrame()
        
        try:
            # Wir versuchen es mit einem kleinen Timeout, um Google nicht zu provozieren
            pytrends = TrendReq(hl='de-DE', tz=360, retries=2, backoff_factor=0.1)
            pytrends.build_payload([self.keyword], timeframe='today 3-m')
            trend_df = pytrends.interest_over_time()
        except Exception as e:
            print(f"⚠️ Google Trends blockiert (Code 429 oder Timeout). Nutze Notfall-Modus.")

        # 3. Daten-Fusion mit Fallback-Logik
        if not trend_df.empty and self.keyword in trend_df.columns:
            # Erfolg: Trends sind da
            combined = pd.merge(price_df, trend_df[[self.keyword]], 
                                left_index=True, right_index=True, how='left')
            combined = combined.ffill().bfill() # Lücken füllen
            combined.to_csv(self.cache_file)
            return combined
        else:
            # Notfall: Nur Preise liefern (TimesFM funktioniert auch nur mit Preisen!)
            print("Info: Arbeite heute nur mit Preisdaten (kein Sentiment).")
            # Wir erstellen eine Fake-Trend-Spalte mit Nullen, damit das restliche Skript nicht abstürzt
            price_df[self.keyword] = 0 
            return price_df
