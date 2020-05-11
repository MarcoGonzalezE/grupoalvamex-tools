# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class MkOP(models.Model):
    # _name = 'mk.wizard.op'
    _inherit = 'mrp.production'
    _description = 'Funcion Orden de Produccion'


    name = fields.Char()
    product_id = fields.Many2one()
    picking_type_id = fields.Many2one()
    location_src_id = fields.Many2one()
    location_dest_id = fields.Many2one()
    state = fields.Selection()

    orden_producion_costear = fields.Char('Orden de Produccion', compute="_compute_orden")
    state = fields.Selection()
    costeado = fields.Boolean(string="Costeado")
    asig_miscelanea = fields.Boolean(string="Miscelanea Asignada")

    @api.depends('name')
    def _compute_orden(self):
        self.orden_producion_costear = self.name

    def action_op_funtion(self):
        self._sql_report_object_op()
        self._sql_execute_function()
        self.costeado = True


    def _sql_report_object_op(self):
        query_funcion="""CREATE OR REPLACE FUNCTION public.mrp_real_cost(mo character varying)
              RETURNS void AS
                $BODY$
                    DECLARE    
                        _cargos float;
                        _move_id integer;
                        _quant_id integer;
                        _cost numeric;
                        r record;
                        c CURSOR FOR select product_qty,product_id from mrp_production where name = $1;
                    BEGIN  
                        FOR r in c LOOP
                        _cargos := (select sum(debit) from account_move_line where name = $1 and product_id <> r.product_id);
                        _move_id := (select id from stock_move  where origin = $1 and round(product_qty,4) = round(r.product_qty,4) and product_id = r.product_id);
                        _quant_id := (select quant_id  FROM stock_quant_move_rel where move_id = _move_id);
                        _cost = _cargos / r.product_qty;          
                        update stock_quant set cost = _cost where id = _quant_id;
                        update account_move_line set debit = _cargos 
                        where id in (select id from account_move_line  where name = $1 and round(quantity,4) = round(r.product_qty,4) and product_id = r.product_id
                                     and debit <> 0.0);
                        update account_move_line set credit = _cargos 
                        where id in (select id from account_move_line  where name = $1 and round(quantity,4) = round(r.product_qty,4) and product_id = r.product_id
                                     and credit <> 0.0);  
                        END LOOP;
                    END; 
                $BODY$
            LANGUAGE plpgsql VOLATILE
                    """
        self.env.cr.execute(query_funcion)

    def _sql_execute_function(self):
        query = """select  mrp_real_cost(%s)"""
        params = [self.name]
        self.env.cr.execute(query, tuple(params))
        res = self.env.cr.dictfetchall()
        print (res)


    @api.depends('product_id')
    def asignar_misc(self):
        #product = self.env['fabricacion.miscelanea.product.product.rel'].search([('product_product_id','=', self.product_id)])
        if self.state == 'confirmed':
            misc = self.env['fabricacion.miscelanea'].search([('productos','=', self.product_id.id)])
            if misc.id is not False:
                for p in misc:
                    if p.productos == self.product_id:
                        self.picking_type_id = p.ta
                        self.location_src_id = p.mp
                        self.location_dest_id = p.pf
                        self.asig_miscelanea = True
            else:
                raise ValidationError(_(self.product_id.name + ' NO ESTA REGISTRADO EN MISCELANEA'))
        else:
            raise ValidationError(_('La Orden de Produccion se encuentra en proceso, finalizada o cancelada'))

 # Miscelanea Modulo de fabricacion
class FabricacionMiscelanea(models.Model):
    _name = 'fabricacion.miscelanea'
    _inherit = ['mail.thread']

    name = fields.Char(string="Nombre", track_visibility='onchange')
    ta = fields.Many2one('stock.picking.type', string="Tipo de albarán", track_visibility='onchange')
    mp = fields.Many2one('stock.location', string="Ubicación Materias Primas", track_visibility='onchange')
    pf = fields.Many2one('stock.location', string="Ubicación de Productos Finalizados", track_visibility='onchange')
    productos = fields.Many2many('product.product', string="Productos")