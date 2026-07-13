from datetime import date

import pandas as pd
import streamlit as st
from db import obtener_ventas_confirmadas

st.set_page_config(page_title="Ventas", page_icon="💰", layout="wide")
st.title("💰 Ventas diarias y mensuales")

ventas = obtener_ventas_confirmadas()
if not ventas:
    st.info("Todavía no hay ventas confirmadas.")
    st.stop()

df = pd.DataFrame(ventas)
df["fecha_confirmacion"] = pd.to_datetime(df["fecha_confirmacion"])
df["total"] = df["total"].astype(float)
df["mes"] = df["fecha_confirmacion"].dt.to_period("M").astype(str)
df["dia"] = df["fecha_confirmacion"].dt.date


def resumen_metodo_pago(sub_df):
    resumen = sub_df.groupby("metodo_pago")["total"].sum()
    return {m: resumen.get(m, 0.0) for m in ["efectivo", "transferencia", "tarjeta"]}


def mostrar_metricas(sub_df):
    st.metric("Total", f"${sub_df['total'].sum():,.0f}".replace(",", "."))
    metodo = resumen_metodo_pago(sub_df)
    c1, c2, c3 = st.columns(3)
    c1.metric("💵 Efectivo", f"${metodo['efectivo']:,.0f}".replace(",", "."))
    c2.metric("🏦 Transferencia", f"${metodo['transferencia']:,.0f}".replace(",", "."))
    c3.metric("💳 Tarjeta", f"${metodo['tarjeta']:,.0f}".replace(",", "."))


tab_dia, tab_mes, tab_historial = st.tabs(["Ventas del día", "Ventas del mes", "Historial completo"])

with tab_dia:
    dias_disponibles = sorted(df["dia"].unique(), reverse=True)
    idx = dias_disponibles.index(date.today()) if date.today() in dias_disponibles else 0
    fecha_sel = st.selectbox("Día", dias_disponibles, index=idx)
    sub = df[df["dia"] == fecha_sel]

    mostrar_metricas(sub)
    st.dataframe(
        sub[["numero", "fecha_confirmacion", "metodo_pago", "total"]].sort_values("fecha_confirmacion", ascending=False),
        hide_index=True,
        use_container_width=True,
        column_config={
            "numero": "Presupuesto",
            "fecha_confirmacion": st.column_config.DatetimeColumn("Fecha", format="DD/MM/YYYY"),
            "metodo_pago": "Pago",
            "total": st.column_config.NumberColumn("Total", format="$ %.0f"),
        },
    )

with tab_mes:
    meses_disponibles = sorted(df["mes"].unique(), reverse=True)
    mes_sel = st.selectbox("Mes", meses_disponibles)
    sub = df[df["mes"] == mes_sel]

    mostrar_metricas(sub)
    por_dia = sub.groupby("dia")["total"].sum().reset_index().sort_values("dia", ascending=False)
    st.dataframe(
        por_dia,
        hide_index=True,
        use_container_width=True,
        column_config={"dia": "Día", "total": st.column_config.NumberColumn("Total", format="$ %.0f")},
    )

with tab_historial:
    resumen_dias = (
        df.groupby("dia")
        .agg(total=("total", "sum"), ventas=("id", "count"))
        .reset_index()
        .sort_values("dia", ascending=False)
    )
    st.dataframe(
        resumen_dias,
        hide_index=True,
        use_container_width=True,
        column_config={
            "dia": "Día",
            "total": st.column_config.NumberColumn("Total", format="$ %.0f"),
            "ventas": "Cantidad de ventas",
        },
    )
