# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

class MkUnb(models.Model):
	_inherit = "mrp.unbuild"
	_description = 'Funcion Orden de Descontruccion'

	state = fields.Selection()
	name = fields.Char()
	anulado = fields.Boolean(string="Anulado")

	def action_unb_funcion(self):
		self._sql_report_object_unb()
		self._sql_execute_funcion()
		self.anulado = True

	def _sql_execute_funcion(self):
		query = """select remove_account_moves(%s)"""
		params = [self.name]
		self.env.cr.execute(query, tuple(params))
		res = self.env.cr.dictfetchall()
		print (res)

	def _sql_report_object_unb(self):
		query_funcion="""CREATE OR REPLACE FUNCTION public.remove_account_moves(x_order character varying)
			RETURNS character varying AS
			$BODY$
					DECLARE
					r record;
					p_mo_id numeric;
					p_mo_name character varying;
					c CURSOR FOR  select ID,MOVE_ID from account_move_line  where name = x_order;
					m CURSOR FOR  select ID,MOVE_ID from account_move_line  where name = p_mo_name;
				BEGIN
					p_mo_id := (select mo_id from mrp_unbuild where name = x_order);
					p_mo_name := (select name from mrp_production where id = p_mo_id);
					FOR r IN c LOOP
						delete from account_move_line where id = r.id;
						delete from account_move where id = r.move_id;
					END LOOP;
					FOR p IN m LOOP
						delete from account_move_line where id = p.id;
						delete from account_move where id = p.move_id;
					END LOOP;
					RETURN 'FUNCION EJECUTADA CON EXITO';
				END;
			$BODY$
  			LANGUAGE plpgsql VOLATILE
  			COST 100;"""
  		self.env.cr.execute(query_funcion)

