"""
Carga productos_v2.csv, marcas_compatibles_v2.csv y modelos_compatibles.csv a Supabase.

Requiere la SERVICE_ROLE key (no la anon key) porque hace inserts masivos
saltando RLS. Conseguila en Supabase -> Settings -> API -> service_role.

Uso:
    export SUPABASE_URL="https://tu-proyecto.supabase.co"
    export SUPABASE_SERVICE_KEY="tu-service-role-key"
    python cargar_datos.py
"""
import csv
import os
import sys
from supabase import create_client

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not URL or not KEY:
    print("Falta configurar SUPABASE_URL y SUPABASE_SERVICE_KEY como variables de entorno.")
    sys.exit(1)

client = create_client(URL, KEY)


def cargar_productos(path="productos_v2.csv"):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append({
                "id": int(row["id"]),
                "familia": row["familia"],
                "subfamilia": row["subfamilia"],
                "codigo": row["codigo"],
                "marca": row["marca"] or None,
                "tipo": row["tipo"] or None,
                "lado": row["lado"] or None,
                "descripcion": row["descripcion"] or None,
                "precio": float(row["precio"] or 0),
                "stock": int(row["stock"] or 0),
                "proveedor": row["proveedor"] or None,
                "fecha_actualizacion": row["fecha_actualizacion"] or None,
            })

    for i in range(0, len(rows), 100):
        lote = rows[i:i + 100]
        client.table("toro_productos").insert(lote).execute()
        print(f"  productos: {i + len(lote)}/{len(rows)}")
    print(f"Cargados {len(rows)} productos.")


def cargar_marcas(path="marcas_compatibles_v2.csv"):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [{"producto_id": int(row["producto_id"]), "marca_vehiculo": row["marca_vehiculo"]} for row in reader]

    for i in range(0, len(rows), 100):
        lote = rows[i:i + 100]
        client.table("toro_marcas_compatibles").insert(lote).execute()
        print(f"  marcas_compatibles: {i + len(lote)}/{len(rows)}")
    print(f"Cargadas {len(rows)} marcas compatibles.")


def cargar_modelos(path="modelos_compatibles.csv"):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [
            {"producto_id": int(row["producto_id"]), "marca_vehiculo": row["marca_vehiculo"], "modelo": row["modelo"]}
            for row in reader
        ]

    for i in range(0, len(rows), 100):
        lote = rows[i:i + 100]
        client.table("toro_modelos_compatibles").insert(lote).execute()
        print(f"  modelos_compatibles: {i + len(lote)}/{len(rows)}")
    print(f"Cargados {len(rows)} modelos compatibles.")


if __name__ == "__main__":
    print("Cargando productos...")
    cargar_productos()
    print("Cargando marcas compatibles...")
    cargar_marcas()
    print("Cargando modelos compatibles...")
    cargar_modelos()
    print("Listo.")
