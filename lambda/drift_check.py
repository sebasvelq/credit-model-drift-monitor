import boto3
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from evidently import Report
from evidently.presets import DataDriftPreset

s3 = boto3.client("s3")
sns = boto3.client("sns")

BUCKET = os.environ["BUCKET_NAME"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]
DRIFT_THRESHOLD = float(os.environ.get("DRIFT_THRESHOLD", "0.3"))

# Variables financieras sesgadas que necesitan log-transform antes de medir drift
COLS_TO_LOG = ["DebtRatio", "MonthlyIncome"]

def handler(event, context):
    s3.download_file(BUCKET, "reference-data/reference.csv", "/tmp/reference.csv")
    reference = pd.read_csv("/tmp/reference.csv")

    batch_key = event.get("batch_key")
    if not batch_key:
        objs = s3.list_objects_v2(Bucket=BUCKET, Prefix="production-data/")
        batch_key = sorted([o["Key"] for o in objs["Contents"]])[-1]

    s3.download_file(BUCKET, batch_key, "/tmp/current.csv")
    current = pd.read_csv("/tmp/current.csv")

    # Aplicar log-transform antes de calcular drift
    reference_transformed = reference.copy()
    current_transformed = current.copy()
    for col in COLS_TO_LOG:
        reference_transformed[col] = np.log1p(reference_transformed[col])
        current_transformed[col] = np.log1p(current_transformed[col])

    report = Report([DataDriftPreset(method="psi", threshold=0.1)])
    my_eval = report.run(current_transformed, reference_transformed)
    result = my_eval.dict()

    drift_info = result["metrics"][0]["value"]
    n_drifted = drift_info["count"]
    drift_share = drift_info["share"]
    dataset_drift = drift_share >= DRIFT_THRESHOLD

    metrics_record = {
        "timestamp": datetime.utcnow().isoformat(),
        "batch_key": batch_key,
        "dataset_drift": dataset_drift,
        "drift_share": drift_share,
        "n_drifted_columns": n_drifted,
    }
    metrics_key = f"metrics/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    s3.put_object(Bucket=BUCKET, Key=metrics_key, Body=json.dumps(metrics_record))

    if dataset_drift:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="⚠️ Drift detectado en modelo de producción",
            Message=f"Batch {batch_key} muestra drift_share={drift_share:.2f} "
                    f"({n_drifted} columnas afectadas). Revisar el dashboard."
        )

    return {"statusCode": 200, "body": json.dumps(metrics_record)}