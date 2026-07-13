import streamlit as st
from db import (
    buscar_productos, obtener_familias, obtener_subfamilias,
    obtener_marcas_disponibles, obtener_modelos_disponibles, get_client,
)

st.set_page_config(page_title="TORO REPUESTOS", page_icon="🔧", layout="wide")

if "carrito" not in st.session_state:
    st.session_state.carrito = {}  # producto_id -> cantidad

col_izq, col_der = st.columns([3, 2])

with col_izq:
    st.title("🔧 TORO REPUESTOS")
    st.caption("Catálogo y control de stock")

    texto = st.text_input("Buscar por código o descripción (opcional)", placeholder="ej: 8PK2205, correa...")

    c1, c2 = st.columns(2)
    with c1:
        familias = ["Todas"] + obtener_familias()
        familia = st.selectbox("Familia", familias)
    with c2:
        subfamilias = ["Todas"] + obtener_subfamilias(familia)
        subfamilia = st.selectbox("Subfamilia", subfamilias)

    c3, c4 = st.columns(2)
    with c3:
        marcas = ["Todas"] + obtener_marcas_disponibles(familia, subfamilia)
        marca_vehiculo = st.selectbox("Marca de vehículo", marcas)
    with c4:
        modelos = ["Todos"] + obtener_modelos_disponibles(marca_vehiculo, familia, subfamilia)
        modelo = st.selectbox("Modelo", modelos)

    productos = buscar_productos(
        texto=texto, familia=familia, subfamilia=subfamilia,
        marca_vehiculo=marca_vehiculo, modelo=modelo,
    )

    st.write(f"**{len(productos)} productos encontrados**")

    for p in productos:
        with st.container(border=True):
            cc1, cc2, cc3, cc4, cc5 = st.columns([1, 1, 3, 1, 1])
            cc1.write(f"**{p['codigo']}**")
            cc2.write(p["marca"] or "-")
            cc3.write(p["descripcion"] or "-")
            cc4.write(f"${p['precio']:,.0f}".replace(",", "."))

            stock = p["stock"]
            color = "🟢" if stock > 3 else ("🟡" if stock > 0 else "🔴")
            cc5.write(f"{color} Stock: {stock}")

            if stock > 0:
                cantidad_actual = st.session_state.carrito.get(p["id"], 0)
                nueva_cant = st.number_input(
                    "Cantidad", min_value=0, max_value=stock, value=cantidad_actual,
                    key=f"cant_{p['id']}", label_visibility="collapsed"
                )
                if nueva_cant != cantidad_actual:
                    if nueva_cant == 0:
                        st.session_state.carrito.pop(p["id"], None)
                    else:
                        st.session_state.carrito[p["id"]] = nueva_cant
                    st.rerun()

with col_der:
    st.markdown("####  ")  # alinea con el titulo de la izquierda
    st.markdown(
        """
        <div style="border:1px solid #ddd; border-radius:8px; padding:16px 20px; background:white;">
            <div style="text-align:center; border-bottom:1px solid #ddd; padding-bottom:8px; margin-bottom:8px;">
                <strong>PRESUPUESTO</strong><br/>
                <span style="font-size:12px; color:#888;">Comprobante no válido como factura</span>
            </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.carrito:
        client = get_client()
        ids_carrito = list(st.session_state.carrito.keys())
        detalle = {p["id"]: p for p in client.table("toro_productos").select("*").in_("id", ids_carrito).execute().data}

        filas_html = "<table style='width:100%; font-size:13px; border-collapse:collapse;'>"
        filas_html += "<tr style='color:#888; font-size:11px;'><td>Detalle</td><td style='text-align:right;'>P.Unit</td><td style='text-align:right;'>Importe</td></tr>"
        total = 0
        for pid, cant in st.session_state.carrito.items():
            prod = detalle.get(pid)
            if not prod:
                continue
            subtotal = prod["precio"] * cant
            total += subtotal
            filas_html += (
                f"<tr style='border-top:1px solid #eee;'>"
                f"<td style='padding:4px 0;'>{cant} x {prod['codigo']}</td>"
                f"<td style='text-align:right;'>${prod['precio']:,.0f}</td>"
                f"<td style='text-align:right;'>${subtotal:,.0f}</td></tr>"
            ).replace(",", ".")
        filas_html += "</table>"
        st.markdown(filas_html, unsafe_allow_html=True)

        st.markdown(
            f"""
            <div style="border-top:2px solid #333; margin-top:8px; padding-top:8px; display:flex; justify-content:space-between; font-weight:bold;">
                <span>TOTAL</span><span>${total:,.0f}</span>
            </div>
            </div>
            """.replace(",", "."),
            unsafe_allow_html=True,
        )

        st.write("")
        if st.button("Ir al carrito →", type="primary", use_container_width=True):
            st.switch_page("pages/1_Carrito.py")
    else:
        st.markdown(
            "<p style='color:#888; font-size:13px; text-align:center; padding:20px 0;'>"
            "Elegí productos con la cantidad para que aparezcan acá.</p></div>",
            unsafe_allow_html=True,
        )
