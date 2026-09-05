import pandas as pd
import numpy as np
from evidently import Report
from evidently.presets import DataDriftPreset

reference = pd.read_csv("data/reference.csv")

# Aplicar log-transform a las variables financieras sesgadas ANTES de medir drift
# (práctica estándar para ratios/ingresos, evita que la cola larga de la distribución
# oculte cambios reales en la mayoría de los datos)
cols_to_log = ["DebtRatio", "MonthlyIncome"]

reference_transformed = reference.copy()
for col in cols_to_log:
    reference_transformed[col] = np.log1p(reference_transformed[col])

for batch_name in ["batch_00", "batch_09"]:
    current = pd.read_csv(f"data/production_batches/{batch_name}.csv")
    current_transformed = current.copy()
    for col in cols_to_log:
        current_transformed[col] = np.log1p(current_transformed[col])

    report = Report([DataDriftPreset(method="psi", threshold=0.1)])
    my_eval = report.run(current_transformed, reference_transformed)
    result = my_eval.dict()

    print(f"\n--- {batch_name} ---")
    for m in result["metrics"]:
        if "DebtRatio" in m["metric_name"] or "MonthlyIncome" in m["metric_name"] or "Drifted" in m["metric_name"]:
            print(m["metric_name"], "->", m["value"])