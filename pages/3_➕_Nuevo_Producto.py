import streamlit as st
from db import (
    obtener_familias, obtener_marcas_disponibles, obtener_modelos_disponibles,
    crear_producto, agregar_marcas_compatibles, agregar_modelos_compatibles,
)

st.set_page_config(page_title="Nuevo producto", page_icon="➕", layout="wide")
st.title("➕ Cargar producto nuevo")

if "compat_rows" not in st.session_state:
    st.session_state.compat_rows = []  # [{"marca": str, "modelos": [str, ...]}]
if "form_nonce" not in st.session_state:
    st.session_state.form_nonce = 0

n = st.session_state.form_nonce
familias_existentes = obtener_familias()
marcas_vehiculo_existentes = obtener_marcas_disponibles()

st.subheader("Datos del producto")

c1, c2 = st.columns(2)
with c1:
    familia_sel = st.selectbox("Familia", ["+ Nueva familia..."] + familias_existentes, key=f"familia_sel_{n}")
    familia = (
        st.text_input("Nombre de la familia nueva", key=f"familia_nueva_{n}")
        if familia_sel == "+ Nueva familia..." else familia_sel
    )
with c2:
    subfamilia = st.text_input("Subfamilia", placeholder="ej: Correas Poly V, Rótula", key=f"subfamilia_{n}")

c3, c4, c5 = st.columns(3)
with c3:
    codigo = st.text_input("Código *", placeholder="ej: 8PK2205", key=f"codigo_{n}")
with c4:
    marca = st.text_input("Marca del repuesto", placeholder="ej: SKF, CRD, MC", key=f"marca_{n}")
with c5:
    lado = st.selectbox("Lado (solo Tren Delantero)", ["", "D", "I"], key=f"lado_{n}")

tipo = st.text_input("Tipo (solo Tren Delantero)", placeholder="ej: ROTULA, PARRILLA", key=f"tipo_{n}")
descripcion = st.text_area("Descripción", key=f"descripcion_{n}")

c6, c7, c8 = st.columns(3)
with c6:
    precio = st.number_input("Precio *", min_value=0.0, step=100.0, format="%.2f", key=f"precio_{n}")
with c7:
    stock = st.number_input("Stock *", min_value=0, step=1, key=f"stock_{n}")
with c8:
    proveedor = st.text_input("Proveedor", key=f"proveedor_{n}")

st.divider()
st.subheader("Compatibilidad con vehículos (opcional)")

cc1, cc2, cc3 = st.columns([2, 3, 1])
with cc1:
    marca_veh_sel = st.selectbox(
        "Marca de vehículo", ["+ Nueva marca..."] + marcas_vehiculo_existentes, key="compat_marca_sel"
    )
    marca_veh = (
        st.text_input("Nombre de la marca nueva", key="compat_marca_nueva")
        if marca_veh_sel == "+ Nueva marca..." else marca_veh_sel
    )
with cc2:
    modelos_existentes = (
        obtener_modelos_disponibles(marca_veh) if marca_veh_sel != "+ Nueva marca..." and marca_veh else []
    )
    modelos_sel = st.multiselect("Modelos existentes", modelos_existentes, key="compat_modelos_sel")
    modelos_nuevos_str = st.text_input(
        "Modelos nuevos (separados por coma)", placeholder="ej: Clio, Megane", key="compat_modelos_nuevos"
    )
with cc3:
    st.write("")
    st.write("")
    agregar = st.button("+ Agregar", use_container_width=True)

if agregar:
    modelos_nuevos = [m.strip() for m in modelos_nuevos_str.split(",") if m.strip()]
    todos_modelos = sorted(set(modelos_sel) | set(modelos_nuevos))
    if not marca_veh:
        st.warning("Elegí o escribí una marca de vehículo.")
    elif not todos_modelos:
        st.warning("Agregá al menos un modelo (de la lista o escribiendo uno nuevo).")
    else:
        existente = next((r for r in st.session_state.compat_rows if r["marca"] == marca_veh), None)
        if existente:
            existente["modelos"] = sorted(set(existente["modelos"]) | set(todos_modelos))
        else:
            st.session_state.compat_rows.append({"marca": marca_veh, "modelos": todos_modelos})
        for key in ("compat_marca_nueva", "compat_modelos_sel", "compat_modelos_nuevos"):
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

if st.session_state.compat_rows:
    st.write("**Compatibilidad agregada:**")
    for i, row in enumerate(st.session_state.compat_rows):
        rc1, rc2 = st.columns([5, 1])
        rc1.write(f"🚗 **{row['marca']}**: {', '.join(row['modelos'])}")
        if rc2.button("🗑️ Quitar", key=f"quitar_compat_{i}"):
            st.session_state.compat_rows.pop(i)
            st.rerun()
else:
    st.caption("Todavía no agregaste ninguna marca/modelo compatible.")

st.divider()

if st.button("Guardar producto", type="primary", use_container_width=True):
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

            marcas_compat = [row["marca"] for row in st.session_state.compat_rows]
            if marcas_compat:
                agregar_marcas_compatibles(producto_id, marcas_compat)

            entradas_modelos = [
                (row["marca"], modelo)
                for row in st.session_state.compat_rows
                for modelo in row["modelos"]
            ]
            if entradas_modelos:
                agregar_modelos_compatibles(producto_id, entradas_modelos)

            st.session_state.compat_rows = []
            st.session_state.form_nonce += 1
            st.session_state.ultimo_producto_guardado = f"Producto **{codigo}** cargado con id {producto_id}."
            st.rerun()
        except Exception as e:
            st.error(f"No se pudo guardar el producto: {e}")

if "ultimo_producto_guardado" in st.session_state:
    st.success(st.session_state.ultimo_producto_guardado)
    st.balloons()
    del st.session_state["ultimo_producto_guardado"]
