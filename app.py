
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Pulse EAFIT | Dashboard IoT",
    page_icon="💓",
    layout="wide"
)

st.title("💓 Pulse EAFIT")
st.caption(
    "Dashboard interactivo de monitoreo fisiológico IoT"
)

st.info(
    "Proyecto académico con datos sintéticos. "
    "Las mediciones no representan diagnósticos médicos."
)

@st.cache_data
def cargar_datos():
    df = pd.read_csv("proyecto_integrador_eafit_max30102.csv")

    df["timestamp"] = pd.to_datetime(
        df["timestamp"], utc=True, errors="coerce"
    )
    df["timestamp"] = df["timestamp"].dt.tz_convert(
        "America/Bogota"
    )

    df["heart_rate_bpm"] = pd.to_numeric(
        df["heart_rate_bpm"], errors="coerce"
    )
    df["spo2_percent"] = pd.to_numeric(
        df["spo2_percent"], errors="coerce"
    )

    return df

try:
    df = cargar_datos()

    st.sidebar.header("Filtros")

    fechas = df["timestamp"].dropna().dt.date
    fecha_min = fechas.min()
    fecha_max = fechas.max()

    rango = st.sidebar.date_input(
        "Rango de fechas",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max
    )

    estudiantes = sorted(
        df["student_id"].dropna().unique().tolist()
    )

    estudiante = st.sidebar.selectbox(
        "Estudiante",
        ["Todos"] + estudiantes
    )

    estado = st.sidebar.selectbox(
        "Estado de medición",
        ["Todos", "valid", "invalid"]
    )

    filtrado = df.copy()

    if len(rango) == 2:
        filtrado = filtrado[
            filtrado["timestamp"].dt.date.between(
                rango[0], rango[1]
            )
        ]

    if estudiante != "Todos":
        filtrado = filtrado[
            filtrado["student_id"] == estudiante
        ]

    if estado != "Todos":
        filtrado = filtrado[
            filtrado["measurement_status"] == estado
        ]

    validas = filtrado[
        filtrado["measurement_status"] == "valid"
    ]

    total = len(filtrado)
    estudiantes_total = filtrado["student_id"].nunique()
    bpm = validas["heart_rate_bpm"].mean()
    spo2 = validas["spo2_percent"].mean()

    invalidas = (
        (filtrado["measurement_status"] == "invalid").sum()
    )
    porcentaje_invalidas = (
        invalidas / total * 100 if total else 0
    )

    st.subheader("Indicadores generales")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Mediciones", f"{total:,}")
    c2.metric("Estudiantes", f"{estudiantes_total:,}")
    c3.metric("BPM promedio", f"{bpm:.2f}" if pd.notna(bpm) else "—")
    c4.metric("SpO₂ promedio", f"{spo2:.2f}%" if pd.notna(spo2) else "—")
    c5.metric("Inválidas", f"{porcentaje_invalidas:.2f}%")

    st.subheader("Datos registrados")
    st.dataframe(
        filtrado,
        use_container_width=True,
        hide_index=True
    )

except FileNotFoundError:
    st.error(
        "No se encontró el archivo CSV. "
        "Comprueba que esté en la raíz del repositorio "
        "y que su nombre coincida exactamente."
    )
except Exception as e:
    st.error(f"No se pudo cargar el dashboard: {e}")
