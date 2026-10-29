
import streamlit as st
import pandas as pd
import plotly.express as px

# ==================================================
# 1. CONFIGURACION GENERAL
# ==================================================

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

# ==================================================
# 2. CARGA Y PREPARACION DE DATOS
# ==================================================

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
            f"Faltan columnas en el CSV: {', '.join(faltantes)}"
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

except FileNotFoundError:
    st.error(
        "No se encontró el archivo CSV. Comprueba que "
        "esté en la raíz del repositorio y que su nombre "
        "sea proyecto_integrador_eafit_max30102.csv."
    )
    st.stop()

except Exception as error:
    st.error(f"No fue posible cargar los datos: {error}")
    st.stop()


if df.empty:
    st.error("El archivo no contiene registros con fechas válidas.")
    st.stop()


# ==================================================
# 3. FILTROS
# ==================================================

st.sidebar.title("🔎 Filtros")

fechas = df["fecha"].dropna()

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


# ==================================================
# 4. APLICAR FILTROS
# ==================================================

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
        "No hay mediciones para los filtros seleccionados. "
        "Cambia el rango de fechas, estudiante o estado."
    )
    st.stop()

validas = filtrado[
    filtrado["measurement_status"] == "valid"
].copy()

invalidas = (
    filtrado["measurement_status"] == "invalid"
).sum()

total = len(filtrado)

porcentaje_invalidas = (
    invalidas / total * 100 if total else 0
)

bpm_promedio = validas["heart_rate_bpm"].mean()
spo2_promedio = validas["spo2_percent"].mean()


# ==================================================
# 5. INDICADORES GENERALES
# ==================================================

st.subheader("📊 Indicadores generales")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Mediciones",
    f"{total:,}"
)

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

c5.metric(
    "Inválidas",
    f"{porcentaje_invalidas:.2f}%"
)

st.divider()


# ==================================================
# 6. GRAFICO 1: MEDICIONES POR FECHA
# ==================================================

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

st.plotly_chart(
    fig_fecha,
    use_container_width=True
)


# ==================================================
# 7. GRAFICOS 2 Y 3: DISTRIBUCIONES
# ==================================================

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


# ==================================================
# 8. GRAFICO 4: USO POR HORA
# ==================================================

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
    template="plotly_dark"
)

fig_hora.update_xaxes(dtick=1)

st.plotly_chart(
    fig_hora,
    use_container_width=True
)


# ==================================================
# 9. GRAFICO 5: ESTADO DE MEDICIONES
# ==================================================

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
    hole=0.45,
    title="Proporción de mediciones por estado",
    template="plotly_dark"
)

st.plotly_chart(
    fig_estado,
    use_container_width=True
)


# ==================================================
# 10. GRAFICO 6: USO POR DIA DE LA SEMANA
# ==================================================

st.subheader("📆 Uso por día de la semana")

orden_dias = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo"
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

st.plotly_chart(
    fig_dia,
    use_container_width=True
)


# ==================================================
# 11. SEGUIMIENTO INDIVIDUAL
# ==================================================

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

# Aplicar el rango de fechas al historial individual.
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

    h1.metric(
        "Mediciones válidas",
        len(historial)
    )

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


# ==================================================
# 12. HALLAZGOS DEL ANALISIS
# ==================================================

st.divider()
st.header("💡 Hallazgos del análisis")

st.caption(
    "Resultados descriptivos calculados con los filtros activos. "
    "Las conclusiones se refieren al uso del dispositivo y "
    "a las características del conjunto de datos."
)

# Hallazgo 1: hora de mayor uso

conteo_horas = filtrado.groupby("hora").size()

if not conteo_horas.empty:
    hora_pico = int(conteo_horas.idxmax())
    cantidad_pico = int(conteo_horas.max())

    porcentaje_hora = (
        cantidad_pico / total * 100 if total else 0
    )

    st.markdown("### 🕒 1. Horario de mayor utilización")

    st.write(
        f"La hora con más registros es las "
        f"**{hora_pico:02d}:00**, con **{cantidad_pico} "
        f"mediciones**, equivalentes al "
        f"**{porcentaje_hora:.2f}%** de las mediciones filtradas."
    )

# Hallazgo 2: frecuencia de uso por estudiante

conteo_estudiantes = filtrado.groupby("student_id").size()

if not conteo_estudiantes.empty:
    promedio_estudiante = conteo_estudiantes.mean()

    max_mediciones = int(conteo_estudiantes.max())

    estudiante_mas_activo = conteo_estudiantes.idxmax()

    st.markdown("### 👥 2. Frecuencia de utilización")

    st.write(
        f"Se registran **{len(conteo_estudiantes)} estudiantes** "
        f"en los datos filtrados, con un promedio de "
        f"**{promedio_estudiante:.2f} mediciones por estudiante**. "
        f"El identificador con más registros es "
        f"**{estudiante_mas_activo}**, con {max_mediciones}."
    )

# Hallazgo 3: calidad de la señal

senal = pd.to_numeric(
    filtrado["signal_quality"],
    errors="coerce"
)

senal_disponible = senal.dropna()

st.markdown("### 📶 3. Calidad de la señal")

if not senal_disponible.empty:
    calidad_promedio = senal_disponible.mean()

    registros_sin_senal = int(senal.isna().sum())

    porcentaje_sin_senal = (
        registros_sin_senal / total * 100 if total else 0
    )

    st.write(
        f"La calidad de señal promedio es "
        f"**{calidad_promedio:.3f}** sobre la escala registrada. "
        f"Hay **{registros_sin_senal} registros** sin este dato "
        f"({porcentaje_sin_senal:.2f}% del conjunto filtrado)."
    )
else:
    st.write(
        "No hay valores de calidad de señal disponibles "
        "para los filtros seleccionados."
    )

# Variabilidad de las mediciones

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
        "valores. Por sí sola no indica un problema de salud."
    )
else:
    st.info(
        "No hay mediciones válidas para calcular la variabilidad."
    )

# Estado de los registros

st.markdown("### 🛡️ Calidad general de los registros")

st.write(
    f"**{int(invalidas)} de {total} registros** "
    f"({porcentaje_invalidas:.2f}%) están marcados como inválidos."
)


# ==================================================
# 13. CALIDAD DE LOS DATOS Y VALORES ATIPICOS
# ==================================================

st.divider()
st.header("🔬 Análisis de calidad de datos")

st.write(
    "Esta sección revisa la completitud de los registros y "
    "detecta posibles valores atípicos mediante el rango "
    "intercuartílico (IQR). Un valor atípico no implica "
    "necesariamente un error ni una condición médica."
)

# Completitud de variables

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
    tabla_faltantes["Valores faltantes"]
    / total * 100
).round(2)

st.subheader("Completitud de los datos")

st.dataframe(
    tabla_faltantes,
    use_container_width=True,
    hide_index=True
)

# Función para detectar valores atípicos por IQR

def detectar_atipicos(datos, columna):
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

    a1.metric(
        "Valores atípicos de BPM",
        len(atipicos_bpm)
    )

    a2.metric(
        "Valores atípicos de SpO₂",
        len(atipicos_spo2)
    )

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
            "No se detectaron valores atípicos con el criterio "
            "IQR en las mediciones válidas filtradas."
        )
else:
    st.info(
        "No hay mediciones válidas para detectar valores atípicos."
    )


# ==================================================
# 14. TABLA DE DATOS
# ==================================================

with st.expander("📋 Consultar tabla de registros"):
    st.dataframe(
        filtrado,
        use_container_width=True,
        hide_index=True
    )

st.caption(
    "Pulse EAFIT · Proyecto Integrador de Computación Física e IoT"
)

