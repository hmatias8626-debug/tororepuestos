import streamlit as st
from db import (
    listar_presupuestos, obtener_items, obtener_productos_stock,
    registrar_devolucion, registrar_cambio, obtener_devoluciones,
)

st.set_page_config(page_title="Devoluciones y cambios", page_icon="↩️", layout="wide")
st.title("↩️ Devoluciones y cambios")

if "dev_nonce" not in st.session_state:
    st.session_state.dev_nonce = 0
n = st.session_state.dev_nonce

presupuestos_confirmados = listar_presupuestos(estado="confirmado")

if not presupuestos_confirmados:
    st.info("No hay presupuestos confirmados todavía.")
    st.stop()

opciones = {f"{p['numero']} — {p['fecha']} — ${p['total']:,.0f}".replace(",", "."): p["id"] for p in presupuestos_confirmados}
presupuesto_sel = st.selectbox("Presupuesto", list(opciones.keys()), key=f"dev_presupuesto_{n}")
presupuesto_id = opciones[presupuesto_sel]

items = obtener_items(presupuesto_id)
productos_disponibles = obtener_productos_stock()
opciones_prod = {f"{p['codigo']} — {p['descripcion'] or ''}": p["id"] for p in productos_disponibles}

st.subheader("Ítems del presupuesto")

for it in items:
    prod = it.get("productos") or {}
    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.write(f"**{prod.get('codigo', '?')}** — {prod.get('descripcion', '')}")
        c2.write(f"Vendido: {it['cantidad']}")
        c3.write(f"${it['precio_unitario']:,.0f} c/u".replace(",", "."))

        accion = st.radio(
            "Acción", ["Ninguna", "Devolver", "Cambiar por otro producto"],
            key=f"accion_{it['id']}_{n}", horizontal=True,
        )

        if accion == "Devolver":
            cantidad_dev = st.number_input(
                "Cantidad a devolver", min_value=1, max_value=int(it["cantidad"]), step=1, key=f"cant_dev_{it['id']}_{n}"
            )
            if st.button("Confirmar devolución", key=f"btn_dev_{it['id']}_{n}"):
                registrar_devolucion(presupuesto_id, it["producto_id"], int(cantidad_dev))
                st.session_state.dev_nonce += 1
                st.success(f"Devueltas {cantidad_dev} unidad(es) de {prod.get('codigo')}. Stock actualizado.")
                st.rerun()

        elif accion == "Cambiar por otro producto":
            cc1, cc2 = st.columns(2)
            with cc1:
                cantidad_cambio_vieja = st.number_input(
                    "Cantidad a cambiar", min_value=1, max_value=int(it["cantidad"]), step=1,
                    key=f"cant_cambio_vieja_{it['id']}_{n}",
                )
            with cc2:
                producto_nuevo_sel = st.selectbox(
                    "Producto nuevo", list(opciones_prod.keys()), key=f"prod_nuevo_{it['id']}_{n}"
                )
            cantidad_nueva = st.number_input(
                "Cantidad del producto nuevo", min_value=1, step=1, key=f"cant_nueva_{it['id']}_{n}"
            )
            if st.button("Confirmar cambio", key=f"btn_cambio_{it['id']}_{n}"):
                try:
                    registrar_cambio(
                        presupuesto_id=presupuesto_id,
                        producto_id=it["producto_id"],
                        cantidad=int(cantidad_cambio_vieja),
                        producto_cambio_id=opciones_prod[producto_nuevo_sel],
                        cantidad_cambio=int(cantidad_nueva),
                    )
                    st.session_state.dev_nonce += 1
                    st.success(f"Cambio registrado: {prod.get('codigo')} por {producto_nuevo_sel.split(' — ')[0]}.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo registrar el cambio: {e}")

historial = obtener_devoluciones(presupuesto_id)
if historial:
    st.divider()
    st.subheader("Historial de devoluciones/cambios de este presupuesto")
    for h in historial:
        prod = h.get("producto") or {}
        if h["tipo"] == "devolucion":
            st.write(f"↩️ {h['fecha']} — Devolución: {h['cantidad']} x {prod.get('codigo', '?')}")
        else:
            prod_cambio = h.get("producto_cambio") or {}
            st.write(
                f"🔄 {h['fecha']} — Cambio: {h['cantidad']} x {prod.get('codigo', '?')} "
                f"por {h['cantidad_cambio']} x {prod_cambio.get('codigo', '?')}"
            )
