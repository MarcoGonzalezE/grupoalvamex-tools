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








