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


def buscar_productos(texto: str = "", categoria: str | None = None, marca_vehiculo: str | None = None, limit: int = 100):
    """Busca productos por codigo/descripcion, opcionalmente filtrado por categoria y marca de vehiculo."""
    client = get_client()

    if marca_vehiculo and marca_vehiculo != "Todas":
        # primero resolvemos los producto_id compatibles con esa marca
        compat = (
            client.table("marcas_compatibles")
            .select("producto_id")
            .eq("marca_vehiculo", marca_vehiculo)
            .execute()
        )
        ids = [row["producto_id"] for row in compat.data]
        if not ids:
            return []
        query = client.table("productos").select("*").in_("id", ids)
    else:
        query = client.table("productos").select("*")

    if categoria and categoria != "Todas":
        query = query.eq("categoria", categoria)

    if texto:
        # busca coincidencia en codigo o descripcion (OR)
        query = query.or_(f"codigo.ilike.%{texto}%,descripcion.ilike.%{texto}%")

    query = query.order("categoria").order("codigo").limit(limit)
    result = query.execute()
    return result.data


def obtener_categorias():
    client = get_client()
    result = client.table("productos").select("categoria").execute()
    return sorted(set(row["categoria"] for row in result.data))


def obtener_marcas_vehiculo():
    client = get_client()
    result = client.table("marcas_compatibles").select("marca_vehiculo").execute()
    return sorted(set(row["marca_vehiculo"] for row in result.data))


def crear_presupuesto():
    client = get_client()
    numero = client.rpc("siguiente_numero_presupuesto").execute().data
    result = client.table("presupuestos").insert({"numero": numero}).execute()
    return result.data[0]


def agregar_item(presupuesto_id: int, producto_id: int, cantidad: int, precio_unitario: float):
    client = get_client()
    client.table("presupuesto_items").insert({
        "presupuesto_id": presupuesto_id,
        "producto_id": producto_id,
        "cantidad": cantidad,
        "precio_unitario": precio_unitario,
    }).execute()


def eliminar_item(item_id: int):
    client = get_client()
    client.table("presupuesto_items").delete().eq("id", item_id).execute()


def obtener_items(presupuesto_id: int):
    client = get_client()
    result = (
        client.table("presupuesto_items")
        .select("*, productos(codigo, descripcion, categoria)")
        .eq("presupuesto_id", presupuesto_id)
        .execute()
    )
    return result.data


def obtener_presupuesto(presupuesto_id: int):
    client = get_client()
    result = client.table("presupuestos").select("*").eq("id", presupuesto_id).single().execute()
    return result.data


def confirmar_presupuesto(presupuesto_id: int):
    client = get_client()
    client.rpc("confirmar_presupuesto", {"p_id": presupuesto_id}).execute()


def anular_presupuesto(presupuesto_id: int):
    client = get_client()
    client.rpc("anular_presupuesto", {"p_id": presupuesto_id}).execute()


def listar_presupuestos(estado: str | None = None, limit: int = 100):
    client = get_client()
    query = client.table("presupuestos").select("*").order("id", desc=True).limit(limit)
    if estado and estado != "Todos":
        query = query.eq("estado", estado)
    return query.execute().data
