# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class MkOP(models.Model):
    # _name = 'mk.wizard.op'
    _inherit = 'mrp.production'
    _description = 'Funcion Orden de Produccion'


    name = fields.Char()
    orden_producion_costear = fields.Char('Orden de Produccion', compute="_compute_orden")
    state = fields.Selection()
    costeado = fields.Boolean(string="Costeado")
    anulado = fields.Boolean(string="Anulado")

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
                        quant_ids integer;
                        _cost numeric;
                        r record;
                        q record;
                        c CURSOR FOR select product_qty,product_id,origin from mrp_production where name = $1;
                    BEGIN  
                        FOR r in c LOOP
                        _cargos := (select sum(debit) from account_move_line where name = $1 and product_id <> r.product_id);
                        _move_id := (select id from stock_move  where origin = $1 and round(product_qty,4) = round(r.product_qty,4) and product_id = r.product_id);
                        _cost = _cargos / r.product_qty;
                        update product_template 
                        set manufacture_cost = _cost, manufacture_origin = r.origin,last_date_cost = (select CURRENT_DATE) 
                        where id = (select product_tmpl_id from product_product where id = r.product_id);
                        
                        FOR q in select quant_id  FROM stock_quant_move_rel where move_id = _move_id LOOP
                        update stock_quant set cost = _cost where id = q.quant_id;
                        END LOOP;

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

#DESCONTRUCCION
    def action_unbuild(self):        
        unbuild_obj = self.env['mrp.unbuild']
        new_unbuild = unbuild_obj.create({'product_id':self.product_id.id,
            'mo_id':self.id,
            'bom_id':self.bom_id.id,
            'product_qty':self.product_qty,
            'location_id':self.location_dest_id.id,
            'location_dest_id':self.location_src_id.id,
            'product_uom_id':self.product_uom_id.id,
            'state':'done'})
        new_unbuild.action_unbuild()
        new_unbuild.action_unb_funcion()
        self.state = 'cancel'
        self.anulado = True
        self.message_post(body=_("Cancelada por %s") % (new_unbuild.name))