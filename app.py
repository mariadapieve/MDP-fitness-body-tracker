import os
import io
import base64
import pandas as pd
import streamlit as st
import plotly.express as px
from PIL import Image

# ===================== CONFIG & BRANDING =====================
st.set_page_config(page_title="MDP Fitness Body Tracker", page_icon="💪", layout="wide")

PRIMARY = "#0D0D0D"     # negro
ACCENT  = "#D0B49F"     # beige rosado (ajustalo si querés)
TEXT    = "#FFFFFF"

# CSS (logo chico + tipografía general + colores)
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700&family=Inter:wght@400;600&display=swap');
    html, body, [class*="stApp"] {{
        background: {PRIMARY} !important;
        color: {TEXT} !important;
        font-family: 'Inter', sans-serif;
    }}
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
        font-family: 'Playfair Display', serif;
        letter-spacing: .2px;
    }}
    /* achicar img de cabecera */
    .mdp-logo img {{ max-height: 120px; object-fit: contain; margin: 0 auto; display:block; }}
    .block-container {{ padding-top: 1.2rem; }}
    .stTabs [role="tablist"] > div[role="tab"] {{
        color: {TEXT}; border-color: {ACCENT};
    }}
    .stTabs [role="tab"][aria-selected="true"] {{
        background: rgba(208,180,159,.15); border-bottom: 2px solid {ACCENT};
    }}
    </style>
    """,
    unsafe_allow_html=True
)

def show_logo():
    for p in ["assets/logo_main.png", "logo_main.png"]:
        if os.path.exists(p):
            st.markdown('<div class="mdp-logo">', unsafe_allow_html=True)
            st.image(p, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            return
show_logo()

st.title("MDP Fitness Body Tracker")

# ===================== ARCHIVOS & COLUMNAS =====================
CSV_CANDIDATES = ["data/body_metrics.csv", "body_metrics.csv"]
MEALS_CSV      = "meals_log.csv"  # se guarda en el contenedor (efímero en la nube, sirve para exportar)

COLS = ["Fecha","Peso (kg)","% Grasa","Grasa (kg)","Músculo (kg)","IMC","% Agua","Grasa visceral","TMB (kcal)"]

def find_metrics_csv():
    for p in CSV_CANDIDATES:
        if os.path.exists(p): return p
    os.makedirs("data", exist_ok=True)
    return "body_metrics.csv"

METRICS_CSV = find_metrics_csv()

def normalize_columns(df):
    rename_map = {
        "date":"Fecha","weight_kg":"Peso (kg)","fat_percent":"% Grasa",
        "fat_kg":"Grasa (kg)","muscle_kg":"Músculo (kg)","bmi":"IMC",
        "water_percent":"% Agua","visceral_fat":"Grasa visceral","tmb_kcal":"TMB (kcal)"
    }
    df.rename(columns={k:v for k,v in rename_map.items() if k in df.columns}, inplace=True)
    for c in COLS:
        if c not in df.columns: df[c] = pd.NA
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    return df[COLS].sort_values("Fecha")

@st.cache_data
def load_metrics(path):
    if os.path.exists(path) and os.path.getsize(path)>0:
        try:
            raw = pd.read_csv(path)
            raw.columns = [c.strip() for c in raw.columns]
            return normalize_columns(raw)
        except Exception as e:
            st.error(f"No pude leer {path}: {e}")
    return pd.DataFrame(columns=COLS)

def save_metrics(df, path):
    df.to_csv(path, index=False)

metrics = load_metrics(METRICS_CSV)

# DB de alimentos
FOOD_DB_PATHS = ["data/food_db.csv","food_db.csv"]
def load_fooddb():
    for p in FOOD_DB_PATHS:
        if os.path.exists(p):
            df = pd.read_csv(p)
            df.columns = [c.strip().lower() for c in df.columns]
            # se esperan columnas: food, protein, carbs, fat (por 100 g)
            return df
    # fallback básico
    return pd.DataFrame({
        "food":["pollo pechuga","salmón","huevo","batata","arroz blanco","frutillas","yogur natural"],
        "protein":[31,20,13,1.6,2.7,0.7,4],
        "carbs":[0,0,1.1,20,28,7.7,6],
        "fat":[3.6,13,10,0.1,0.3,0.3,3]
    })
fooddb = load_fooddb()

# ===================== TABS =====================
tab_hist, tab_add, tab_meals = st.tabs(["📈 Historial", "➕ Agregar medición", "🍽️ Comidas & Macros"])

# --------------------- HISTORIAL ---------------------
with tab_hist:
    st.subheader("Tabla de historial")
    if metrics.empty:
        st.info("No hay datos aún. Cargá un CSV o agregá tu primera medición en la pestaña de al lado.")
    st.dataframe(metrics, use_container_width=True)

    # Importar CSV histórico
    st.markdown("**Cargar/actualizar historial desde CSV** (mismas columnas que la tabla):")
    up = st.file_uploader("Subí tu body_metrics.csv", type=["csv"], key="metrics_csv")
    if up:
        try:
            df_new = pd.read_csv(up)
            df_new = normalize_columns(df_new)
            save_metrics(df_new, METRICS_CSV)
            st.success("Historial actualizado. Refrescá la página (Rerun).")
        except Exception as e:
            st.error(f"No pude procesar el CSV: {e}")

    if not metrics.empty and metrics["Fecha"].notna().any():
        st.subheader("Peso, Grasa (kg) y Músculo (kg)")
        y1 = [c for c in ["Peso (kg)","Grasa (kg)","Músculo (kg)"] if c in metrics.columns]
        fig1 = px.line(metrics, x="Fecha", y=y1, markers=True)
        fig1.update_layout(hovermode="x unified")
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader("Todas las métricas (sin TMB)")
        y2 = [c for c in ["Peso (kg)","% Grasa","Grasa (kg)","Músculo (kg)","IMC","% Agua","Grasa visceral"] if c in metrics.columns]
        if y2:
            fig2 = px.line(metrics, x="Fecha", y=y2, markers=True)
            fig2.update_layout(hovermode="x unified")
            st.plotly_chart(fig2, use_container_width=True)

# --------------------- AGREGAR MEDICIÓN ---------------------
with tab_add:
    st.subheader("Nueva medición")
    c1,c2,c3 = st.columns(3)
    with c1:
        fecha = st.date_input("Fecha")
        peso  = st.number_input("Peso (kg)", min_value=0.0, step=0.1)
        grasa_pct = st.number_input("% Grasa", min_value=0.0, step=0.1)
    with c2:
        grasa_kg = st.number_input("Grasa (kg)", min_value=0.0, step=0.1, help="Si lo dejás en 0, lo calculo con Peso × %Grasa.")
        musculo  = st.number_input("Músculo (kg)", min_value=0.0, step=0.1)
        imc      = st.number_input("IMC", min_value=0.0, step=0.1)
    with c3:
        agua     = st.number_input("% Agua", min_value=0.0, step=0.1)
        visceral = st.number_input("Grasa visceral", min_value=0.0, step=0.1)
        tmb      = st.number_input("TMB (kcal)", min_value=0.0, step=1.0)

    grasa_calc = None
    if (not grasa_kg) and peso and grasa_pct:
        grasa_calc = round(peso*(grasa_pct/100),2)
        st.caption(f"↳ Sugerencia Grasa (kg): **{grasa_calc}**")

    if st.button("💾 Guardar medición"):
        new = pd.DataFrame([{
            "Fecha": pd.to_datetime(fecha),
            "Peso (kg)": peso or pd.NA,
            "% Grasa": grasa_pct or pd.NA,
            "Grasa (kg)": (grasa_calc if grasa_calc is not None else (grasa_kg or pd.NA)),
            "Músculo (kg)": musculo or pd.NA,
            "IMC": imc or pd.NA,
            "% Agua": agua or pd.NA,
            "Grasa visceral": visceral or pd.NA,
            "TMB (kcal)": tmb or pd.NA
        }])
        out = pd.concat([metrics, new], ignore_index=True).sort_values("Fecha")
        save_metrics(out, METRICS_CSV)
        st.success("Guardado. Volvé a Historial y actualizá para ver el gráfico.")
        st.cache_data.clear()

# --------------------- COMIDAS & MACROS ---------------------
with tab_meals:
    st.subheader("Registro de comidas + foto (opcional) y cálculo de macros")

    # Targets (A/B) — podés ajustar
    plan = st.radio("Plan del día", ["Escenario A (80P/80C/105G)", "Escenario B (95P/80C/70G)"], horizontal=True)
    if plan.startswith("Escenario A"):
        target = {"protein":80.0, "carbs":80.0, "fat":105.0, "kcal": 80*4+80*4+105*9}
    else:
        target = {"protein":95.0, "carbs":80.0, "fat":70.0, "kcal": 95*4+80*4+70*9}

    st.write(f"**Objetivo diario:** {target['protein']} g proteína | {target['carbs']} g carbs | {target['fat']} g grasas (~{int(target['kcal'])} kcal)")

    # Foto opcional (no se guarda en disco; solo vista previa)
    up_photo = st.file_uploader("Foto de tu comida (opcional)", type=["jpg","jpeg","png"])
    if up_photo:
        img = Image.open(up_photo)
        st.image(img, caption="Foto cargada", use_container_width=True)

    st.markdown("**Seleccioná hasta 8 alimentos y cantidad (g):**")
    rows = []
    for i in range(1,9):
        c1,c2,c3 = st.columns([2,1,1])
        with c1:
            food = st.selectbox(f"Alimento #{i}", [""] + fooddb["food"].tolist(), key=f"food{i}")
        with c2:
            grams = st.number_input(f"Gramos #{i}", min_value=0, step=10, key=f"g{i}")
        with c3:
            st.write("")  # spacer
        if food and grams>0:
            row = fooddb[fooddb["food"]==food].iloc[0]
            factor = grams/100.0
            rows.append({
                "food": food,
                "grams": grams,
                "protein": row["protein"]*factor,
                "carbs": row["carbs"]*factor,
                "fat": row["fat"]*factor,
                "kcal": (row["protein"]*4 + row["carbs"]*4 + row["fat"]*9)*factor
            })

    if rows:
        macro_df = pd.DataFrame(rows)
        st.dataframe(macro_df[["food","grams","protein","carbs","fat","kcal"]], use_container_width=True)
        totals = macro_df[["protein","carbs","fat","kcal"]].sum()

        def colorize(v, tgt):
            if v > tgt: return "🔴 por encima"
            if v < tgt*0.9: return "🟡 por debajo"
            return "🟢 OK"

        st.markdown("**Totales del día:**")
        st.write(f"- {totals['protein']:.1f} g proteína → {colorize(totals['protein'], target['protein'])}")
        st.write(f"- {totals['carbs']:.1f} g carbs → {colorize(totals['carbs'], target['carbs'])}")
        st.write(f"- {totals['fat']:.1f} g grasas → {colorize(totals['fat'], target['fat'])}")
        st.write(f"- {totals['kcal']:.0f} kcal (estimadas)")

        # Exportar CSV del día (descarga)
        csv_bytes = macro_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Descargar registro (CSV)", data=csv_bytes, file_name="comida_del_dia.csv", mime="text/csv")
    else:
        st.info("Elegí al menos un alimento y cantidad para calcular macros.")
