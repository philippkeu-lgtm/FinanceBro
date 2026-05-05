import pandas as pd
import numpy as np
import timesfm

class TimesFMForecaster:
    def __init__(self, context_len=128, horizon_len=7):
        """
        context_len: Wie viele Tage schauen wir zurück? (Standard: 128 Tage)
        horizon_len: Wie viele Tage sagen wir voraus? (Standard: 7 Tage)
        """
        self.context_len = context_len
        self.horizon_len = horizon_len
        
        print("Initialisiere Google TimesFM (Modell wird geladen)...")
        # Standard-Konfiguration für das 200M Modell
        self.tfm = timesfm.TimesFm(
            context_len=self.context_len,
            horizon_len=self.horizon_len,
            input_patch_len=32,
            output_patch_len=128,
            num_layers=20,
            model_dims=1280,
            backend='cpu' # Wir nutzen 'cpu', da das in GitHub Codespaces/Lokal am stabilsten läuft
        )
        
        # Lade die vortrainierten Gewichte direkt aus dem HuggingFace Hub
        self.tfm.load_from_checkpoint(repo_id="google/timesfm-1.0-200m")
        print("Modell erfolgreich geladen!")

    def predict(self, df, column_name='Close'):
        """
        Nimmt unseren DataFrame und generiert eine Vorhersage.
        """
        # 1. Daten bereinigen: Alle leeren Felder entfernen
        clean_data = df[column_name].dropna().values
        
        # 2. Prüfen, ob wir genug Historie haben
        if len(clean_data) < self.context_len:
            raise ValueError(f"Nicht genug Daten! Brauche {self.context_len} Tage, habe nur {len(clean_data)}.")

        # 3. Nur die letzten X Tage nehmen (Context Length)
        input_data = clean_data[-self.context_len:]
        
        print(f"Erstelle Prognose für die nächsten {self.horizon_len} Tage...")
        
        # 4. TimesFM erwartet eine Liste von Arrays (Batch-Processing)
        # Wir geben ihm ein Array mit unserem einen Asset
        forecast, _ = self.tfm.forecast([input_data])
        
        # 5. Das Ergebnis extrahieren (forecast[0] weil wir nur ein Asset abgefragt haben)
        predicted_values = forecast[0]
        
        return predicted_values
