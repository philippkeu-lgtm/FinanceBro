import yfinance as yf
from pytrends.request import TrendReq
import pandas as pd
import os
from datetime import datetime

class FinancialDataEngine:
    def __init__(self, ticker, keyword):
        self.ticker = ticker
        self.keyword = keyword
        self.cache_file = f"data_cache_{ticker}.csv"

    def fetch_all(self):
        # 1. Preisdaten (YFinance ist sehr stabil)
        print(f"Lade Kurse für {self.ticker}...")
        price_data = yf.download(self.ticker, period="3mo", interval="1d")
        price_df = price_data[['Close']].copy()

        # 2. Google Trends (mit Vorsicht genießen)
        print(f"Lade Trends für '{self.keyword}'...")
        try:
            pytrends = TrendReq(hl='de-DE', tz=360)
            pytrends.build_payload([self.keyword], timeframe='today 3-m')
            trend_df = pytrends.interest_over_time()
            
            # Zusammenführen (Merge)
            combined = pd.merge(price_df, trend_df[self.keyword], 
                                left_index=True, right_index=True, how='left')
            
            # Lücken füllen (falls am Wochenende keine Trends da sind)
            combined = combined.ffill()
            
            # Speichern für Stabilität
            combined.to_csv(self.cache_file)
            return combined
            
        except Exception as e:
            print(f"API Fehler: {e}. Nutze Cache, falls vorhanden.")
            if os.path.exists(self.cache_file):
                return pd.read_csv(self.cache_file, index_col=0)
            raise e

# Beispielaufruf:
# engine = FinancialDataEngine("BTC-USD", "Bitcoin")
# data = engine.fetch_all()
# print(data.tail())
