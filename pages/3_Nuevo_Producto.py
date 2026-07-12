import streamlit as st
from db import (
    obtener_familias, obtener_subfamilias, obtener_marcas_disponibles,
    crear_producto, agregar_marcas_compatibles, agregar_modelos_compatibles,
)

st.set_page_config(page_title="Nuevo producto", page_icon="➕", layout="wide")
st.title("➕ Cargar producto nuevo")

familias_existentes = obtener_familias()
marcas_vehiculo_existentes = obtener_marcas_disponibles()

with st.form("nuevo_producto", clear_on_submit=True):
    st.subheader("Datos del producto")

    c1, c2 = st.columns(2)
    with c1:
        familia_sel = st.selectbox("Familia", ["+ Nueva familia..."] + familias_existentes)
        familia = st.text_input("Nombre de la familia nueva") if familia_sel == "+ Nueva familia..." else familia_sel
    with c2:
        subfamilia = st.text_input("Subfamilia", placeholder="ej: Correas Poly V, Rótula")

    c3, c4, c5 = st.columns(3)
    with c3:
        codigo = st.text_input("Código *", placeholder="ej: 8PK2205")
    with c4:
        marca = st.text_input("Marca del repuesto", placeholder="ej: SKF, CRD, MC")
    with c5:
        lado = st.selectbox("Lado (solo Tren Delantero)", ["", "D", "I"])

    tipo = st.text_input("Tipo (solo Tren Delantero)", placeholder="ej: ROTULA, PARRILLA")
    descripcion = st.text_area("Descripción")

    c6, c7, c8 = st.columns(3)
    with c6:
        precio = st.number_input("Precio *", min_value=0.0, step=100.0, format="%.2f")
    with c7:
        stock = st.number_input("Stock *", min_value=0, step=1)
    with c8:
        proveedor = st.text_input("Proveedor")

    st.divider()
    st.subheader("Compatibilidad con vehículos (opcional)")

    marcas_input = st.text_input(
        "Marcas de vehículo compatibles (separadas por coma)",
        placeholder="ej: Renault, Fiat, VW",
        help=f"Ya existen: {', '.join(marcas_vehiculo_existentes)}" if marcas_vehiculo_existentes else None,
    )
    modelos_input = st.text_area(
        "Modelos compatibles (una marca por línea, formato: Marca: modelo1, modelo2)",
        placeholder="Renault: Clio, Megane\nFiat: Palio, Uno",
    )

    enviado = st.form_submit_button("Guardar producto", type="primary", use_container_width=True)

if enviado:
    errores = []
    if not familia:
        errores.append("Falta la familia.")
    if not subfamilia:
        errores.append("Falta la subfamilia.")
    if not codigo:
        errores.append("Falta el código.")

    if errores:
        for e in errores:
            st.error(e)
    else:
        try:
            producto = crear_producto(
                familia=familia,
                subfamilia=subfamilia,
                codigo=codigo,
                precio=precio,
                stock=int(stock),
                marca=marca,
                tipo=tipo,
                lado=lado,
                descripcion=descripcion,
                proveedor=proveedor,
            )
            producto_id = producto["id"]

            marcas_compat = [m.strip() for m in marcas_input.split(",") if m.strip()]
            if marcas_compat:
                agregar_marcas_compatibles(producto_id, marcas_compat)

            entradas_modelos = []
            for linea in modelos_input.splitlines():
                if ":" not in linea:
                    continue
                marca_veh, modelos_str = linea.split(":", 1)
                marca_veh = marca_veh.strip()
                for modelo in modelos_str.split(","):
                    modelo = modelo.strip()
                    if marca_veh and modelo:
                        entradas_modelos.append((marca_veh, modelo))
            if entradas_modelos:
                agregar_modelos_compatibles(producto_id, entradas_modelos)

            st.success(f"Producto **{codigo}** cargado con id {producto_id}.")
            st.balloons()
        except Exception as e:
            st.error(f"No se pudo guardar el producto: {e}")
