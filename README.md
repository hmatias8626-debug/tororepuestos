# TORO REPUESTOS — Sistema de presupuestos con control de stock

## 1. Crear el proyecto en Supabase

1. Andá a https://supabase.com y creá un proyecto nuevo (gratis).
2. En el panel del proyecto, andá a **SQL Editor** → **New query**.
3. Pegá todo el contenido de `schema.sql` y ejecutalo. Esto crea las tablas,
   funciones y triggers necesarios.

## 2. Cargar los datos del catálogo

Tenés dos formas, elegí la que te resulte más cómoda:

### Opción A — Import CSV desde el dashboard (más simple)
1. En Supabase, andá a **Table Editor** → tabla `productos` → botón **Insert** → **Import data from CSV**.
   Subí `productos.csv`. Los IDs ya vienen numerados del 1 al 483, coincidiendo
   con la secuencia — revisá que la tabla tenga `id` como serial y que el import
   no falle por conflicto de secuencia (si falla, importá sin la columna `id`
   y dejá que Supabase autogenere).
2. Repetí lo mismo con la tabla `marcas_compatibles` usando `marcas_compatibles.csv`.
   Ojo: esta tabla depende de los IDs de `productos`, así que cargala **después**.

### Opción B — Script Python (más prolijo, recomendado si vas a repetir el proceso)
Ver `cargar_datos.py` — usa las credenciales de servicio (service_role key, no
la anon key) para insertar todo de una.

## 3. Configurar la app localmente

```bash
cd toro_repuestos_app
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Editá .streamlit/secrets.toml con la URL y anon key de tu proyecto
# (Supabase → Settings → API)
streamlit run app.py
```

## 4. Estructura de la app

- `app.py` — catálogo con buscador, filtros por categoría/marca de vehículo,
  y selector de cantidades (arma un carrito en `st.session_state`)
- `pages/1_Nuevo_Presupuesto.py` — revisa el carrito, valida stock, confirma
  el presupuesto (esto descuenta stock automáticamente vía la función SQL
  `confirmar_presupuesto`)
- `pages/2_Historial.py` — lista presupuestos anteriores, permite anular uno
  confirmado (devuelve el stock)
- `db.py` — todas las consultas a Supabase en un solo lugar

## 5. Qué falta / próximos pasos sugeridos

- **Exportar presupuesto a PDF/imagen** para mandar por WhatsApp — se puede
  sumar con `reportlab` o generando una imagen con Pillow.
- **Autenticación** — hoy cualquiera con el link accede. Si tu cuñado quiere
  restringir el acceso (por ejemplo, a sus empleados), conviene sumar
  `streamlit-authenticator` o el auth nativo de Supabase.
- **Alertas de stock bajo** — ya está el campo de stock, se puede agregar
  una vista de "productos con stock ≤ X" fácilmente.
- **Historial de precios** — hoy al actualizar el precio de un producto se
  pierde el anterior; si eso importa, se puede armar una tabla
  `historial_precios`.

## 6. Sobre los 10 productos "a revisar"

En el Excel consolidado (`TORO_REPUESTOS_consolidado.xlsx`, hoja `a_revisar`)
quedaron 10 productos sin marca de vehículo clara (algunos con descripción
vacía en el Excel original, otros genéricos como "universal" o "tractor").
Conviene que tu cuñado los complete antes o después de cargar los datos —
no bloquean el resto del sistema.
