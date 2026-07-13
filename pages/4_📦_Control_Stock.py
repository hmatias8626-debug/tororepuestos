import pandas as pd
import streamlit as st
from db import obtener_productos_stock, actualizar_precio_stock

st.set_page_config(page_title="Control de stock", page_icon="📦", layout="wide")
st.title("📦 Control de stock")

productos = obtener_productos_stock()
df = pd.DataFrame(productos)

if df.empty:
    st.info("No hay productos cargados todavía.")
    st.stop()

df["valorizado"] = df["precio"] * df["stock"]

st.metric("Valorizado total (a precio de venta)", f"${df['valorizado'].sum():,.0f}".replace(",", "."))

st.subheader("Valorizado por familia")
resumen = (
    df.groupby("familia")
    .agg(productos=("id", "count"), stock_total=("stock", "sum"), valorizado=("valorizado", "sum"))
    .reset_index()
    .sort_values("valorizado", ascending=False)
)
st.dataframe(
    resumen,
    use_container_width=True,
    hide_index=True,
    column_config={
        "familia": "Familia",
        "productos": st.column_config.NumberColumn("Productos"),
        "stock_total": st.column_config.NumberColumn("Stock total"),
        "valorizado": st.column_config.NumberColumn("Valorizado", format="$ %.0f"),
    },
)

st.divider()
st.subheader("Detalle de productos (editable)")
st.caption("Modificá precio o stock directamente en la tabla y presioná \"Guardar cambios\".")

familias = ["Todas"] + sorted(df["familia"].unique().tolist())
familia_filtro = st.selectbox("Filtrar por familia", familias)
df_vista = df if familia_filtro == "Todas" else df[df["familia"] == familia_filtro]

columnas = ["id", "familia", "subfamilia", "codigo", "descripcion", "precio", "stock"]
editado = st.data_editor(
    df_vista[columnas],
    use_container_width=True,
    hide_index=True,
    disabled=["id", "familia", "subfamilia", "codigo", "descripcion"],
    column_config={
        "id": st.column_config.NumberColumn("ID"),
        "familia": "Familia",
        "subfamilia": "Subfamilia",
        "codigo": "Código",
        "descripcion": "Descripción",
        "precio": st.column_config.NumberColumn("Precio", format="$ %.2f", min_value=0.0),
        "stock": st.column_config.NumberColumn("Stock", min_value=0, step=1),
    },
    key="editor_stock",
)

if st.button("Guardar cambios", type="primary"):
    original_por_id = df_vista.set_index("id")[["precio", "stock"]].to_dict("index")
    cambios = 0
    for _, fila in editado.iterrows():
        original = original_por_id.get(fila["id"])
        if original and (float(fila["precio"]) != float(original["precio"]) or int(fila["stock"]) != int(original["stock"])):
            actualizar_precio_stock(int(fila["id"]), float(fila["precio"]), int(fila["stock"]))
            cambios += 1

    if cambios:
        st.success(f"Se actualizaron {cambios} producto(s).")
        st.rerun()
    else:
        st.info("No hay cambios para guardar.")
