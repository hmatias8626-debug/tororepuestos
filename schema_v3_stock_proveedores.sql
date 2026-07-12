-- =========================================================
-- TORO REPUESTOS - Schema v3 (Proveedores, compras, devoluciones/cambios)
-- =========================================================
-- No borra nada existente: solo agrega tablas y funciones nuevas.
-- Ejecutar UNA VEZ sobre la base que ya tiene schema_v2.sql aplicado.

-- ---------- Tabla: toro_proveedores ----------
create table if not exists toro_proveedores (
    id              bigserial primary key,
    nombre          text not null unique,
    contacto        text,
    creado_en       timestamptz not null default now()
);

alter table toro_proveedores enable row level security;
create policy "acceso total toro_proveedores" on toro_proveedores for all using (true) with check (true);

-- ---------- Tabla: toro_compras ----------
-- Cada compra incrementa el stock del producto y genera (o no) deuda con el proveedor.
create table if not exists toro_compras (
    id              bigserial primary key,
    proveedor_id    bigint not null references toro_proveedores (id),
    producto_id     bigint not null references toro_productos (id),
    cantidad        integer not null check (cantidad > 0),
    costo_unitario  numeric(12, 2) not null default 0,
    total           numeric(12, 2) generated always as (cantidad * costo_unitario) stored,
    pagada          boolean not null default false,
    fecha           date not null default current_date,
    creado_en       timestamptz not null default now()
);

create index if not exists idx_toro_compras_proveedor on toro_compras (proveedor_id);
create index if not exists idx_toro_compras_producto on toro_compras (producto_id);
create index if not exists idx_toro_compras_pagada on toro_compras (pagada);

alter table toro_compras enable row level security;
create policy "acceso total toro_compras" on toro_compras for all using (true) with check (true);

-- ---------- Tabla: toro_devoluciones ----------
-- Devoluciones y cambios de productos vendidos, siempre ligados a un presupuesto confirmado.
create table if not exists toro_devoluciones (
    id                  bigserial primary key,
    presupuesto_id      bigint not null references toro_presupuestos (id),
    tipo                text not null check (tipo in ('devolucion', 'cambio')),
    producto_id         bigint not null references toro_productos (id),
    cantidad            integer not null check (cantidad > 0),
    producto_cambio_id  bigint references toro_productos (id),
    cantidad_cambio     integer check (cantidad_cambio > 0),
    fecha               date not null default current_date,
    creado_en           timestamptz not null default now()
);

create index if not exists idx_toro_devoluciones_presupuesto on toro_devoluciones (presupuesto_id);

alter table toro_devoluciones enable row level security;
create policy "acceso total toro_devoluciones" on toro_devoluciones for all using (true) with check (true);

-- ---------- Funcion: ajustar stock (usada por compras y devoluciones simples) ----------
create or replace function ajustar_stock(p_producto_id bigint, p_delta integer)
returns void as $$
begin
    update toro_productos
    set stock = stock + p_delta, actualizado_en = now()
    where id = p_producto_id;
end;
$$ language plpgsql;

-- ---------- Funcion: registrar cambio (devuelve stock del producto viejo, descuenta el nuevo) ----------
create or replace function registrar_cambio(
    p_producto_viejo_id bigint,
    p_cantidad_vieja integer,
    p_producto_nuevo_id bigint,
    p_cantidad_nueva integer
)
returns void as $$
declare
    stock_disponible integer;
begin
    select stock into stock_disponible from toro_productos where id = p_producto_nuevo_id;

    if stock_disponible < p_cantidad_nueva then
        raise exception 'Stock insuficiente para el producto de cambio (disponible: %, pedido: %)',
            stock_disponible, p_cantidad_nueva;
    end if;

    update toro_productos set stock = stock + p_cantidad_vieja, actualizado_en = now() where id = p_producto_viejo_id;
    update toro_productos set stock = stock - p_cantidad_nueva, actualizado_en = now() where id = p_producto_nuevo_id;
end;
$$ language plpgsql;
