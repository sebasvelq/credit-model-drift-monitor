import streamlit as st
import boto3
import json
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Drift Monitor", layout="wide")

s3 = boto3.client("s3")
BUCKET = "drift-monitoring-sebvq"  # tu bucket real

@st.cache_data(ttl=300)
def load_metrics():
    objs = s3.list_objects_v2(Bucket=BUCKET, Prefix="metrics/")
    records = []
    for o in objs.get("Contents", []):
        body = s3.get_object(Bucket=BUCKET, Key=o["Key"])["Body"].read()
        records.append(json.loads(body))
    df = pd.DataFrame(records)
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")
    return df

st.title("📊 Model Drift Monitoring Dashboard")
st.caption("Monitoreo automático de data drift — modelo de riesgo crediticio (Give Me Some Credit)")

df = load_metrics()

if df.empty:
    st.warning("Aún no hay métricas registradas. Corre la Lambda manualmente o espera al schedule automático.")
else:
    col1, col2, col3 = st.columns(3)
    latest = df.iloc[-1]
    col1.metric("Último drift_share", f"{latest['drift_share']:.2%}")
    col2.metric("Columnas con drift", int(latest["n_drifted_columns"]))
    col3.metric("¿Drift detectado?", "🔴 Sí" if latest["dataset_drift"] else "🟢 No")

    st.subheader("Evolución del drift_share en el tiempo")
    fig = px.line(df, x="timestamp", y="drift_share", markers=True)
    fig.add_hline(y=0.15, line_dash="dash", line_color="red", annotation_text="Umbral de alerta")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Historial de batches procesados")
    st.dataframe(df[["timestamp", "batch_key", "drift_share", "n_drifted_columns", "dataset_drift"]])

if st.button("🔄 Refrescar datos"):
    st.cache_data.clear()
    st.rerun()