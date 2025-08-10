
import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

st.set_page_config(page_title="Maria Da Pieve • Body & Macros Tracker", page_icon="assets/logo_icon.png", layout="wide")

# Branding header
col1, col2 = st.columns([1,4])
with col1:
    st.image("assets/logo_main.png", use_column_width=True)
with col2:
    st.title("Body & Macros Tracker")
    st.caption("by María Da Pieve")

st.sidebar.header("🎯 Objetivo diario (Escenario)")
scenario = st.sidebar.radio("Elegí tu plan", ["Escenario A (80P/80C/105G ~1589 kcal)", "Escenario B (95P/80C/70G ~1332 kcal)"])
if scenario.startswith("Escenario A"):
    target = {"protein": 80, "carbs": 80, "fat": 105, "kcal": 1589}
else:
    target = {"protein": 95, "carbs": 80, "fat": 70, "kcal": 1332}
st.sidebar.write(target)

tab_dash, tab_add, tab_meal = st.tabs(["📊 Historial", "➕ Nueva medición", "🍽️ Comidas & Macros"])

# ===== TAB 1: DASHBOARD =====
with tab_dash:
    st.subheader("Histórico completo (interactivo)")
    df = pd.read_csv("data/body_metrics.csv", parse_dates=["date"])
    df = df.sort_values("date")

    cols_all = ["weight_kg","fat_kg","muscle_kg","fat_percent","bmi","visceral_fat","water_percent"]
    fig_all = px.line(df, x="date", y=cols_all, markers=True, title="Todas las métricas (sin TMB)")
    fig_all.update_layout(hovermode="x unified")
    st.plotly_chart(fig_all, use_container_width=True)

    st.subheader("Composición corporal")
    fig_focus = px.line(df, x="date", y=["weight_kg","fat_kg","muscle_kg"], markers=True, title="Peso, grasa (kg), músculo (kg)")
    fig_focus.update_layout(hovermode="x unified")
    st.plotly_chart(fig_focus, use_container_width=True)

# ===== TAB 2: ADD MEASUREMENT =====
with tab_add:
    st.subheader("Agregar medición")
    c1, c2, c3 = st.columns(3)
    with c1:
        date = st.date_input("Fecha")
        weight = st.number_input("Peso (kg)", min_value=0.0, step=0.1)
        fat_kg = st.number_input("Masa grasa (kg)", min_value=0.0, step=0.1)
    with c2:
        muscle_kg = st.number_input("Músculo (kg)", min_value=0.0, step=0.1)
        fat_pct = st.number_input("% Grasa", min_value=0.0, step=0.1)
        bmi = st.number_input("IMC", min_value=0.0, step=0.1)
    with c3:
        visceral = st.number_input("Grasa visceral", min_value=0.0, step=0.1)
        water = st.number_input("% Agua", min_value=0.0, step=0.1)
        tmb = st.number_input("TMB (kcal/día)", min_value=0.0, step=1.0)

    if st.button("💾 Guardar medición"):
        df_new = pd.read_csv("data/body_metrics.csv", parse_dates=["date"])
        new = pd.DataFrame([{
            "date": pd.to_datetime(date),
            "weight_kg": weight,
            "fat_kg": fat_kg,
            "muscle_kg": muscle_kg,
            "fat_percent": fat_pct,
            "bmi": bmi,
            "visceral_fat": visceral,
            "water_percent": water,
            "tmb_kcal": tmb
        }])
        df_out = pd.concat([df_new, new], ignore_index=True).sort_values("date")
        df_out.to_csv("data/body_metrics.csv", index=False)
        st.success("✅ Medición guardada")

# ===== TAB 3: MEAL TRACKER =====
with tab_meal:
    st.subheader("Registro de comidas (con foto)")
    st.caption("Seleccioná alimentos y gramos; se calculan los macros y se compara vs tu objetivo diario.")
    food_db = pd.read_csv("data/food_db.csv")
    st.write("Base de alimentos (por 100 g)")
    st.dataframe(food_db)

    items = []
    for i in range(1,6):
        cols = st.columns([2,1,1])
        with cols[0]:
            food = st.selectbox(f"Alimento #{i}", ["(ninguno)"] + food_db["food"].tolist(), key=f"f{i}")
        with cols[1]:
            grams = st.number_input(f"Gramos #{i}", min_value=0, step=10, key=f"g{i}")
        with cols[2]:
            pass
        if food != "(ninguno)" and grams > 0:
            row = food_db[food_db["food"] == food].iloc[0]
            factor = grams/100.0
            items.append({
                "food": food,
                "grams": grams,
                "protein": row["protein_g"]*factor,
                "carbs": row["carbs_g"]*factor,
                "fat": row["fat_g"]*factor,
                "kcal": row["kcal"]*factor
            })
    if st.button("🍽️ Calcular macros"):
        if not items:
            st.warning("Agregá al menos un alimento.")
        else:
            meal = pd.DataFrame(items)
            st.write("Detalle de la comida")
            st.dataframe(meal)

            totals = meal[["protein","carbs","fat","kcal"]].sum()
            st.write(f"**Totales:** {totals['protein']:.1f} g proteína | {totals['carbs']:.1f} g carbs | {totals['fat']:.1f} g grasas | {totals['kcal']:.0f} kcal")

            # Traffic light vs target
            def colorize(value, goal):
                ratio = value/goal if goal>0 else 0
                if ratio <= 0.9: return "🟡 por debajo"
                if ratio <= 1.05: return "🟢 OK"
                return "🔴 pasado"

            st.write("**Comparación con objetivo diario:**")
            st.write(f"Proteína: {colorize(totals['protein'], target['protein'])}")
            st.write(f"Carbohidratos: {colorize(totals['carbs'], target['carbs'])}")
            st.write(f"Grasas: {colorize(totals['fat'], target['fat'])}")
            st.write(f"Calorías: {colorize(totals['kcal'], target['kcal'])}")
