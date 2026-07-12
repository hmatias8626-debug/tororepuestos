import streamlit as st
from db import buscar_productos, obtener_categorias, obtener_marcas_vehiculo

st.set_page_config(page_title="TORO REPUESTOS", page_icon="🔧", layout="wide")

st.title("🔧 TORO REPUESTOS")
st.caption("Catálogo y control de stock")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    texto = st.text_input("Buscar por código o descripción", placeholder="ej: 8PK2205, gol, correa...")
with col2:
    categorias = ["Todas"] + obtener_categorias()
    categoria = st.selectbox("Categoría", categorias)
with col3:
    marcas = ["Todas"] + obtener_marcas_vehiculo()
    marca_vehiculo = st.selectbox("Marca de vehículo", marcas)

productos = buscar_productos(texto=texto, categoria=categoria, marca_vehiculo=marca_vehiculo)

st.write(f"**{len(productos)} productos encontrados**")

if "carrito" not in st.session_state:
    st.session_state.carrito = {}  # producto_id -> cantidad

for p in productos:
    with st.container(border=True):
        c1, c2, c3, c4, c5 = st.columns([1, 1, 3, 1, 1])
        c1.write(f"**{p['codigo']}**")
        c2.write(p["marca"] or "-")
        c3.write(p["descripcion"] or "-")
        c4.write(f"${p['precio']:,.0f}".replace(",", "."))

        stock = p["stock"]
        color = "🟢" if stock > 3 else ("🟡" if stock > 0 else "🔴")
        c5.write(f"{color} Stock: {stock}")

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

if st.session_state.carrito:
    st.sidebar.header("🧾 Presupuesto actual")
    total = 0
    for pid, cant in st.session_state.carrito.items():
        prod = next((p for p in productos if p["id"] == pid), None)
        if prod:
            subtotal = prod["precio"] * cant
            total += subtotal
            st.sidebar.write(f"{cant} x {prod['codigo']} — ${subtotal:,.0f}".replace(",", "."))
    st.sidebar.metric("Total", f"${total:,.0f}".replace(",", "."))
    if st.sidebar.button("Ir a generar presupuesto →", type="primary", use_container_width=True):
        st.switch_page("pages/1_Nuevo_Presupuesto.py")
else:
    st.sidebar.info("Agregá productos con la cantidad para armar un presupuesto.")
