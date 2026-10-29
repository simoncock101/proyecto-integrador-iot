
import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------------------------------
# CONFIGURACION
# --------------------------------------------------

st.set_page_config(
    page_title="Pulse EAFIT | Dashboard IoT",
    page_icon="💓",
    layout="wide"
)

st.title("💓 Pulse EAFIT")
st.caption(
    "Dashboard interactivo de indicadores fisiológicos IoT"
)

st.info(
    "Proyecto académico con datos sintéticos. "
    "Las mediciones no permiten establecer diagnósticos médicos."
)

# --------------------------------------------------
# CARGA Y PREPARACION DE DATOS
# --------------------------------------------------

ARCHIVO = "proyecto_integrador_eafit_max30102.csv"


@st.cache_data
def cargar_datos():
    df = pd.read_csv(ARCHIVO)

    df["timestamp"] = pd.to_datetime(
        df["timestamp"], utc=True, errors="coerce"
    )

    df["timestamp"] = df["timestamp"].dt.tz_convert(
        "America/Bogota"
    )

    for columna in [
        "heart_rate_bpm",
        "spo2_percent",
        "signal_quality"
    ]:
        df[columna] = pd.to_numeric(
            df[columna], errors="coerce"
        )

    df = df.dropna(subset=["timestamp"])

    df["fecha"] = df["timestamp"].dt.date
    df["hora"] = df["timestamp"].dt.hour
    df["dia_semana"] = df["timestamp"].dt.day_name()

    dias_espanol = {
        "Monday": "Lunes",
        "Tuesday": "Martes",
        "Wednesday": "Miércoles",
        "Thursday": "Jueves",
        "Friday": "Viernes",
        "Saturday": "Sábado",
        "Sunday": "Domingo"
    }

    df["dia_semana"] = df["dia_semana"].map(dias_espanol)

    return df


try:
    df = cargar_datos()
except Exception as error:
    st.error(f"No fue posible cargar los datos: {error}")
    st.stop()

# --------------------------------------------------
# FILTROS
# --------------------------------------------------

st.sidebar.title("🔎 Filtros")

fechas = df["fecha"].dropna()

if fechas.empty:
    st.error("No hay fechas válidas para analizar.")
    st.stop()

fecha_min = min(fechas)
fecha_max = max(fechas)

rango_fechas = st.sidebar.date_input(
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

# --------------------------------------------------
# APLICAR FILTROS
# --------------------------------------------------

filtrado = df.copy()

if isinstance(rango_fechas, (tuple, list)):
    if len(rango_fechas) == 2:
        inicio, fin = rango_fechas

        filtrado = filtrado[
            filtrado["fecha"].between(inicio, fin)
        ]
    elif len(rango_fechas) == 1:
        filtrado = filtrado[
            filtrado["fecha"] == rango_fechas[0]
        ]

if estudiante != "Todos":
    filtrado = filtrado[
        filtrado["student_id"] == estudiante
    ]

if estado != "Todos":
    filtrado = filtrado[
        filtrado["measurement_status"] == estado
    ]

if filtrado.empty:
    st.warning(
        "No hay mediciones para los filtros seleccionados."
    )
    st.stop()

validas = filtrado[
    filtrado["measurement_status"] == "valid"
]

invalidas = (
    filtrado["measurement_status"] == "invalid"
).sum()

total = len(filtrado)

porcentaje_invalidas = (
    invalidas / total * 100 if total else 0
)

bpm_promedio = validas["heart_rate_bpm"].mean()
spo2_promedio = validas["spo2_percent"].mean()

# --------------------------------------------------
# INDICADORES
# --------------------------------------------------

st.subheader("📊 Indicadores generales")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Mediciones", f"{total:,}")
c2.metric(
    "Estudiantes",
    f"{filtrado['student_id'].nunique():,}"
)
c3.metric(
    "BPM promedio",
    f"{bpm_promedio:.2f}" if pd.notna(bpm_promedio) else "—"
)
c4.metric(
    "SpO₂ promedio",
    f"{spo2_promedio:.2f}%" if pd.notna(spo2_promedio) else "—"
)
c5.metric("Inválidas", f"{porcentaje_invalidas:.2f}%")

st.divider()

# --------------------------------------------------
# GRAFICO 1: MEDICIONES POR FECHA
# --------------------------------------------------

st.subheader("📅 Actividad del tótem")

mediciones_fecha = (
    filtrado.groupby("fecha")
    .size()
    .reset_index(name="mediciones")
)

fig_fecha = px.line(
    mediciones_fecha,
    x="fecha",
    y="mediciones",
    markers=True,
    title="Cantidad de mediciones por día",
    labels={
        "fecha": "Fecha",
        "mediciones": "Número de mediciones"
    },
    template="plotly_dark"
)

fig_fecha.update_layout(
    margin=dict(l=20, r=20, t=60, b=20)
)

st.plotly_chart(fig_fecha, use_container_width=True)

# --------------------------------------------------
# GRAFICOS 2 Y 3: DISTRIBUCIONES
# --------------------------------------------------

col1, col2 = st.columns(2)

with col1:
    st.subheader("❤️ Distribución de BPM")

    bpm_data = validas.dropna(
        subset=["heart_rate_bpm"]
    )

    if not bpm_data.empty:
        fig_bpm = px.histogram(
            bpm_data,
            x="heart_rate_bpm",
            nbins=25,
            title="Distribución de frecuencia cardíaca",
            labels={
                "heart_rate_bpm": "BPM",
                "count": "Mediciones"
            },
            template="plotly_dark"
        )

        st.plotly_chart(
            fig_bpm,
            use_container_width=True
        )
    else:
        st.info("No hay datos válidos de BPM.")

with col2:
    st.subheader("🫁 Distribución de SpO₂")

    spo2_data = validas.dropna(
        subset=["spo2_percent"]
    )

    if not spo2_data.empty:
        fig_spo2 = px.histogram(
            spo2_data,
            x="spo2_percent",
            nbins=25,
            title="Distribución de saturación estimada",
            labels={
                "spo2_percent": "SpO₂ (%)",
                "count": "Mediciones"
            },
            template="plotly_dark"
        )

        st.plotly_chart(
            fig_spo2,
            use_container_width=True
        )
    else:
        st.info("No hay datos válidos de SpO₂.")

# --------------------------------------------------
# GRAFICO 4: USO POR HORA
# --------------------------------------------------

st.subheader("🕒 Horarios de utilización")

mediciones_hora = (
    filtrado.groupby("hora")
    .size()
    .reindex(range(24), fill_value=0)
    .reset_index(name="mediciones")
)

fig_hora = px.bar(
    mediciones_hora,
    x="hora",
    y="mediciones",
    title="Mediciones por hora del día",
    labels={
        "hora": "Hora",
        "mediciones": "Número de mediciones"
    },
    template="plotly_dark"
)

fig_hora.update_xaxes(dtick=1)

st.plotly_chart(fig_hora, use_container_width=True)

# --------------------------------------------------
# GRAFICO 5: ESTADO DE MEDICIONES
# --------------------------------------------------

st.subheader("🛡️ Calidad de los registros")

conteo_estado = (
    filtrado["measurement_status"]
    .value_counts()
    .rename_axis("estado")
    .reset_index(name="cantidad")
)

fig_estado = px.pie(
    conteo_estado,
    names="estado",
    values="cantidad",
    hole=0.45,
    title="Proporción de mediciones por estado",
    template="plotly_dark"
)

st.plotly_chart(fig_estado, use_container_width=True)

# --------------------------------------------------
# GRAFICO 6: MEDICIONES POR DIA DE LA SEMANA
# --------------------------------------------------

st.subheader("📆 Uso por día de la semana")

orden_dias = [
    "Lunes", "Martes", "Miércoles", "Jueves",
    "Viernes", "Sábado", "Domingo"
]

mediciones_dia = (
    filtrado["dia_semana"]
    .value_counts()
    .reindex(orden_dias, fill_value=0)
    .rename_axis("dia")
    .reset_index(name="mediciones")
)

fig_dia = px.bar(
    mediciones_dia,
    x="dia",
    y="mediciones",
    title="Distribución semanal de uso",
    labels={
        "dia": "Día de la semana",
        "mediciones": "Número de mediciones"
    },
    template="plotly_dark"
)

st.plotly_chart(fig_dia, use_container_width=True)

# --------------------------------------------------
# SEGUIMIENTO INDIVIDUAL
# --------------------------------------------------

st.divider()
st.header("👤 Seguimiento individual")

if estudiante == "Todos":
    estudiante_individual = st.selectbox(
        "Selecciona un estudiante para consultar su historial",
        estudiantes,
        key="seguimiento_estudiante"
    )
else:
    estudiante_individual = estudiante
    st.write(f"Estudiante seleccionado: {estudiante}")

historial = df[
    (df["student_id"] == estudiante_individual)
    & (df["measurement_status"] == "valid")
].sort_values("timestamp")

if isinstance(rango_fechas, (tuple, list)):
    if len(rango_fechas) == 2:
        historial = historial[
            historial["fecha"].between(
                rango_fechas[0], rango_fechas[1]
            )
        ]

if not historial.empty:
    primera = historial["timestamp"].min()
    ultima = historial["timestamp"].max()

    h1, h2, h3 = st.columns(3)

    h1.metric("Mediciones válidas", len(historial))
    h2.metric(
        "Primera medición",
        primera.strftime("%d/%m/%Y")
    )
    h3.metric(
        "Última medición",
        ultima.strftime("%d/%m/%Y")
    )

    fig_individual = px.line(
        historial,
        x="timestamp",
        y="heart_rate_bpm",
        markers=True,
        title="Evolución de frecuencia cardíaca",
        labels={
            "timestamp": "Fecha y hora",
            "heart_rate_bpm": "BPM"
        },
        template="plotly_dark"
    )

    st.plotly_chart(
        fig_individual,
        use_container_width=True
    )

    fig_individual_spo2 = px.line(
        historial,
        x="timestamp",
        y="spo2_percent",
        markers=True,
        title="Evolución de SpO₂",
        labels={
            "timestamp": "Fecha y hora",
            "spo2_percent": "SpO₂ (%)"
        },
        template="plotly_dark"
    )

    st.plotly_chart(
        fig_individual_spo2,
        use_container_width=True
    )
else:
    st.info(
        "No hay mediciones válidas para este estudiante "
        "en el período seleccionado."
    )

# --------------------------------------------------
# HALLAZGOS AUTOMATICOS
# --------------------------------------------------

st.divider()
st.header("💡 Hallazgos del análisis")

hallazgo_1 = (
    filtrado.groupby("hora")
    .size()
)

if not hallazgo_1.empty:
    hora_pico = int(hallazgo_1.idxmax())
    cantidad_pico = int(hallazgo_1.max())

    st.markdown(
        f"**1. Hora de mayor uso:** las {hora_pico:02d}:00, "
        f"con {cantidad_pico} mediciones en el período filtrado."
    )

conteo_dias = filtrado["dia_semana"].value_counts()

if not conteo_dias.empty:
    dia_pico = conteo_dias.idxmax()
    cantidad_dia = int(conteo_dias.max())

    st.markdown(
        f"**2. Día con más actividad:** {dia_pico}, "
        f"con {cantidad_dia} mediciones."
    )

st.markdown(
    f"**3. Calidad de los registros:** "
    f"{porcentaje_invalidas:.2f}% de las mediciones "
    f"del conjunto filtrado están marcadas como inválidas."
)

st.caption(
    "Los hallazgos son descriptivos y dependen de los filtros. "
    "No constituyen evaluaciones ni diagnósticos médicos."
)

# --------------------------------------------------
# TABLA DE DATOS
# --------------------------------------------------

with st.expander("📋 Consultar tabla de registros"):
    st.dataframe(
        filtrado,
        use_container_width=True,
        hide_index=True
    )

st.caption(
    "Pulse EAFIT · Proyecto Integrador de Computación Física e IoT"
)

