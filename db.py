"""
Conexion a Supabase, compartida por todas las paginas de la app.
Requiere en .streamlit/secrets.toml:

[supabase]
url = "https://xxxx.supabase.co"
key = "tu-anon-key"
"""
import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_client() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


# ---------- Filtros en cascada ----------

def obtener_familias():
    client = get_client()
    result = client.table("toro_productos").select("familia").execute()
    return sorted(set(row["familia"] for row in result.data))


def obtener_subfamilias(familia: str | None = None):
    client = get_client()
    query = client.table("toro_productos").select("subfamilia")
    if familia and familia != "Todas":
        query = query.eq("familia", familia)
    result = query.execute()
    return sorted(set(row["subfamilia"] for row in result.data))


def obtener_marcas_disponibles(familia: str | None = None, subfamilia: str | None = None):
    """Marcas de vehiculo compatibles, acotadas por familia/subfamilia si se especifican."""
    client = get_client()
    if (familia and familia != "Todas") or (subfamilia and subfamilia != "Todas"):
        query = client.table("toro_productos").select("id")
        if familia and familia != "Todas":
            query = query.eq("familia", familia)
        if subfamilia and subfamilia != "Todas":
            query = query.eq("subfamilia", subfamilia)
        ids = [row["id"] for row in query.execute().data]
        if not ids:
            return []
        result = client.table("toro_marcas_compatibles").select("marca_vehiculo").in_("producto_id", ids).execute()
    else:
        result = client.table("toro_marcas_compatibles").select("marca_vehiculo").execute()
    return sorted(set(row["marca_vehiculo"] for row in result.data))


def obtener_modelos_disponibles(marca: str | None = None, familia: str | None = None, subfamilia: str | None = None):
    """Modelos compatibles con la marca elegida, acotados por familia/subfamilia si aplica."""
    client = get_client()
    query = client.table("toro_modelos_compatibles").select("producto_id, marca_vehiculo, modelo")
    if marca and marca != "Todas":
        query = query.eq("marca_vehiculo", marca)
    result = query.execute().data

    if (familia and familia != "Todas") or (subfamilia and subfamilia != "Todas"):
        pquery = client.table("toro_productos").select("id")
        if familia and familia != "Todas":
            pquery = pquery.eq("familia", familia)
        if subfamilia and subfamilia != "Todas":
            pquery = pquery.eq("subfamilia", subfamilia)
        ids_validos = set(row["id"] for row in pquery.execute().data)
        result = [r for r in result if r["producto_id"] in ids_validos]

    return sorted(set(r["modelo"] for r in result))


def buscar_productos(
    texto: str = "",
    familia: str | None = None,
    subfamilia: str | None = None,
    marca_vehiculo: str | None = None,
    modelo: str | None = None,
    limit: int = 100,
):
    client = get_client()

    ids_filtrados = None

    if modelo and modelo != "Todos":
        q = client.table("toro_modelos_compatibles").select("producto_id").eq("modelo", modelo)
        if marca_vehiculo and marca_vehiculo != "Todas":
            q = q.eq("marca_vehiculo", marca_vehiculo)
        rows = q.execute().data
        ids_filtrados = set(r["producto_id"] for r in rows)
    elif marca_vehiculo and marca_vehiculo != "Todas":
        rows = client.table("toro_marcas_compatibles").select("producto_id").eq("marca_vehiculo", marca_vehiculo).execute().data
        ids_filtrados = set(r["producto_id"] for r in rows)

    if ids_filtrados is not None and not ids_filtrados:
        return []

    query = client.table("toro_productos").select("*")
    if ids_filtrados is not None:
        query = query.in_("id", list(ids_filtrados))
    if familia and familia != "Todas":
        query = query.eq("familia", familia)
    if subfamilia and subfamilia != "Todas":
        query = query.eq("subfamilia", subfamilia)
    if texto:
        query = query.or_(f"codigo.ilike.%{texto}%,descripcion.ilike.%{texto}%")

    query = query.order("subfamilia").order("codigo").limit(limit)
    return query.execute().data


# ---------- Alta de productos ----------

def crear_producto(
    familia: str,
    subfamilia: str,
    codigo: str,
    precio: float,
    stock: int,
    marca: str | None = None,
    tipo: str | None = None,
    lado: str | None = None,
    descripcion: str | None = None,
    proveedor: str | None = None,
):
    client = get_client()
    result = client.table("toro_productos").insert({
        "familia": familia,
        "subfamilia": subfamilia,
        "codigo": codigo,
        "marca": marca or None,
        "tipo": tipo or None,
        "lado": lado or None,
        "descripcion": descripcion or None,
        "precio": precio,
        "stock": stock,
        "proveedor": proveedor or None,
    }).execute()
    return result.data[0]


def agregar_marcas_compatibles(producto_id: int, marcas_vehiculo: list[str]):
    client = get_client()
    rows = [{"producto_id": producto_id, "marca_vehiculo": m} for m in marcas_vehiculo]
    if rows:
        client.table("toro_marcas_compatibles").insert(rows).execute()


def agregar_modelos_compatibles(producto_id: int, entradas: list[tuple[str, str]]):
    """entradas: lista de tuplas (marca_vehiculo, modelo)."""
    client = get_client()
    rows = [{"producto_id": producto_id, "marca_vehiculo": m, "modelo": mod} for m, mod in entradas]
    if rows:
        client.table("toro_modelos_compatibles").insert(rows).execute()


# ---------- Presupuestos ----------

def crear_presupuesto():
    client = get_client()
    numero = client.rpc("siguiente_numero_presupuesto").execute().data
    result = client.table("toro_presupuestos").insert({"numero": numero}).execute()
    return result.data[0]


def agregar_item(presupuesto_id: int, producto_id: int, cantidad: int, precio_unitario: float):
    client = get_client()
    client.table("toro_presupuesto_items").insert({
        "presupuesto_id": presupuesto_id,
        "producto_id": producto_id,
        "cantidad": cantidad,
        "precio_unitario": precio_unitario,
    }).execute()


def eliminar_item(item_id: int):
    client = get_client()
    client.table("toro_presupuesto_items").delete().eq("id", item_id).execute()


def obtener_items(presupuesto_id: int):
    client = get_client()
    result = (
        client.table("toro_presupuesto_items")
        .select("*, productos:toro_productos(codigo, descripcion, subfamilia)")
        .eq("presupuesto_id", presupuesto_id)
        .execute()
    )
    return result.data


def obtener_presupuesto(presupuesto_id: int):
    client = get_client()
    result = client.table("toro_presupuestos").select("*").eq("id", presupuesto_id).single().execute()
    return result.data


def confirmar_presupuesto(presupuesto_id: int):
    client = get_client()
    client.rpc("confirmar_presupuesto", {"p_id": presupuesto_id}).execute()


def anular_presupuesto(presupuesto_id: int):
    client = get_client()
    client.rpc("anular_presupuesto", {"p_id": presupuesto_id}).execute()


def listar_presupuestos(estado: str | None = None, limit: int = 100):
    client = get_client()
    query = client.table("toro_presupuestos").select("*").order("id", desc=True).limit(limit)
    if estado and estado != "Todos":
        query = query.eq("estado", estado)
    return query.execute().data


# ---------- Control de stock ----------

def obtener_productos_stock():
    client = get_client()
    result = (
        client.table("toro_productos")
        .select("id, familia, subfamilia, codigo, descripcion, precio, stock")
        .order("familia")
        .order("codigo")
        .execute()
    )
    return result.data


def actualizar_precio_stock(producto_id: int, precio: float, stock: int):
    client = get_client()
    client.table("toro_productos").update({"precio": precio, "stock": stock}).eq("id", producto_id).execute()


# ---------- Proveedores y compras ----------

def obtener_proveedores():
    client = get_client()
    result = client.table("toro_proveedores").select("*").order("nombre").execute()
    return result.data


def crear_proveedor(nombre: str, contacto: str | None = None):
    client = get_client()
    result = client.table("toro_proveedores").insert({"nombre": nombre, "contacto": contacto or None}).execute()
    return result.data[0]


def registrar_compra(proveedor_id: int, producto_id: int, cantidad: int, costo_unitario: float, pagada: bool = False):
    client = get_client()
    result = client.table("toro_compras").insert({
        "proveedor_id": proveedor_id,
        "producto_id": producto_id,
        "cantidad": cantidad,
        "costo_unitario": costo_unitario,
        "pagada": pagada,
    }).execute()
    client.rpc("ajustar_stock", {"p_producto_id": producto_id, "p_delta": cantidad}).execute()
    return result.data[0]


def obtener_compras(proveedor_id: int | None = None, solo_pendientes: bool = False, limit: int = 200):
    client = get_client()
    query = (
        client.table("toro_compras")
        .select("*, productos:toro_productos(codigo, descripcion), proveedores:toro_proveedores(nombre)")
        .order("id", desc=True)
        .limit(limit)
    )
    if proveedor_id:
        query = query.eq("proveedor_id", proveedor_id)
    if solo_pendientes:
        query = query.eq("pagada", False)
    return query.execute().data


def marcar_compra_pagada(compra_id: int):
    client = get_client()
    client.table("toro_compras").update({"pagada": True}).eq("id", compra_id).execute()


def obtener_deuda_por_proveedor():
    """Total adeudado (compras no pagadas) agrupado por proveedor."""
    client = get_client()
    proveedores = {p["id"]: p["nombre"] for p in obtener_proveedores()}
    pendientes = client.table("toro_compras").select("proveedor_id, total").eq("pagada", False).execute().data

    deuda = {pid: 0.0 for pid in proveedores}
    for row in pendientes:
        deuda[row["proveedor_id"]] = deuda.get(row["proveedor_id"], 0.0) + float(row["total"])

    return [{"proveedor_id": pid, "nombre": nombre, "deuda": deuda.get(pid, 0.0)} for pid, nombre in proveedores.items()]


# ---------- Devoluciones y cambios ----------

def registrar_devolucion(presupuesto_id: int, producto_id: int, cantidad: int):
    client = get_client()
    result = client.table("toro_devoluciones").insert({
        "presupuesto_id": presupuesto_id,
        "tipo": "devolucion",
        "producto_id": producto_id,
        "cantidad": cantidad,
    }).execute()
    client.rpc("ajustar_stock", {"p_producto_id": producto_id, "p_delta": cantidad}).execute()
    return result.data[0]


def registrar_cambio(
    presupuesto_id: int,
    producto_id: int,
    cantidad: int,
    producto_cambio_id: int,
    cantidad_cambio: int,
):
    client = get_client()
    client.rpc("registrar_cambio", {
        "p_producto_viejo_id": producto_id,
        "p_cantidad_vieja": cantidad,
        "p_producto_nuevo_id": producto_cambio_id,
        "p_cantidad_nueva": cantidad_cambio,
    }).execute()
    result = client.table("toro_devoluciones").insert({
        "presupuesto_id": presupuesto_id,
        "tipo": "cambio",
        "producto_id": producto_id,
        "cantidad": cantidad,
        "producto_cambio_id": producto_cambio_id,
        "cantidad_cambio": cantidad_cambio,
    }).execute()
    return result.data[0]


def obtener_devoluciones(presupuesto_id: int):
    client = get_client()
    result = (
        client.table("toro_devoluciones")
        .select("*, producto:toro_productos!toro_devoluciones_producto_id_fkey(codigo, descripcion), producto_cambio:toro_productos!toro_devoluciones_producto_cambio_id_fkey(codigo, descripcion)")
        .eq("presupuesto_id", presupuesto_id)
        .order("id", desc=True)
        .execute()
    )
    return result.data
