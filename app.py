
import os
import pandas as pd
import streamlit as st
import plotly.express as px

# ===================== CONFIGURACIÓN =====================
st.set_page_config(
    page_title="MDP Fitness Body Tracker",
    page_icon="💪",
    layout="wide"
)

# Branding opcional (no rompe si falta el logo)
LOGO_PATH = "assets/logo_main.png"
if os.path.exists(LOGO_PATH):
    st.image(LOGO_PATH, use_container_width=True)
else:
    st.caption("Tip: podés subir tu logo en assets/logo_main.png (opcional).")

st.title("📊 MDP Fitness Body Tracker")

CSV_PATH = "data/body_metrics.csv"
COLS = [
    "Fecha",            # fecha (YYYY-MM-DD)
    "Peso (kg)",
    "% Grasa",
    "Grasa (kg)",
    "Músculo (kg)",
    "IMC",
    "% Agua",
    "Grasa visceral",
    "TMB (kcal)"
]

# ===================== DATA =====================
@st.cache_data
def load_data():
    """Carga el CSV y lo normaliza. Si no existe, devuelve un DF vacío con las columnas esperadas."""
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        df.columns = [c.strip() for c in df.columns]
        # Mapear nombres alternativos -> estándar
        rename_map = {
            "date": "Fecha", "weight_kg": "Peso (kg)", "fat_percent": "% Grasa",
            "fat_kg": "Grasa (kg)", "muscle_kg": "Músculo (kg)", "bmi": "IMC",
            "water_percent": "% Agua", "visceral_fat": "Grasa visceral",
            "tmb_kcal": "TMB (kcal)"
        }
        df.rename(columns={k:v for k,v in rename_map.items() if k in df.columns}, inplace=True)
        # Asegurar columnas
        for c in COLS:
            if c not in df.columns:
                df[c] = pd.NA
        # Fecha a datetime
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        df = df[COLS].sort_values("Fecha")
        return df
    else:
        # Si no hay CSV, crear estructura vacía
        os.makedirs("data", exist_ok=True)
        empty = pd.DataFrame(columns=COLS)
        empty.to_csv(CSV_PATH, index=False)
        return empty

def save_data(df):
    os.makedirs("data", exist_ok=True)
    df.to_csv(CSV_PATH, index=False)

df = load_data()

# ===================== UI: TABS =====================
tab_hist, tab_add = st.tabs(["📈 Historial", "➕ Agregar medición"])

# --------------------- TAB HISTORIAL ---------------------
with tab_hist:
    st.subheader("Tabla de historial")
    st.dataframe(df, use_container_width=True)

    if not df.empty and df["Fecha"].notna().any():
        st.subheader("Gráfico: Peso, Grasa (kg) y Músculo (kg)")
        y_focus = [c for c in ["Peso (kg)", "Grasa (kg)", "Músculo (kg)"] if c in df.columns]
        fig_focus = px.line(df, x="Fecha", y=y_focus, markers=True)
        fig_focus.update_layout(hovermode="x unified")
        st.plotly_chart(fig_focus, use_container_width=True)

        st.subheader("Gráfico: Todas las métricas (excepto TMB por escala)")
        y_all = [c for c in ["Peso (kg)", "% Grasa", "Grasa (kg)", "Músculo (kg)", "IMC", "% Agua", "Grasa visceral"] if c in df.columns]
        fig_all = px.line(df, x="Fecha", y=y_all, markers=True)
        fig_all.update_layout(hovermode="x unified")
        st.plotly_chart(fig_all, use_container_width=True)
    else:
        st.info("Aún no hay datos. Cargá tu primera medición en la pestaña “Agregar medición”.")

# --------------------- TAB AGREGAR ---------------------
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

    # Autocálculo de Grasa (kg) si no se carga manualmente
    if (not grasa_kg) and peso and grasa_pct:
        grasa_kg_calc = round(peso * (grasa_pct/100), 2)
        st.caption(f"↳ Sugerido Grasa (kg): **{grasa_kg_calc}** (calculado con Peso × %Grasa)")
    else:
        grasa_kg_calc = grasa_kg

    if st.button("💾 Guardar medición"):
        new = pd.DataFrame([{
            "Fecha": pd.to_datetime(fecha),
            "Peso (kg)": peso if peso else pd.NA,
            "% Grasa": grasa_pct if grasa_pct else pd.NA,
            "Grasa (kg)": grasa_kg_calc if grasa_kg_calc else pd.NA,
            "Músculo (kg)": musculo if musculo else pd.NA,
            "IMC": imc if imc else pd.NA,
            "% Agua": agua if agua else pd.NA,
            "Grasa visceral": visceral if visceral else pd.NA,
            "TMB (kcal)": tmb if tmb else pd.NA
        }])

        out = pd.concat([df, new], ignore_index=True).sort_values("Fecha")
        save_data(out)
        st.success("✅ Medición guardada. Actualizá la pestaña de historial para verla.")
        st.rerun()

st.caption("Hecho con ❤️ en Streamlit. Editá tus datos en data/body_metrics.csv")
