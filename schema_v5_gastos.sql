-- =========================================================
-- TORO REPUESTOS - Schema v5 (gastos generales del negocio)
-- =========================================================
-- No borra nada existente. Gastos independientes de compras a
-- proveedores (alquiler, sueldos, servicios, etc.): solo descripcion,
-- monto y fecha.

create table if not exists toro_gastos (
    id              bigserial primary key,
    descripcion     text not null,
    monto           numeric(12, 2) not null check (monto > 0),
    fecha           date not null default current_date,
    creado_en       timestamptz not null default now()
);

create index if not exists idx_toro_gastos_fecha on toro_gastos (fecha);

alter table toro_gastos enable row level security;
create policy "acceso total toro_gastos" on toro_gastos for all using (true) with check (true);
