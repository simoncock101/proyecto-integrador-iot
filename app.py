
import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================================
# 1. CONFIGURACION Y ESTILO
# ============================================================

st.set_page_config(
    page_title="Pulse EAFIT | Dashboard IoT",
    page_icon="💓",
    layout="wide"
)

AZUL = "#5267F5"
AZUL_OSCURO = "#17365D"
TEXTO = "#334155"
TEXTO_SECUNDARIO = "#475569"
CUADRICULA = "#E8EDF4"
FONDO = "#FFFFFF"
TURQUESA = "#087F8C"
ROJO = "#E85D5D"


st.markdown("""
<style>
    .stApp {
        background-color: #F7F9FC;
        color: #172B4D;
    }

    [data-testid="stHeader"] {
        background-color: rgba(247, 249, 252, 0.95);
    }

    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E3EAF3;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #17365D !important;
    }

    h1, h2, h3 {
        color: #17365D !important;
        letter-spacing: -0.4px;
    }

    p, label, .stMarkdown {
        color: #334155;
    }

    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E3EAF3;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(23, 54, 93, 0.04);
    }

    [data-testid="stMetricLabel"] {
        color: #64748B !important;
    }

    [data-testid="stMetricValue"] {
        color: #17365D !important;
        font-weight: 700;
    }

    [data-testid="stAlert"] {
        border-radius: 10px;
    }

    div[data-testid="stPlotlyChart"] {
        background-color: #FFFFFF;
        border: 1px solid #E3EAF3;
        border-radius: 12px;
        padding: 8px;
        margin-bottom: 12px;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #E3EAF3;
        border-radius: 10px;
        overflow: hidden;
    }

    div.stButton > button,
    div.stDownloadButton > button {
        background-color: #087F8C;
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }

    div.stButton > button:hover,
    div.stDownloadButton > button:hover {
        background-color: #066874;
        color: #FFFFFF;
    }

    hr {
        border-color: #E2E8F0;
    }

    #MainMenu, footer {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)


st.title("💓 Pulse EAFIT")
st.caption("Dashboard interactivo de indicadores fisiológicos IoT")

st.info(
    "Proyecto académico con datos sintéticos. "
    "Los resultados son descriptivos y no constituyen "
    "un diagnóstico médico."
)


# ============================================================
# 2. FUNCIONES AUXILIARES
# ============================================================

def aplicar_estilo(fig, titulo=None):
    """Aplica un estilo claro y legible a los gráficos."""

    titulo_final = titulo

    if titulo_final is None:
        titulo_final = fig.layout.title.text

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=FONDO,
        plot_bgcolor=FONDO,
        font=dict(
            family="Arial, sans-serif",
            size=13,
            color=TEXTO
        ),
        title=dict(
            text=titulo_final,
            x=0.02,
            xanchor="left",
            font=dict(size=18, color=AZUL_OSCURO)
        ),
        margin=dict(l=45, r=25, t=70, b=45),
        legend=dict(
            font=dict(size=12, color=TEXTO),
            bgcolor="rgba(255,255,255,0.9)"
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            font=dict(color=TEXTO, size=13),
            bordercolor="#D7E0EC"
        )
    )

    fig.update_xaxes(
        title_font=dict(size=13, color=TEXTO),
        tickfont=dict(size=12, color=TEXTO_SECUNDARIO),
        gridcolor=CUADRICULA,
        linecolor="#CBD5E1",
        zerolinecolor=CUADRICULA
    )

    fig.update_yaxes(
        title_font=dict(size=13, color=TEXTO),
        tickfont=dict(size=12, color=TEXTO_SECUNDARIO),
        gridcolor=CUADRICULA,
        linecolor="#CBD5E1",
        zerolinecolor=CUADRICULA
    )

    return fig


def detectar_atipicos(datos, columna):
    """Detecta posibles valores atípicos usando el método IQR."""

    valores = datos[columna].dropna()

    if len(valores) < 4:
        return valores.iloc[0:0]

    q1 = valores.quantile(0.25)
    q3 = valores.quantile(0.75)
    iqr = q3 - q1

    limite_inferior = q1 - 1.5 * iqr
    limite_superior = q3 + 1.5 * iqr

    return valores[
        (valores < limite_inferior)
        | (valores > limite_superior)
    ]


def resumir_rango(datos, columna, minimo, maximo):
    """Resume mediciones dentro y fuera de un rango de referencia."""

    valores = datos[columna].dropna()
    cantidad = len(valores)

    if cantidad == 0:
        return {
            "total": 0,
            "dentro": 0,
            "debajo": 0,
            "encima": 0,
            "porcentaje_dentro": 0.0,
            "porcentaje_debajo": 0.0,
            "porcentaje_encima": 0.0
        }

    dentro = int(
        ((valores >= minimo) & (valores <= maximo)).sum()
    )

    debajo = int((valores < minimo).sum())
    encima = int((valores > maximo).sum())

    return {
        "total": cantidad,
        "dentro": dentro,
        "debajo": debajo,
        "encima": encima,
        "porcentaje_dentro": dentro / cantidad * 100,
        "porcentaje_debajo": debajo / cantidad * 100,
        "porcentaje_encima": encima / cantidad * 100
    }


# ============================================================
# 3. CARGA Y PREPARACION DE DATOS
# ============================================================

ARCHIVO = "proyecto_integrador_eafit_max30102.csv"


@st.cache_data
def cargar_datos():
    df = pd.read_csv(ARCHIVO)

    columnas_requeridas = [
        "timestamp",
        "student_id",
        "nfc_id",
        "device_id",
        "heart_rate_bpm",
        "spo2_percent",
        "signal_quality",
        "measurement_status"
    ]

    faltantes = [
        columna for columna in columnas_requeridas
        if columna not in df.columns
    ]

    if faltantes:
        raise ValueError(
            "Faltan columnas en el CSV: "
            + ", ".join(faltantes)
        )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        utc=True,
        errors="coerce"
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
            df[columna],
            errors="coerce"
        )

    df = df.dropna(subset=["timestamp"]).copy()

    df["fecha"] = df["timestamp"].dt.date
    df["hora"] = df["timestamp"].dt.hour

    traduccion_dias = {
        "Monday": "Lunes",
        "Tuesday": "Martes",
        "Wednesday": "Miércoles",
        "Thursday": "Jueves",
        "Friday": "Viernes",
        "Saturday": "Sábado",
        "Sunday": "Domingo"
    }

    df["dia_semana"] = (
        df["timestamp"].dt.day_name().map(traduccion_dias)
    )

    return df


try:
    df = cargar_datos()

except FileNotFoundError:
    st.error(
        "No se encontró el archivo "
        "proyecto_integrador_eafit_max30102.csv. "
        "Comprueba que esté en la raíz del repositorio."
    )
    st.stop()

except Exception as error:
    st.error(f"Error al cargar los datos: {error}")
    st.stop()


if df.empty:
    st.error("No hay registros con fechas válidas.")
    st.stop()


# ============================================================
# 4. FILTROS
# ============================================================

st.sidebar.title("🔎 Filtros")
st.sidebar.caption("Personaliza los datos que deseas explorar.")

fecha_min = min(df["fecha"])
fecha_max = max(df["fecha"])

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


# ============================================================
# 5. APLICAR FILTROS
# ============================================================

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
        "No hay mediciones con los filtros seleccionados. "
        "Prueba con otro rango o estudiante."
    )
    st.stop()


validas = filtrado[
    filtrado["measurement_status"] == "valid"
].copy()

registros_invalidos = filtrado[
    filtrado["measurement_status"] == "invalid"
].copy()

total = len(filtrado)
cantidad_invalidas = len(registros_invalidos)

porcentaje_invalidas = (
    cantidad_invalidas / total * 100 if total else 0
)

bpm_promedio = validas["heart_rate_bpm"].mean()
spo2_promedio = validas["spo2_percent"].mean()


# ============================================================
# 6. INDICADORES GENERALES
# ============================================================

st.subheader("📊 Indicadores generales")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Mediciones", f"{total:,}")

c2.metric(
    "Estudiantes",
    f"{filtrado['student_id'].nunique():,}"
)

c3.metric(
    "BPM promedio",
    f"{bpm_promedio:.2f}"
    if pd.notna(bpm_promedio) else "—"
)

c4.metric(
    "SpO₂ promedio",
    f"{spo2_promedio:.2f}%"
    if pd.notna(spo2_promedio) else "—"
)

c5.metric("Inválidas", f"{porcentaje_invalidas:.2f}%")


# ============================================================
# 7. RESUMEN VISUAL CON ICONOS
# ============================================================

st.divider()

st.header("💓 ¿Cómo van los resultados?")
st.caption(
    "Una forma sencilla de entender las mediciones "
    "sin tener que interpretar las gráficas."
)

# Rangos de referencia orientativos.
# BPM: referencia habitual en adultos en reposo.
# SpO2: referencia habitual para adultos a nivel del mar.
BPM_MIN = 60
BPM_MAX = 100
SPO2_MIN = 95
SPO2_MAX = 100

resumen_bpm = resumir_rango(
    validas,
    "heart_rate_bpm",
    BPM_MIN,
    BPM_MAX
)

resumen_spo2 = resumir_rango(
    validas,
    "spo2_percent",
    SPO2_MIN,
    SPO2_MAX
)

col_corazon, col_persona, col_oxigeno = st.columns(
    [1, 1, 1]
)

with col_corazon:
    st.markdown(
        """
        <div style="
            text-align:center;
            padding:18px 10px;
            background:#FFFFFF;
            border:1px solid #E3EAF3;
            border-radius:16px;
        ">
            <div style="font-size:44px;">❤️</div>
            <div style="
                font-size:19px;
                color:#17365D;
                font-weight:600;
            ">Corazón</div>
            <div style="
                font-size:12px;
                color:#64748B;
            ">Frecuencia cardíaca</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if resumen_bpm["total"] > 0:
        st.metric(
            "Mediciones dentro del rango",
            f'{resumen_bpm["porcentaje_dentro"]:.1f}%'
        )

        st.progress(
            resumen_bpm["porcentaje_dentro"] / 100
        )

        st.caption(
            f'{resumen_bpm["dentro"]:,} de '
            f'{resumen_bpm["total"]:,} mediciones'
        )

        st.caption(
            f'Por debajo: {resumen_bpm["porcentaje_debajo"]:.1f}% '
            f' · Por encima: {resumen_bpm["porcentaje_encima"]:.1f}%'
        )
    else:
        st.info("Sin datos válidos de BPM.")

with col_persona:
    st.markdown(
        """
        <div style="
            text-align:center;
            padding:10px 8px 18px 8px;
            background:#FFFFFF;
            border:1px solid #E3EAF3;
            border-radius:16px;
        ">
            <div style="font-size:82px; line-height:1.3;">🧍</div>
            <div style="
                font-size:19px;
                color:#17365D;
                font-weight:600;
            ">Pulse EAFIT</div>
            <div style="
                font-size:12px;
                color:#64748B;
                margin-top:5px;
            ">Resumen de las mediciones</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style="
            text-align:center;
            margin-top:10px;
            padding:12px;
            background:#EAF3FF;
            border-radius:12px;
            color:#17365D;
            font-size:13px;
        ">
            Los porcentajes se actualizan con los filtros.
        </div>
        """,
        unsafe_allow_html=True
    )

with col_oxigeno:
    st.markdown(
        """
        <div style="
            text-align:center;
            padding:18px 10px;
            background:#FFFFFF;
            border:1px solid #E3EAF3;
            border-radius:16px;
        ">
            <div style="font-size:44px;">🫁</div>
            <div style="
                font-size:19px;
                color:#17365D;
                font-weight:600;
            ">Oxígeno</div>
            <div style="
                font-size:12px;
                color:#64748B;
            ">Saturación de oxígeno</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if resumen_spo2["total"] > 0:
        st.metric(
            "Mediciones dentro del rango",
            f'{resumen_spo2["porcentaje_dentro"]:.1f}%'
        )

        st.progress(
            resumen_spo2["porcentaje_dentro"] / 100
        )

        st.caption(
            f'{resumen_spo2["dentro"]:,} de '
            f'{resumen_spo2["total"]:,} mediciones'
        )

        st.caption(
            f'Por debajo: {resumen_spo2["porcentaje_debajo"]:.1f}% '
            f' · Por encima: {resumen_spo2["porcentaje_encima"]:.1f}%'
        )
    else:
        st.info("Sin datos válidos de SpO₂.")

st.caption(
    "Los rangos son orientativos: 60–100 BPM en adultos en reposo "
    "y 95–100% de SpO₂ en condiciones habituales a nivel del mar. "
    "Estar dentro de un rango no demuestra que alguien esté sano. "
    "Los datos son sintéticos y no representan diagnósticos médicos."
)


# ============================================================
# 8. MEDICIONES POR FECHA
# ============================================================

st.divider()
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
    color_discrete_sequence=[AZUL]
)

fig_fecha.update_traces(
    line=dict(width=3),
    marker=dict(size=7)
)

fig_fecha = aplicar_estilo(fig_fecha)
st.plotly_chart(fig_fecha, use_container_width=True)


# ============================================================
# 9. DISTRIBUCION DE BPM Y SPO2
# ============================================================

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
                "count": "Número de mediciones"
            },
            color_discrete_sequence=[AZUL]
        )

        fig_bpm.update_traces(
            marker_line_color="#FFFFFF",
            marker_line_width=1
        )

        fig_bpm = aplicar_estilo(fig_bpm)
        st.plotly_chart(fig_bpm, use_container_width=True)
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
                "count": "Número de mediciones"
            },
            color_discrete_sequence=[TURQUESA]
        )

        fig_spo2.update_traces(
            marker_line_color="#FFFFFF",
            marker_line_width=1
        )

        fig_spo2 = aplicar_estilo(fig_spo2)
        st.plotly_chart(fig_spo2, use_container_width=True)
    else:
        st.info("No hay datos válidos de SpO₂.")


# ============================================================
# 10. USO POR HORA
# ============================================================

st.subheader("🕒 Horarios de utilización")

mediciones_hora = (
    filtrado.groupby("hora")
    .size()
    .reindex(range(24), fill_value=0)
    .rename_axis("hora")
    .reset_index(name="mediciones")
)

fig_hora = px.bar(
    mediciones_hora,
    x="hora",
    y="mediciones",
    title="Mediciones por hora del día",
    labels={
        "hora": "Hora del día",
        "mediciones": "Número de mediciones"
    },
    color_discrete_sequence=[AZUL]
)

fig_hora.update_xaxes(
    tickmode="linear",
    dtick=1
)

fig_hora = aplicar_estilo(fig_hora)
st.plotly_chart(fig_hora, use_container_width=True)


# ============================================================
# 11. ESTADO DE LAS MEDICIONES
# ============================================================

st.subheader("🛡️ Estado de las mediciones")

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
    hole=0.48,
    title="Proporción de mediciones por estado",
    color="estado",
    color_discrete_map={
        "valid": AZUL,
        "invalid": ROJO
    }
)

fig_estado = aplicar_estilo(fig_estado)

fig_estado.update_traces(
    textposition="inside",
    textinfo="percent",
    textfont=dict(
        color="#FFFFFF",
        size=14,
        family="Arial, sans-serif"
    ),
    marker=dict(
        line=dict(color="#FFFFFF", width=3)
    ),
    hovertemplate=(
        "<b>Estado:</b> %{label}<br>"
        "<b>Mediciones:</b> %{value:,}<br>"
        "<b>Porcentaje:</b> %{percent:.2%}"
        "<extra></extra>"
    )
)

st.plotly_chart(fig_estado, use_container_width=True)


# ============================================================
# 12. USO POR DIA DE LA SEMANA
# ============================================================

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
    color_discrete_sequence=[TURQUESA]
)

fig_dia.update_traces(
    marker_line_color="#FFFFFF",
    marker_line_width=1
)

fig_dia = aplicar_estilo(fig_dia)
st.plotly_chart(fig_dia, use_container_width=True)


# ============================================================
# 13. SEGUIMIENTO INDIVIDUAL
# ============================================================

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
                rango_fechas[0],
                rango_fechas[1]
            )
        ]
    elif len(rango_fechas) == 1:
        historial = historial[
            historial["fecha"] == rango_fechas[0]
        ]

if not historial.empty:
    primera = historial["timestamp"].min()
    ultima = historial["timestamp"].max()

    h1, h2, h3 = st.columns(3)

    h1.metric("Mediciones válidas", len(historial))
    h2.metric("Primera medición", primera.strftime("%d/%m/%Y"))
    h3.metric("Última medición", ultima.strftime("%d/%m/%Y"))

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
        color_discrete_sequence=[AZUL]
    )

    fig_individual.update_traces(
        line=dict(width=3),
        marker=dict(size=6)
    )

    fig_individual = aplicar_estilo(fig_individual)
    st.plotly_chart(fig_individual, use_container_width=True)

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
        color_discrete_sequence=[TURQUESA]
    )

    fig_individual_spo2.update_traces(
        line=dict(width=3),
        marker=dict(size=6)
    )

    fig_individual_spo2 = aplicar_estilo(fig_individual_spo2)

    st.plotly_chart(
        fig_individual_spo2,
        use_container_width=True
    )
else:
    st.info(
        "No hay mediciones válidas para este estudiante "
        "en el período seleccionado."
    )


# ============================================================
# 14. HALLAZGOS DEL ANALISIS
# ============================================================

st.divider()
st.header("💡 Hallazgos del análisis")

st.caption(
    "Resultados descriptivos calculados con los filtros actuales."
)

conteo_horas = filtrado.groupby("hora").size()

if not conteo_horas.empty:
    hora_pico = int(conteo_horas.idxmax())
    cantidad_pico = int(conteo_horas.max())
    porcentaje_hora = cantidad_pico / total * 100

    st.markdown("### 🕒 1. Horario de mayor utilización")

    st.write(
        f"La hora con más registros es las **{hora_pico:02d}:00**, "
        f"con **{cantidad_pico} mediciones**, equivalentes al "
        f"**{porcentaje_hora:.2f}%** del conjunto filtrado."
    )

conteo_estudiantes = filtrado.groupby("student_id").size()

if not conteo_estudiantes.empty:
    promedio_estudiante = conteo_estudiantes.mean()
    max_mediciones = int(conteo_estudiantes.max())
    estudiante_mas_activo = conteo_estudiantes.idxmax()

    st.markdown("### 👥 2. Frecuencia de utilización")

    st.write(
        f"Se registran **{len(conteo_estudiantes)} estudiantes**, "
        f"con un promedio de **{promedio_estudiante:.2f} "
        f"mediciones por estudiante**. El identificador con más "
        f"registros es **{estudiante_mas_activo}**, con "
        f"{max_mediciones}."
    )

senal = pd.to_numeric(
    filtrado["signal_quality"],
    errors="coerce"
)

senal_disponible = senal.dropna()

st.markdown("### 📶 3. Calidad de la señal")

if not senal_disponible.empty:
    calidad_promedio = senal_disponible.mean()
    registros_sin_senal = int(senal.isna().sum())
    porcentaje_sin_senal = registros_sin_senal / total * 100

    st.write(
        f"La calidad de señal promedio es **{calidad_promedio:.3f}**. "
        f"Hay **{registros_sin_senal} registros** sin este dato "
        f"({porcentaje_sin_senal:.2f}% del conjunto filtrado)."
    )
else:
    st.write("No hay valores de calidad de señal disponibles.")

st.markdown("### 📊 Variabilidad de las mediciones válidas")

if not validas.empty:
    desviacion_bpm = validas["heart_rate_bpm"].std()
    desviacion_spo2 = validas["spo2_percent"].std()

    v1, v2 = st.columns(2)

    v1.metric(
        "Desviación estándar de BPM",
        f"{desviacion_bpm:.2f}"
        if pd.notna(desviacion_bpm) else "—"
    )

    v2.metric(
        "Desviación estándar de SpO₂",
        f"{desviacion_spo2:.2f}"
        if pd.notna(desviacion_spo2) else "—"
    )

    st.caption(
        "La desviación estándar describe la dispersión de los "
        "valores; no determina por sí sola un problema de salud."
    )
else:
    st.info("No hay mediciones válidas para calcular la variabilidad.")

st.markdown("### 🛡️ Calidad general de los registros")

st.write(
    f"**{cantidad_invalidas} de {total} registros** "
    f"({porcentaje_invalidas:.2f}%) están marcados como inválidos."
)


# ============================================================
# 15. COMPLETITUD Y VALORES ATIPICOS
# ============================================================

st.divider()
st.header("🔬 Análisis de calidad de datos")

st.write(
    "Se revisa la completitud y se detectan posibles valores "
    "atípicos mediante el rango intercuartílico (IQR). "
    "Un valor atípico no implica necesariamente un error."
)

columnas_revisar = [
    "timestamp",
    "student_id",
    "heart_rate_bpm",
    "spo2_percent",
    "signal_quality",
    "measurement_status"
]

tabla_faltantes = pd.DataFrame({
    "Variable": columnas_revisar,
    "Valores faltantes": [
        filtrado[col].isna().sum()
        for col in columnas_revisar
    ]
})

tabla_faltantes["Porcentaje faltante"] = (
    tabla_faltantes["Valores faltantes"] / total * 100
).round(2)

st.subheader("Completitud de los datos")

st.dataframe(
    tabla_faltantes,
    use_container_width=True,
    hide_index=True
)

st.subheader("Posibles valores atípicos")

if not validas.empty:
    atipicos_bpm = detectar_atipicos(
        validas,
        "heart_rate_bpm"
    )

    atipicos_spo2 = detectar_atipicos(
        validas,
        "spo2_percent"
    )

    a1, a2 = st.columns(2)

    a1.metric("Valores atípicos de BPM", len(atipicos_bpm))
    a2.metric("Valores atípicos de SpO₂", len(atipicos_spo2))

    filas_atipicas = []

    for columna, valores in [
        ("heart_rate_bpm", atipicos_bpm),
        ("spo2_percent", atipicos_spo2)
    ]:
        if not valores.empty:
            temporal = validas.loc[
                valores.index,
                ["timestamp", "student_id", columna]
            ].copy()

            temporal = temporal.rename(
                columns={columna: "valor"}
            )

            temporal["variable"] = columna
            filas_atipicas.append(temporal)

    if filas_atipicas:
        tabla_atipicos = pd.concat(
            filas_atipicas,
            ignore_index=True
        )

        st.dataframe(
            tabla_atipicos,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success(
            "No se detectaron valores atípicos con el criterio IQR."
        )
else:
    st.info("No hay mediciones válidas para detectar valores atípicos.")


# ============================================================
# 16. REVISION DE MEDICIONES INVALIDAS
# ============================================================

st.divider()
st.header("🔎 Revisión de mediciones inválidas")

st.write(
    "Consulta los registros identificados como inválidos "
    "en el archivo original."
)

st.metric(
    "Mediciones inválidas con los filtros actuales",
    cantidad_invalidas
)

if registros_invalidos.empty:
    st.success(
        "No hay mediciones inválidas con los filtros actuales."
    )
else:
    st.warning(
        f"Se encontraron {cantidad_invalidas} mediciones inválidas."
    )

    columnas_invalidas = [
        "timestamp",
        "student_id",
        "device_id",
        "heart_rate_bpm",
        "spo2_percent",
        "signal_quality",
        "measurement_status"
    ]

    columnas_disponibles = [
        columna for columna in columnas_invalidas
        if columna in registros_invalidos.columns
    ]

    st.dataframe(
        registros_invalidos[columnas_disponibles],
        use_container_width=True,
        hide_index=True
    )

    csv_invalidos = registros_invalidos[
        columnas_disponibles
    ].to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="📥 Descargar mediciones inválidas",
        data=csv_invalidos,
        file_name="mediciones_invalidas_eafit.csv",
        mime="text/csv"
    )

    st.caption(
        "La etiqueta invalid proviene del archivo original. "
        "Los registros no se eliminan ni se modifican."
    )


# ============================================================
# 17. TABLA GENERAL
# ============================================================

with st.expander("📋 Consultar tabla de registros filtrados"):
    st.dataframe(
        filtrado,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 18. PIE DE PAGINA
# ============================================================

st.divider()

st.caption(
    "Pulse EAFIT · Proyecto Integrador de Computación Física e IoT"
)
