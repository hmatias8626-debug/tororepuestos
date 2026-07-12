import streamlit as st
from db import crear_presupuesto, agregar_item, confirmar_presupuesto, get_client

st.set_page_config(page_title="Nuevo presupuesto", page_icon="🧾", layout="wide")
st.title("🧾 Nuevo presupuesto")

if "carrito" not in st.session_state or not st.session_state.carrito:
    st.info("Todavía no agregaste productos. Volvé al catálogo para elegir.")
    if st.button("← Ir al catálogo"):
        st.switch_page("app.py")
    st.stop()

# Traemos el detalle actual de cada producto en el carrito (por si cambió el precio/stock)
ids = list(st.session_state.carrito.keys())
client = get_client()
detalle = client.table("toro_productos").select("*").in_("id", ids).execute().data
detalle_por_id = {p["id"]: p for p in detalle}

total = 0
st.subheader("Ítems del presupuesto")
for pid, cantidad in list(st.session_state.carrito.items()):
    p = detalle_por_id.get(pid)
    if not p:
        continue
    subtotal = p["precio"] * cantidad
    total += subtotal

    c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
    c1.write(f"**{p['codigo']}** — {p['descripcion'] or ''}")
    c2.write(f"x{cantidad}")
    c3.write(f"${p['precio']:,.0f}".replace(",", "."))
    c4.write(f"${subtotal:,.0f}".replace(",", "."))
    if c5.button("Quitar", key=f"quitar_{pid}"):
        st.session_state.carrito.pop(pid, None)
        st.rerun()

    if cantidad > p["stock"]:
        st.error(f"⚠️ Stock insuficiente para {p['codigo']}: pediste {cantidad}, hay {p['stock']}.")

st.divider()
st.metric("Total del presupuesto", f"${total:,.0f}".replace(",", "."))

col_a, col_b = st.columns(2)
with col_a:
    if st.button("← Seguir agregando productos", use_container_width=True):
        st.switch_page("app.py")

with col_b:
    hay_stock_insuficiente = any(
        cantidad > detalle_por_id[pid]["stock"]
        for pid, cantidad in st.session_state.carrito.items()
        if pid in detalle_por_id
    )
    if st.button("✅ Confirmar presupuesto", type="primary", use_container_width=True, disabled=hay_stock_insuficiente):
        presupuesto = crear_presupuesto()
        for pid, cantidad in st.session_state.carrito.items():
            p = detalle_por_id[pid]
            agregar_item(presupuesto["id"], pid, cantidad, p["precio"])
        try:
            confirmar_presupuesto(presupuesto["id"])
            st.session_state.carrito = {}
            st.success(f"Presupuesto {presupuesto['numero']} confirmado. Stock descontado.")
            st.balloons()
        except Exception as e:
            st.error(f"No se pudo confirmar: {e}")
