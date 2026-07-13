-- =========================================================
-- TORO REPUESTOS - Schema v4 (presupuestos como standby + ventas)
-- =========================================================
-- No borra nada existente. Separa "guardar presupuesto" (borrador, sin
-- tocar stock) de "confirmar" (recien ahi se descuenta stock, se registra
-- fecha efectiva y metodo de pago). Agrega estado 'cancelado' para
-- borradores que el cliente nunca vino a aceptar.

alter table toro_presupuestos add column if not exists fecha_confirmacion date;
alter table toro_presupuestos add column if not exists metodo_pago text
    check (metodo_pago in ('efectivo', 'transferencia', 'tarjeta'));

alter table toro_presupuestos drop constraint if exists toro_presupuestos_estado_check;
alter table toro_presupuestos add constraint toro_presupuestos_estado_check
    check (estado in ('borrador', 'confirmado', 'anulado', 'cancelado'));

-- ---------- Funcion: confirmar presupuesto (ahora exige metodo de pago) ----------
drop function if exists confirmar_presupuesto(bigint);

create or replace function confirmar_presupuesto(p_id bigint, p_metodo_pago text)
returns void as $$
declare
    faltante record;
begin
    if (select estado from toro_presupuestos where id = p_id) != 'borrador' then
        raise exception 'El presupuesto % no esta en estado borrador', p_id;
    end if;

    if p_metodo_pago not in ('efectivo', 'transferencia', 'tarjeta') then
        raise exception 'Metodo de pago invalido: %', p_metodo_pago;
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
    set estado = 'confirmado',
        actualizado_en = now(),
        fecha_confirmacion = current_date,
        metodo_pago = p_metodo_pago
    where id = p_id;
end;
$$ language plpgsql;

-- ---------- Funcion: cancelar un presupuesto que quedo en borrador ----------
create or replace function cancelar_presupuesto(p_id bigint)
returns void as $$
begin
    if (select estado from toro_presupuestos where id = p_id) != 'borrador' then
        raise exception 'Solo se pueden cancelar presupuestos en borrador';
    end if;

    update toro_presupuestos
    set estado = 'cancelado', actualizado_en = now()
    where id = p_id;
end;
$$ language plpgsql;
