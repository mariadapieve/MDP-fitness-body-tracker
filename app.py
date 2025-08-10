
import os
import pandas as pd
import streamlit as st
import plotly.express as px

# ============ CONFIG ============ #
st.set_page_config(page_title="MDP Fitness Body Tracker", page_icon="💪", layout="wide")

# Logo opcional (no rompe si no está). Busca en /assets o en la raíz.
def show_logo():
    for p in ["assets/logo_main.png", "logo_main.png"]:
        if os.path.exists(p):
            st.image(p, use_container_width=True)
            return
    st.caption("Tip: podés subir tu logo como assets/logo_main.png (opcional).")

show_logo()
st.title("📊 MDP Fitness Body Tracker")

# ============ DATA ============ #
# Acepta CSV en /data/body_metrics.csv o /body_metrics.csv (raíz)
CSV_CANDIDATES = ["data/body_metrics.csv", "body_metrics.csv"]

def find_csv_path():
    for p in CSV_CANDIDATES:
        if os.path.exists(p):
            return p
    # si no hay, crea en raíz para evitar problemas de permisos
    os.makedirs("data", exist_ok=True)
    return "body_metrics.csv"

CSV_PATH = find_csv_path()

COLS = [
    "Fecha","Peso (kg)","% Grasa","Grasa (kg)","Músculo (kg)",
    "IMC","% Agua","Grasa visceral","TMB (kcal)"
]

def normalize_columns(df):
    # renombrados comunes -> estándar
    rename_map = {
        "date":"Fecha", "weight_kg":"Peso (kg)", "fat_percent":"% Grasa",
        "fat_kg":"Grasa (kg)", "muscle_kg":"Músculo (kg)", "bmi":"IMC",
        "water_percent":"% Agua", "visceral_fat":"Grasa visceral",
        "tmb_kcal":"TMB (kcal)"
    }
    df.rename(columns={k:v for k,v in rename_map.items() if k in df.columns}, inplace=True)
    for c in COLS:
        if c not in df.columns:
            df[c] = pd.NA
    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    return df[COLS].sort_values("Fecha")

@st.cache_data
def load_df(path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        try:
            raw = pd.read_csv(path)
            raw.columns = [c.strip() for c in raw.columns]
            return normalize_columns(raw)
        except Exception as e:
            st.error(f"No pude leer {path}: {e}")
    # si no existe o está vacío, crear estructura
    empty = pd.DataFrame(columns=COLS)
    return empty

def save_df(df, path):
    df.to_csv(path, index=False)

df = load_df(CSV_PATH)

# ============ UI ============ #
tab_hist, tab_add = st.tabs(["📈 Historial", "➕ Agregar medición"])

with tab_hist:
    st.subheader("Tabla de historial")
    st.dataframe(df, use_container_width=True)

    if not df.empty and df["Fecha"].notna().any():
        st.subheader("Peso, Grasa (kg) y Músculo (kg)")
        cols_focus = [c for c in ["Peso (kg)","Grasa (kg)","Músculo (kg)"] if c in df.columns]
        fig1 = px.line(df, x="Fecha", y=cols_focus, markers=True)
        fig1.update_layout(hovermode="x unified")
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader("Todas las métricas (sin TMB por escala)")
        cols_all = [c for c in ["Peso (kg)","% Grasa","Grasa (kg)","Músculo (kg)","IMC","% Agua","Grasa visceral"] if c in df.columns]
        if cols_all:
            fig2 = px.line(df, x="Fecha", y=cols_all, markers=True)
            fig2.update_layout(hovermode="x unified")
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Aún no hay datos. Cargá tu primera medición en la pestaña “Agregar medición”.")

with tab_add:
    st.subheader("Nueva medición")
    c1, c2, c3 = st.columns(3)
    with c1:
        fecha = st.date_input("Fecha")
        peso = st.number_input("Peso (kg)", min_value=0.0, step=0.1)
        grasa_pct = st.number_input("% Grasa", min_value=0.0, step=0.1)
    with c2:
        grasa_kg = st.number_input("Grasa (kg)", min_value=0.0, step=0.1)
        musculo = st.number_input("Músculo (kg)", min_value=0.0, step=0.1)
        imc = st.number_input("IMC", min_value=0.0, step=0.1)
    with c3:
        agua = st.number_input("% Agua", min_value=0.0, step=0.1)
        visceral = st.number_input("Grasa visceral", min_value=0.0, step=0.1)
        tmb = st.number_input("TMB (kcal)", min_value=0.0, step=1.0)

    # cálculo sugerido de grasa (kg)
    grasa_calc = None
    if (not grasa_kg) and peso and grasa_pct:
        grasa_calc = round(peso * (grasa_pct/100), 2)
        st.caption(f"↳ Sugerencia ‘Grasa (kg)’: **{grasa_calc}** (Peso × %Grasa)")

    if st.button("💾 Guardar medición"):
        new = pd.DataFrame([{
            "Fecha": pd.to_datetime(fecha),
            "Peso (kg)": peso if peso else pd.NA,
            "% Grasa": grasa_pct if grasa_pct else pd.NA,
            "Grasa (kg)": (grasa_calc if grasa_calc is not None else (grasa_kg if grasa_kg else pd.NA)),
            "Músculo (kg)": musculo if musculo else pd.NA,
            "IMC": imc if imc else pd.NA,
            "% Agua": agua if agua else pd.NA,
            "Grasa visceral": visceral if visceral else pd.NA,
            "TMB (kcal)": tmb if tmb else pd.NA
        }])
        out = pd.concat([df, new], ignore_index=True).sort_values("Fecha")
        save_df(out, CSV_PATH)
        st.success("✅ Guardado. Actualizando…")
        st.cache_data.clear()   # refresca cache
        st.rerun()

st.caption("Hecho con ❤️ en Streamlit. CSV aceptado en /data/body_metrics.csv o /body_metrics.csv")
