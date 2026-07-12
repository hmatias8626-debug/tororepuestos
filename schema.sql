-- =========================================================
-- TORO REPUESTOS - Schema para Supabase (Postgres)
-- =========================================================

-- ---------- Tabla: productos ----------
create table if not exists productos (
    id              bigserial primary key,
    categoria       text not null,
    codigo          text not null,
    marca           text,               -- marca del repuesto (SKF, CRD, MC, etc.)
    descripcion     text,
    precio          numeric(12, 2) not null default 0,
    stock           integer not null default 0 check (stock >= 0),
    proveedor       text,
    fecha_actualizacion date,
    creado_en       timestamptz not null default now(),
    actualizado_en  timestamptz not null default now()
);

create index if not exists idx_productos_categoria on productos (categoria);
create index if not exists idx_productos_codigo on productos (codigo);

-- ---------- Tabla: marcas_compatibles ----------
-- Relacion producto <-> marca de vehiculo, separada del stock
create table if not exists marcas_compatibles (
    id              bigserial primary key,
    producto_id     bigint not null references productos (id) on delete cascade,
    marca_vehiculo  text not null,
    unique (producto_id, marca_vehiculo)
);

create index if not exists idx_marcas_compat_producto on marcas_compatibles (producto_id);
create index if not exists idx_marcas_compat_marca on marcas_compatibles (marca_vehiculo);

-- ---------- Tabla: presupuestos ----------
create table if not exists presupuestos (
    id              bigserial primary key,
    numero          text not null unique,          -- ej: P-0001
    fecha           date not null default current_date,
    estado          text not null default 'borrador'
                        check (estado in ('borrador', 'confirmado', 'anulado')),
    total           numeric(12, 2) not null default 0,
    creado_en       timestamptz not null default now(),
    actualizado_en  timestamptz not null default now()
);

-- ---------- Tabla: presupuesto_items ----------
create table if not exists presupuesto_items (
    id                  bigserial primary key,
    presupuesto_id      bigint not null references presupuestos (id) on delete cascade,
    producto_id         bigint not null references productos (id),
    cantidad            integer not null check (cantidad > 0),
    precio_unitario     numeric(12, 2) not null,   -- copiado del producto al agregarlo
    subtotal            numeric(12, 2) generated always as (cantidad * precio_unitario) stored
);

create index if not exists idx_items_presupuesto on presupuesto_items (presupuesto_id);

-- ---------- Secuencia para numero de presupuesto ----------
create sequence if not exists presupuesto_numero_seq start 1;

create or replace function siguiente_numero_presupuesto()
returns text as $$
    select 'P-' || lpad(nextval('presupuesto_numero_seq')::text, 5, '0');
$$ language sql;

-- ---------- Funcion: recalcular total del presupuesto ----------
create or replace function recalcular_total_presupuesto(p_id bigint)
returns void as $$
begin
    update presupuestos
    set total = coalesce((select sum(subtotal) from presupuesto_items where presupuesto_id = p_id), 0),
        actualizado_en = now()
    where id = p_id;
end;
$$ language plpgsql;

-- trigger: recalcular total cada vez que cambian los items
create or replace function trg_recalcular_total()
returns trigger as $$
begin
    perform recalcular_total_presupuesto(coalesce(new.presupuesto_id, old.presupuesto_id));
    return null;
end;
$$ language plpgsql;

drop trigger if exists items_recalcular_total on presupuesto_items;
create trigger items_recalcular_total
after insert or update or delete on presupuesto_items
for each row execute function trg_recalcular_total();

-- ---------- Funcion: confirmar presupuesto (descuenta stock) ----------
-- Valida stock suficiente para TODOS los items antes de descontar nada.
create or replace function confirmar_presupuesto(p_id bigint)
returns void as $$
declare
    faltante record;
begin
    if (select estado from presupuestos where id = p_id) != 'borrador' then
        raise exception 'El presupuesto % no esta en estado borrador', p_id;
    end if;

    -- Verificar stock suficiente para cada item
    select pi.producto_id, p.codigo, pi.cantidad, p.stock
    into faltante
    from presupuesto_items pi
    join productos p on p.id = pi.producto_id
    where pi.presupuesto_id = p_id
      and p.stock < pi.cantidad
    limit 1;

    if found then
        raise exception 'Stock insuficiente para el producto % (pedido: %, disponible: %)',
            faltante.codigo, faltante.cantidad, faltante.stock;
    end if;

    -- Descontar stock
    update productos p
    set stock = p.stock - pi.cantidad,
        actualizado_en = now()
    from presupuesto_items pi
    where pi.presupuesto_id = p_id
      and pi.producto_id = p.id;

    update presupuestos
    set estado = 'confirmado', actualizado_en = now()
    where id = p_id;
end;
$$ language plpgsql;

-- ---------- Funcion: anular presupuesto confirmado (devuelve stock) ----------
create or replace function anular_presupuesto(p_id bigint)
returns void as $$
begin
    if (select estado from presupuestos where id = p_id) != 'confirmado' then
        raise exception 'Solo se pueden anular presupuestos confirmados';
    end if;

    update productos p
    set stock = p.stock + pi.cantidad,
        actualizado_en = now()
    from presupuesto_items pi
    where pi.presupuesto_id = p_id
      and pi.producto_id = p.id;

    update presupuestos
    set estado = 'anulado', actualizado_en = now()
    where id = p_id;
end;
$$ language plpgsql;

-- ---------- Row Level Security ----------
-- Habilitado pero con politica abierta para uso interno con la anon key.
-- Si en el futuro hay login de usuarios, conviene restringir esto.
alter table productos enable row level security;
alter table marcas_compatibles enable row level security;
alter table presupuestos enable row level security;
alter table presupuesto_items enable row level security;

create policy "acceso total productos" on productos for all using (true) with check (true);
create policy "acceso total marcas_compatibles" on marcas_compatibles for all using (true) with check (true);
create policy "acceso total presupuestos" on presupuestos for all using (true) with check (true);
create policy "acceso total presupuesto_items" on presupuesto_items for all using (true) with check (true);
