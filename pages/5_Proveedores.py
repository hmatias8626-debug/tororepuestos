import streamlit as st
from db import (
    obtener_proveedores, crear_proveedor, obtener_productos_stock,
    registrar_compra, obtener_compras, marcar_compra_pagada, obtener_deuda_por_proveedor,
)

st.set_page_config(page_title="Proveedores", page_icon="🚚", layout="wide")
st.title("🚚 Proveedores y compras")

if "prov_nonce" not in st.session_state:
    st.session_state.prov_nonce = 0
n = st.session_state.prov_nonce

proveedores = obtener_proveedores()
productos = obtener_productos_stock()

tab_deuda, tab_compra, tab_proveedor = st.tabs(["Deuda por proveedor", "Registrar compra", "Agregar proveedor"])

with tab_deuda:
    deuda = obtener_deuda_por_proveedor()
    if not deuda:
        st.info("Todavía no cargaste proveedores.")
    else:
        total_deuda = sum(d["deuda"] for d in deuda)
        st.metric("Deuda total pendiente", f"${total_deuda:,.0f}".replace(",", "."))
        for d in sorted(deuda, key=lambda x: -x["deuda"]):
            with st.expander(f"{d['nombre']} — ${d['deuda']:,.0f}".replace(",", ".")):
                pendientes = obtener_compras(proveedor_id=d["proveedor_id"], solo_pendientes=True)
                if not pendientes:
                    st.caption("Sin compras pendientes de pago.")
                for c in pendientes:
                    prod = c.get("productos") or {}
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(f"{c['fecha']} — {c['cantidad']} x {prod.get('codigo', '?')} ({prod.get('descripcion', '')})")
                    c2.write(f"${c['total']:,.0f}".replace(",", "."))
                    if c3.button("Marcar pagada", key=f"pagar_{c['id']}"):
                        marcar_compra_pagada(c["id"])
                        st.rerun()

with tab_compra:
    if not proveedores:
        st.warning("Primero agregá un proveedor en la pestaña correspondiente.")
    elif not productos:
        st.warning("Todavía no hay productos cargados.")
    else:
        nombres_prov = {p["nombre"]: p["id"] for p in proveedores}
        opciones_prod = {f"{p['codigo']} — {p['descripcion'] or ''}": p["id"] for p in productos}

        proveedor_sel = st.selectbox("Proveedor", list(nombres_prov.keys()), key=f"compra_prov_{n}")
        producto_sel = st.selectbox("Producto", list(opciones_prod.keys()), key=f"compra_prod_{n}")

        c1, c2, c3 = st.columns(3)
        with c1:
            cantidad = st.number_input("Cantidad comprada", min_value=1, step=1, key=f"compra_cant_{n}")
        with c2:
            costo_unitario = st.number_input("Costo unitario", min_value=0.0, step=100.0, format="%.2f", key=f"compra_costo_{n}")
        with c3:
            pagada = st.checkbox("Ya la pagué", key=f"compra_pagada_{n}")

        st.caption(f"Total de la compra: ${cantidad * costo_unitario:,.0f}".replace(",", "."))

        if st.button("Registrar compra", type="primary"):
            registrar_compra(
                proveedor_id=nombres_prov[proveedor_sel],
                producto_id=opciones_prod[producto_sel],
                cantidad=int(cantidad),
                costo_unitario=float(costo_unitario),
                pagada=pagada,
            )
            st.session_state.prov_nonce += 1
            st.success(f"Compra registrada. Stock de {producto_sel.split(' — ')[0]} incrementado en {cantidad}.")
            st.rerun()

with tab_proveedor:
    nombre = st.text_input("Nombre del proveedor", key=f"nuevo_prov_nombre_{n}")
    contacto = st.text_input("Contacto (teléfono, email, etc.)", key=f"nuevo_prov_contacto_{n}")
    if st.button("Guardar proveedor", type="primary"):
        if not nombre:
            st.error("Falta el nombre del proveedor.")
        else:
            try:
                crear_proveedor(nombre, contacto)
                st.session_state.prov_nonce += 1
                st.success(f"Proveedor **{nombre}** agregado.")
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo guardar: {e}")

    if proveedores:
        st.divider()
        st.write("**Proveedores existentes:**")
        for p in proveedores:
            st.write(f"- {p['nombre']}" + (f" ({p['contacto']})" if p.get("contacto") else ""))
