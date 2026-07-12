-- =========================================================
-- TORO REPUESTOS - Schema v2 (Familia/Subfamilia + Modelos)
-- =========================================================
-- Si ya corriste el schema.sql original, ejecuta esto en un
-- proyecto NUEVO de Supabase (o borra las tablas viejas antes).
-- Tablas prefijadas con toro_ porque este proyecto es compartido
-- con otras apps (namnam_*, mipol_*, etc.).

drop table if exists toro_presupuesto_items cascade;
drop table if exists toro_presupuestos cascade;
drop table if exists toro_modelos_compatibles cascade;
drop table if exists toro_marcas_compatibles cascade;
drop table if exists toro_productos cascade;

-- ---------- Tabla: toro_productos ----------
create table toro_productos (
    id              bigserial primary key,
    familia         text not null,
    subfamilia      text not null,
    codigo          text not null,
    marca           text,               -- marca del repuesto (SKF, CRD, MC, etc.)
    tipo            text,               -- solo Tren Delantero (ROTULA, PARRILLA, etc.)
    lado            text,               -- solo Tren Delantero (D/I)
    descripcion     text,
    precio          numeric(12, 2) not null default 0,
    stock           integer not null default 0 check (stock >= 0),
    proveedor       text,
    fecha_actualizacion date,
    creado_en       timestamptz not null default now(),
    actualizado_en  timestamptz not null default now()
);

create index idx_toro_productos_familia on toro_productos (familia);
create index idx_toro_productos_subfamilia on toro_productos (subfamilia);
create index idx_toro_productos_codigo on toro_productos (codigo);

-- ---------- Tabla: toro_marcas_compatibles ----------
create table toro_marcas_compatibles (
    id              bigserial primary key,
    producto_id     bigint not null references toro_productos (id) on delete cascade,
    marca_vehiculo  text not null,
    unique (producto_id, marca_vehiculo)
);

create index idx_toro_marcas_compat_producto on toro_marcas_compatibles (producto_id);
create index idx_toro_marcas_compat_marca on toro_marcas_compatibles (marca_vehiculo);

-- ---------- Tabla: toro_modelos_compatibles ----------
create table toro_modelos_compatibles (
    id              bigserial primary key,
    producto_id     bigint not null references toro_productos (id) on delete cascade,
    marca_vehiculo  text not null,
    modelo          text not null
);

create index idx_toro_modelos_compat_producto on toro_modelos_compatibles (producto_id);
create index idx_toro_modelos_compat_marca_modelo on toro_modelos_compatibles (marca_vehiculo, modelo);

-- ---------- Tabla: toro_presupuestos ----------
create table toro_presupuestos (
    id              bigserial primary key,
    numero          text not null unique,
    fecha           date not null default current_date,
    estado          text not null default 'borrador'
                        check (estado in ('borrador', 'confirmado', 'anulado')),
    total           numeric(12, 2) not null default 0,
    creado_en       timestamptz not null default now(),
    actualizado_en  timestamptz not null default now()
);

-- ---------- Tabla: toro_presupuesto_items ----------
create table toro_presupuesto_items (
    id                  bigserial primary key,
    presupuesto_id      bigint not null references toro_presupuestos (id) on delete cascade,
    producto_id         bigint not null references toro_productos (id),
    cantidad            integer not null check (cantidad > 0),
    precio_unitario     numeric(12, 2) not null,
    subtotal            numeric(12, 2) generated always as (cantidad * precio_unitario) stored
);

create index idx_toro_items_presupuesto on toro_presupuesto_items (presupuesto_id);

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
    update toro_presupuestos
    set total = coalesce((select sum(subtotal) from toro_presupuesto_items where presupuesto_id = p_id), 0),
        actualizado_en = now()
    where id = p_id;
end;
$$ language plpgsql;

create or replace function trg_recalcular_total()
returns trigger as $$
begin
    perform recalcular_total_presupuesto(coalesce(new.presupuesto_id, old.presupuesto_id));
    return null;
end;
$$ language plpgsql;

drop trigger if exists items_recalcular_total on toro_presupuesto_items;
create trigger items_recalcular_total
after insert or update or delete on toro_presupuesto_items
for each row execute function trg_recalcular_total();

-- ---------- Funcion: confirmar presupuesto (descuenta stock) ----------
create or replace function confirmar_presupuesto(p_id bigint)
returns void as $$
declare
    faltante record;
begin
    if (select estado from toro_presupuestos where id = p_id) != 'borrador' then
        raise exception 'El presupuesto % no esta en estado borrador', p_id;
    end if;

    select pi.producto_id, p.codigo, pi.cantidad, p.stock
    into faltante
    from toro_presupuesto_items pi
    join toro_productos p on p.id = pi.producto_id
    where pi.presupuesto_id = p_id
      and p.stock < pi.cantidad
    limit 1;

    if found then
        raise exception 'Stock insuficiente para el producto % (pedido: %, disponible: %)',
            faltante.codigo, faltante.cantidad, faltante.stock;
    end if;

    update toro_productos p
    set stock = p.stock - pi.cantidad,
        actualizado_en = now()
    from toro_presupuesto_items pi
    where pi.presupuesto_id = p_id
      and pi.producto_id = p.id;

    update toro_presupuestos
    set estado = 'confirmado', actualizado_en = now()
    where id = p_id;
end;
$$ language plpgsql;

-- ---------- Funcion: anular presupuesto confirmado (devuelve stock) ----------
create or replace function anular_presupuesto(p_id bigint)
returns void as $$
begin
    if (select estado from toro_presupuestos where id = p_id) != 'confirmado' then
        raise exception 'Solo se pueden anular presupuestos confirmados';
    end if;

    update toro_productos p
    set stock = p.stock + pi.cantidad,
        actualizado_en = now()
    from toro_presupuesto_items pi
    where pi.presupuesto_id = p_id
      and pi.producto_id = p.id;

    update toro_presupuestos
    set estado = 'anulado', actualizado_en = now()
    where id = p_id;
end;
$$ language plpgsql;

-- ---------- Row Level Security ----------
alter table toro_productos enable row level security;
alter table toro_marcas_compatibles enable row level security;
alter table toro_modelos_compatibles enable row level security;
alter table toro_presupuestos enable row level security;
alter table toro_presupuesto_items enable row level security;

create policy "acceso total toro_productos" on toro_productos for all using (true) with check (true);
create policy "acceso total toro_marcas_compatibles" on toro_marcas_compatibles for all using (true) with check (true);
create policy "acceso total toro_modelos_compatibles" on toro_modelos_compatibles for all using (true) with check (true);
create policy "acceso total toro_presupuestos" on toro_presupuestos for all using (true) with check (true);
create policy "acceso total toro_presupuesto_items" on toro_presupuesto_items for all using (true) with check (true);
