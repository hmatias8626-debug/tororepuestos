import streamlit as st
from db import listar_presupuestos, obtener_items, anular_presupuesto, confirmar_presupuesto, cancelar_presupuesto

st.set_page_config(page_title="Historial de presupuestos", page_icon="📋", layout="wide")
st.title("📋 Historial de presupuestos")

estado = st.selectbox("Estado", ["Todos", "borrador", "confirmado", "anulado", "cancelado"])
presupuestos = listar_presupuestos(estado=estado)

if not presupuestos:
    st.info("No hay presupuestos para mostrar.")
    st.stop()

estado_emoji = {"borrador": "📝", "confirmado": "✅", "anulado": "❌", "cancelado": "🚫"}

for p in presupuestos:
    emoji = estado_emoji.get(p["estado"], "")
    with st.expander(f"{emoji} {p['numero']} — {p['fecha']} — ${p['total']:,.0f} — {p['estado']}".replace(",", ".")):
        st.caption(f"Creado: {p['fecha']}")
        if p.get("fecha_confirmacion"):
            st.caption(f"Confirmado: {p['fecha_confirmacion']} — Pago: {p.get('metodo_pago', '?')}")

        items = obtener_items(p["id"])
        for it in items:
            prod = it.get("productos") or {}
            st.write(
                f"{it['cantidad']} x {prod.get('codigo', '?')} "
                f"({prod.get('descripcion', '')}) — "
                f"${it['subtotal']:,.0f}".replace(",", ".")
            )

        if p["estado"] == "borrador":
            st.divider()
            metodo = st.selectbox(
                "Método de pago", ["efectivo", "transferencia", "tarjeta"], key=f"metodo_{p['id']}"
            )
            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button("✅ Confirmar venta", key=f"confirmar_{p['id']}", type="primary", use_container_width=True):
                    try:
                        confirmar_presupuesto(p["id"], metodo)
                        st.success("Presupuesto confirmado, stock descontado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo confirmar: {e}")
            with bc2:
                if st.button("🚫 Cancelar presupuesto", key=f"cancelar_{p['id']}", use_container_width=True):
                    try:
                        cancelar_presupuesto(p["id"])
                        st.success("Presupuesto cancelado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo cancelar: {e}")

        if p["estado"] == "confirmado":
            if st.button("Anular (devuelve stock)", key=f"anular_{p['id']}"):
                try:
                    anular_presupuesto(p["id"])
                    st.success("Presupuesto anulado, stock devuelto.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo anular: {e}")
