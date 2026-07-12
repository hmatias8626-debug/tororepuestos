# TORO REPUESTOS — Sistema de presupuestos con control de stock

## ⚠️ Actualización: esquema v2 (Familia/Subfamilia + filtro por Modelo)

Si ya habías cargado el esquema anterior (schema.sql, tablas `productos`/`marcas_compatibles`
con columna `categoria`), este es un **reemplazo completo**: `schema_v2.sql` borra esas
tablas y las recrea con la nueva estructura. Volvé a cargar los datos desde cero con los
CSV v2 (`productos_v2.csv`, `marcas_compatibles_v2.csv`, `modelos_compatibles.csv`).

## 1. Crear/actualizar el proyecto en Supabase

1. Andá a https://supabase.com y creá un proyecto (o usá el existente).
2. **SQL Editor** → **New query** → pegá todo `schema_v2.sql` y ejecutalo.
   Esto crea las tablas `productos` (con `familia`/`subfamilia` en vez de `categoria`),
   `marcas_compatibles`, `modelos_compatibles`, `presupuestos` y `presupuesto_items`.

## 2. Cargar los datos del catálogo

### Opción A — Import CSV desde el dashboard
Orden importante (las tablas de compatibilidad dependen de los IDs de `productos`):
1. Tabla `productos` → Insert → Import CSV → `productos_v2.csv`
2. Tabla `marcas_compatibles` → Import CSV → `marcas_compatibles_v2.csv`
3. Tabla `modelos_compatibles` → Import CSV → `modelos_compatibles.csv`

### Opción B — Script Python
```bash
export SUPABASE_URL="https://tu-proyecto.supabase.co"
export SUPABASE_SERVICE_KEY="tu-service-role-key"
python cargar_datos.py
```

## 3. Configurar la app localmente

```bash
cd toro_repuestos_app
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Editá .streamlit/secrets.toml con la URL y key de tu proyecto
streamlit run app.py
```

## 4. Cómo funciona el catálogo ahora

Filtros en cascada: **Familia → Subfamilia → Marca de vehículo → Modelo**.

- **Familia**: agrupación amplia (Correas, Frenos, Encendido, Transmisión,
  Refrigeración, Rodamientos, Filtros, Tren Delantero)
- **Subfamilia**: más específico. Para Correas se separa en Correas Poly V /
  Correas de Distribución / Kit de Distribución. Para Filtros y Tren Delantero,
  la subfamilia sale directo del tipo de pieza (Aire, Aceite, Combustible /
  Rótula, Parrilla, Extremo, etc.)
- **Marca de vehículo**: Renault, Fiat, VW, etc. — se acota según lo que ya
  elegiste en Familia/Subfamilia
- **Modelo**: Clio, Gol, Corsa, etc. — se acota según la marca elegida

A medida que elegís productos con cantidad, se arma en vivo un panel tipo
comprobante de presupuesto a la derecha, con el mismo formato del papel que
usa tu cuñado hoy (detalle / precio unitario / importe / total).

## 5. Estructura de la app

- `app.py` — catálogo con filtros en cascada + panel de presupuesto en vivo
- `pages/1_Nuevo_Presupuesto.py` — revisa el carrito, valida stock, confirma
  el presupuesto (descuenta stock vía la función SQL `confirmar_presupuesto`)
- `pages/2_Historial.py` — presupuestos anteriores, permite anular (devuelve stock)
- `db.py` — todas las consultas a Supabase en un solo lugar

## 6. Qué falta / próximos pasos sugeridos

- **Exportar presupuesto a PDF/imagen** para mandar por WhatsApp
- **Autenticación** — hoy cualquiera con el link accede
- **Alertas de stock bajo**
- **Historial de precios**

## 7. Sobre los 10 productos "a revisar"

Ver `a_revisar_v3.json` (o la hoja `a_revisar` del Excel consolidado que ya
tenés): 10 productos sin marca/modelo de vehículo clara — 7 con descripción
vacía en el Excel original, 2 genéricos ("universal"/"tractor"), y 1 caso
mixto donde ya se resolvió automáticamente el modelo principal. No bloquean
el resto del sistema.

## 8. Sobre la calidad de los datos de "modelo"

Los ~450 modelos distintos se extrajeron automáticamente separando las
descripciones del Excel original. Es un proceso heurístico: la gran mayoría
quedó bien (Clio, Gol, Corsa, Fiesta, etc.), pero puede haber algún error de
tipeo heredado del Excel (ej. "Parnet" en vez de "Partner") o algún modelo
mal segmentado. Si tu cuñado nota algo raro buscando, avisame el código del
producto y lo corregimos puntualmente.

