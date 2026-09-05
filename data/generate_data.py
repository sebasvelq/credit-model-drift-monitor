import pandas as pd
import numpy as np

np.random.seed(42)

df = pd.read_csv("cs-training.csv", index_col=0)
df = df.dropna(subset=["MonthlyIncome", "NumberOfDependents"])

debt_ratio_cap = df["DebtRatio"].quantile(0.99)
df = df[df["DebtRatio"] <= debt_ratio_cap]

print(f"Dataset cargado: {len(df)} filas tras limpieza (cap DebtRatio en {debt_ratio_cap:.2f})")

reference = df.sample(frac=0.7, random_state=42)
reference.to_csv("reference.csv", index=False)

rest = df.drop(reference.index).reset_index(drop=True)

n_batches = 10
batch_size = len(rest) // n_batches

for i in range(n_batches):
    batch = rest.iloc[i*batch_size : (i+1)*batch_size].copy()

    if i >= 5:
        drift_strength = (i - 4) * 0.5  # ahora crece más rápido: 0.5, 1.0, 1.5, 2.0, 2.5

        # Drift en DebtRatio: multiplicativo + un shift aditivo para que el cambio
        # sea detectable incluso en una distribución muy concentrada cerca de 0
        batch["DebtRatio"] = batch["DebtRatio"] * (1 + drift_strength) + (drift_strength * 0.5)

        # Drift en MonthlyIncome: caída más pronunciada
        batch["MonthlyIncome"] = batch["MonthlyIncome"] * (1 - 0.25 * drift_strength)
        batch["MonthlyIncome"] = batch["MonthlyIncome"].clip(lower=0)

    batch.to_csv(f"production_batches/batch_{i:02d}.csv", index=False)

print("Listo: reference.csv y 10 batches generados (batches 5-9 con drift más marcado en DebtRatio e ingreso)")