import yfinance as yf
from pytrends.request import TrendReq
import pandas as pd
import os

class FinancialDataEngine:
    def __init__(self, ticker, keyword):
        self.ticker = ticker
        self.keyword = keyword
        self.cache_file = f"data_cache_{ticker}.csv"

    def fetch_all(self):
        print(f"Lade Kurse für {self.ticker}...")
        # Preisdaten holen
        price_data = yf.download(self.ticker, period="3mo", interval="1d")
        
        # FIX: Falls yfinance MultiIndex-Spalten zurückgibt (2 Levels), 
        # nehmen wir nur das oberste Level oder benennen es flach um.
        if isinstance(price_data.columns, pd.MultiIndex):
            price_data.columns = price_data.columns.get_level_values(0)
            
        price_df = price_data[['Close']].copy()

        print(f"Lade Trends für '{self.keyword}'...")
        try:
            pytrends = TrendReq(hl='de-DE', tz=360)
            pytrends.build_payload([self.keyword], timeframe='today 3-m')
            trend_df = pytrends.interest_over_time()
            
            # Falls Google Trends leer ist oder nicht geladen werden kann
            if trend_df.empty:
                print("Warnung: Keine Google Trends Daten gefunden.")
                return price_df

            # Daten zusammenführen
            combined = pd.merge(price_df, trend_df[self.keyword], 
                                left_index=True, right_index=True, how='left')
            
            combined = combined.ffill()
            combined.to_csv(self.cache_file)
            return combined
            
        except Exception as e:
            print(f"API Fehler: {e}. Nutze Cache, falls vorhanden.")
            if os.path.exists(self.cache_file):
                return pd.read_csv(self.cache_file, index_col=0, parse_dates=True)
            return price_df # Falls kein Cache da ist, nimm nur die Preise
