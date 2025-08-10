
# María Da Pieve • Body & Macros Tracker

Interfaz web para registrar métricas corporales y comidas, con gráficos interactivos y branding.

## Despliegue en Streamlit Cloud (móvil y escritorio)
1. Creá un repo en GitHub y subí estos archivos.
2. Entrá a https://streamlit.io → **Sign in** → **New app**.
3. Elegí tu repo, rama `main`, archivo `app.py` → **Deploy**.
4. Te dará un link `https://<tu-app>.streamlit.app` que podés abrir desde el celu.

## Estructura
- `app.py` → app principal
- `data/body_metrics.csv` → historial (editable)
- `data/food_db.csv` → base de alimentos por 100 g
- `assets/` → logos
- `.streamlit/config.toml` → tema

## Correr localmente
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notas
- Para persistir datos en la nube, se puede conectar a Google Sheets.
- OCR para leer fotos de báscula/tablas se puede agregar en una siguiente versión.
