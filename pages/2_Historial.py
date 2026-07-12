import streamlit as st
from db import listar_presupuestos, obtener_items, anular_presupuesto

st.set_page_config(page_title="Historial de presupuestos", page_icon="📋", layout="wide")
st.title("📋 Historial de presupuestos")

estado = st.selectbox("Estado", ["Todos", "borrador", "confirmado", "anulado"])
presupuestos = listar_presupuestos(estado=estado)

if not presupuestos:
    st.info("No hay presupuestos para mostrar.")
    st.stop()

for p in presupuestos:
    estado_emoji = {"borrador": "📝", "confirmado": "✅", "anulado": "❌"}.get(p["estado"], "")
    with st.expander(f"{estado_emoji} {p['numero']} — {p['fecha']} — ${p['total']:,.0f} — {p['estado']}".replace(",", ".")):
        items = obtener_items(p["id"])
        for it in items:
            prod = it.get("productos") or {}
            st.write(
                f"{it['cantidad']} x {prod.get('codigo', '?')} "
                f"({prod.get('descripcion', '')}) — "
                f"${it['subtotal']:,.0f}".replace(",", ".")
            )

        if p["estado"] == "confirmado":
            if st.button("Anular (devuelve stock)", key=f"anular_{p['id']}"):
                try:
                    anular_presupuesto(p["id"])
                    st.success("Presupuesto anulado, stock devuelto.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo anular: {e}")
