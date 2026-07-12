import streamlit as st
from db import (
    obtener_productos_stock, obtener_producto, actualizar_producto,
    obtener_marcas_compatibles_producto, obtener_modelos_compatibles_producto,
    eliminar_marca_compatible, eliminar_modelo_compatible,
    agregar_marcas_compatibles, agregar_modelos_compatibles,
)

st.set_page_config(page_title="Editar producto", page_icon="✏️", layout="wide")
st.title("✏️ Editar producto")

if "edit_nonce" not in st.session_state:
    st.session_state.edit_nonce = 0
n = st.session_state.edit_nonce

productos = obtener_productos_stock()
if not productos:
    st.info("Todavía no hay productos cargados.")
    st.stop()

opciones = {f"{p['codigo']} — {p['descripcion'] or ''}": p["id"] for p in productos}
seleccion = st.selectbox("Buscar producto (por código o descripción)", list(opciones.keys()), key=f"edit_sel_{n}")
producto_id = opciones[seleccion]
producto = obtener_producto(producto_id)

st.divider()
st.subheader("Datos del producto")

c1, c2 = st.columns(2)
with c1:
    familia = st.text_input("Familia", value=producto["familia"], key=f"edit_familia_{producto_id}_{n}")
with c2:
    subfamilia = st.text_input("Subfamilia", value=producto["subfamilia"], key=f"edit_subfamilia_{producto_id}_{n}")

c3, c4, c5 = st.columns(3)
with c3:
    codigo = st.text_input("Código", value=producto["codigo"], key=f"edit_codigo_{producto_id}_{n}")
with c4:
    marca = st.text_input("Marca del repuesto", value=producto["marca"] or "", key=f"edit_marca_{producto_id}_{n}")
with c5:
    lado_opciones = ["", "D", "I"]
    lado_actual = producto["lado"] or ""
    lado = st.selectbox(
        "Lado (solo Tren Delantero)", lado_opciones,
        index=lado_opciones.index(lado_actual) if lado_actual in lado_opciones else 0,
        key=f"edit_lado_{producto_id}_{n}",
    )

tipo = st.text_input("Tipo (solo Tren Delantero)", value=producto["tipo"] or "", key=f"edit_tipo_{producto_id}_{n}")
descripcion = st.text_area("Descripción", value=producto["descripcion"] or "", key=f"edit_descripcion_{producto_id}_{n}")

c6, c7, c8 = st.columns(3)
with c6:
    precio = st.number_input(
        "Precio", min_value=0.0, step=100.0, format="%.2f", value=float(producto["precio"]), key=f"edit_precio_{producto_id}_{n}"
    )
with c7:
    stock = st.number_input("Stock", min_value=0, step=1, value=int(producto["stock"]), key=f"edit_stock_{producto_id}_{n}")
with c8:
    proveedor = st.text_input("Proveedor", value=producto["proveedor"] or "", key=f"edit_proveedor_{producto_id}_{n}")

if st.button("Guardar cambios del producto", type="primary"):
    if not codigo or not familia or not subfamilia:
        st.error("Familia, subfamilia y código son obligatorios.")
    else:
        actualizar_producto(
            producto_id,
            familia=familia,
            subfamilia=subfamilia,
            codigo=codigo,
            marca=marca or None,
            tipo=tipo or None,
            lado=lado or None,
            descripcion=descripcion or None,
            precio=float(precio),
            stock=int(stock),
            proveedor=proveedor or None,
        )
        st.success("Datos del producto actualizados.")
        st.rerun()

st.divider()
st.subheader("Marcas y modelos de vehículo compatibles")

marcas_actuales = obtener_marcas_compatibles_producto(producto_id)
modelos_actuales = obtener_modelos_compatibles_producto(producto_id)

col_marcas, col_modelos = st.columns(2)

with col_marcas:
    st.write("**Marcas compatibles**")
    if not marcas_actuales:
        st.caption("Sin marcas cargadas.")
    for m in marcas_actuales:
        mc1, mc2 = st.columns([4, 1])
        mc1.write(m["marca_vehiculo"])
        if mc2.button("🗑️", key=f"quitar_marca_{m['id']}_{n}"):
            eliminar_marca_compatible(m["id"])
            st.rerun()

    nueva_marca = st.text_input("Agregar marca nueva", key=f"nueva_marca_{producto_id}_{n}")
    if st.button("+ Agregar marca", key=f"btn_marca_{producto_id}_{n}"):
        if nueva_marca:
            try:
                agregar_marcas_compatibles(producto_id, [nueva_marca])
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo agregar: {e}")
        else:
            st.warning("Escribí una marca.")

with col_modelos:
    st.write("**Modelos compatibles**")
    if not modelos_actuales:
        st.caption("Sin modelos cargados.")
    for mo in modelos_actuales:
        mo1, mo2 = st.columns([4, 1])
        mo1.write(f"{mo['marca_vehiculo']}: {mo['modelo']}")
        if mo2.button("🗑️", key=f"quitar_modelo_{mo['id']}_{n}"):
            eliminar_modelo_compatible(mo["id"])
            st.rerun()

    marcas_disponibles = sorted(set(m["marca_vehiculo"] for m in marcas_actuales))
    if marcas_disponibles:
        marca_para_modelo = st.selectbox("Marca", marcas_disponibles, key=f"marca_para_modelo_{producto_id}_{n}")
    else:
        marca_para_modelo = st.text_input(
            "Marca (agregá una marca compatible primero, o escribila acá)",
            key=f"marca_para_modelo_txt_{producto_id}_{n}",
        )
    nuevo_modelo = st.text_input("Agregar modelo nuevo", key=f"nuevo_modelo_{producto_id}_{n}")
    if st.button("+ Agregar modelo", key=f"btn_modelo_{producto_id}_{n}"):
        if marca_para_modelo and nuevo_modelo:
            try:
                agregar_modelos_compatibles(producto_id, [(marca_para_modelo, nuevo_modelo)])
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo agregar: {e}")
        else:
            st.warning("Completá marca y modelo.")
