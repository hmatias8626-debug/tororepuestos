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
