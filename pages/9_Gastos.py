from datetime import date

import pandas as pd
import streamlit as st
from db import registrar_gasto, obtener_gastos, eliminar_gasto

st.set_page_config(page_title="Gastos", page_icon="💸", layout="wide")
st.title("💸 Gastos")

st.subheader("Cargar gasto nuevo")
c1, c2, c3 = st.columns([3, 1, 1])
with c1:
    descripcion = st.text_input("Descripción", placeholder="ej: Alquiler julio, Luz, Sueldo empleado")
with c2:
    monto = st.number_input("Monto", min_value=0.0, step=100.0, format="%.2f")
with c3:
    fecha = st.date_input("Fecha", value=date.today())

if st.button("💾 Guardar gasto", type="primary"):
    if not descripcion or monto <= 0:
        st.error("Completá la descripción y un monto mayor a 0.")
    else:
        registrar_gasto(descripcion, float(monto), fecha.isoformat())
        st.success(f"Gasto **{descripcion}** guardado.")
        st.rerun()

st.divider()

gastos = obtener_gastos()
if not gastos:
    st.info("Todavía no cargaste gastos.")
    st.stop()

df = pd.DataFrame(gastos)
df["fecha"] = pd.to_datetime(df["fecha"])
df["monto"] = df["monto"].astype(float)
df["mes"] = df["fecha"].dt.to_period("M").astype(str)
df["dia"] = df["fecha"].dt.date

tab_dia, tab_mes, tab_historial = st.tabs(["Gastos del día", "Gastos del mes", "Historial completo"])

with tab_dia:
    dias_disponibles = sorted(df["dia"].unique(), reverse=True)
    idx = dias_disponibles.index(date.today()) if date.today() in dias_disponibles else 0
    fecha_sel = st.selectbox("Día", dias_disponibles, index=idx, key="gastos_dia")
    sub = df[df["dia"] == fecha_sel]

    st.metric("Total del día", f"${sub['monto'].sum():,.0f}".replace(",", "."))
    for _, row in sub.sort_values("id", ascending=False).iterrows():
        rc1, rc2 = st.columns([5, 1])
        rc1.write(f"{row['descripcion']} — ${row['monto']:,.0f}".replace(",", "."))
        if rc2.button("🗑️ Borrar", key=f"borrar_gasto_{row['id']}"):
            eliminar_gasto(int(row["id"]))
            st.rerun()

with tab_mes:
    meses_disponibles = sorted(df["mes"].unique(), reverse=True)
    mes_sel = st.selectbox("Mes", meses_disponibles, key="gastos_mes")
    sub = df[df["mes"] == mes_sel]

    st.metric("Total del mes", f"${sub['monto'].sum():,.0f}".replace(",", "."))
    por_dia = sub.groupby("dia")["monto"].sum().reset_index().sort_values("dia", ascending=False)
    st.dataframe(
        por_dia,
        hide_index=True,
        use_container_width=True,
        column_config={"dia": "Día", "monto": st.column_config.NumberColumn("Total", format="$ %.0f")},
    )

with tab_historial:
    st.dataframe(
        df[["fecha", "descripcion", "monto"]].sort_values("fecha", ascending=False),
        hide_index=True,
        use_container_width=True,
        column_config={
            "fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
            "descripcion": "Descripción",
            "monto": st.column_config.NumberColumn("Monto", format="$ %.0f"),
        },
    )
