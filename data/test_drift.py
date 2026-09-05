import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset

reference = pd.read_csv("reference.csv")
current = pd.read_csv("production_batches/batch_07.csv")  # uno con drift

report = Report([DataDriftPreset()])

# OJO: el orden es (current, reference) — al revés de lo que uno esperaría
my_eval = report.run(current, reference)

my_eval.save_html("drift_report_test.html")

result = my_eval.dict()

# El primer metric ahora es "DriftedColumnsCount", con count y share
drift_info = result["metrics"][0]["value"]
print(f"Columnas con drift: {drift_info['count']}")
print(f"% de columnas con drift: {drift_info['share']:.2%}")