# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class mrp_contabilidad(models.Model):
	_name = 'mrp.wizard.contabilidad'
	_description = "Funciones para el cambio de fechas en asientos contables"
	_inherit = ['mail.thread']

	name = fields.Char(string="Funcion", default="Asientos contables")
	operacion = fields.Selection([('mes','Mes'),
								  ('semana','Semana')], string="Ejecutar por", required=True, track_visibility='onchange')
	fecha_inicio = fields.Datetime(string="Fecha Inicial")
	fecha_final = fields.Datetime(string="Fecha Final")
	periodo = fields.Many2one('account.period', string="Periodo", track_visibility='onchange')
	resultado = fields.Text('Resultado', readonly=True)
	ultimaEjecucion = fields.Datetime(string="Ultima ejecucion", readonly=True, track_visibility='onchange')

	@api.onchange('periodo')
	def _onchange_periodo(self):
		inicio_fecha = self.periodo.date_start
		final_fecha = self.periodo.date_stop

		#inicio = inicio_fecha.replace(minute=0, hour=0, second=0)
		#final = final_fecha.replace(minute=59, hour=23, second=59)

		self.fecha_inicio = self.periodo.date_start
		self.fecha_final = self.periodo.date_stop

		#self.fecha_inicio = self.fecha_inicio.replace(minute=0, hour=0, second=0)
		#self.fecha_final = self.fecha_final.replace(minute=59, hour=23, second=59)




		# inicio = inicio_fecha.strftime("%Y%m%d")
		# final = final_fecha.strftime("%Y%m%d")

		#inicio_cont = inicio_fecha + '000000'
		#final_cont = final_fecha + '235959'

		#self.fecha_inicio = datetime.strptime(inicio_fecha, '%Y/%m/%d 00:00:00')
		#self.fecha_final = datetime.strptime(final_fecha, '%Y/%m/%d 23:59:59')

	@api.onchange('operacion')
	def _onchange_operacion(self):
		self.resultado = False

	def action_mrp_funcion(self):
		if self.operacion == 'mes':
			self._sql_trans()			
			self._sql_ord_prod()
		if self.operacion == 'semana':
			self._sql_trans_dia()
			self._sql_ord_prod_dia()
		self._sql_execute_funcion()
		self.ultimaEjecucion = datetime.now()
		

	def _sql_execute_funcion(self, context=None):
		if self.operacion == 'mes':
			query_trans = """select changedatetransfer(%s,%s,%s)"""
			query_op= """select changedatemanufactureorder(%s,%s,%s)"""
		if self.operacion == 'semana':
			query_trans = """select changedatetransfer_per_day(%s,%s,%s)"""
			query_op = """select changedatemanufactureorder_per_day(%s,%s,%s)"""

		params = [self.fecha_inicio, self.fecha_final, self.periodo.id]
		self.env.cr.execute(query_trans, tuple(params))
		self.env.cr.execute(query_op, tuple(params))
		res = self.env.cr.dictfetchall()
		print (res)
		self.resultado = res
		


#TRANSFERENCIAS
	def _sql_trans(self):
		query_funcion="""CREATE OR REPLACE FUNCTION public.changedatetransfer(x_fecha_inicio date, x_fecha_final date, x_periodo integer)
    		RETURNS character varying AS
			$BODY$
			DECLARE
  				r record;
  				c CURSOR FOR  select sp.min_date mindate,am.id amid,am.date amdate,am.period_id amperiod,aml.id amlid,aml.date amldate,aml.period_id amlperiod, aml.date_maturity amldatematurity
				from stock_picking sp
				inner join account_move am on am.ref = sp.name
				inner join account_move_line aml on aml.move_id = am.id
				where sp.min_date at time zone 'utc' between x_fecha_inicio and x_fecha_final and am.period_id <> x_periodo; 
			BEGIN	
  				FOR r IN c LOOP			
					IF r.amdate <> r.mindate
						THEN
						update account_move set date = r.mindate, period_id = x_periodo where id = r.amid;
					END IF;
					IF r.amldate <> r.mindate
						THEN
						update account_move_line set date = r.mindate,period_id = x_periodo, date_maturity = r.mindate where id = r.amlid;
					END IF;	
				END LOOP;
				RETURN 'FUNCION EJECUTADA CON EXITO';  
			END;
			$BODY$
			LANGUAGE plpgsql VOLATILE
			COST 100;"""
		self.env.cr.execute(query_funcion)
#TRANSFERENCIAS POR DIA
	def _sql_trans_dia(self):
		query_funcion="""CREATE OR REPLACE FUNCTION public.changedatetransfer_per_day(x_fecha_inicio date, x_fecha_final date, x_periodo integer)
			RETURNS character varying AS
			$BODY$
			DECLARE
				r record;
				c CURSOR FOR  select sp.min_date mindate,am.id amid,am.date amdate,am.period_id amperiod,aml.id amlid,aml.date amldate,aml.period_id amlperiod, aml.date_maturity amldatematurity
				from stock_picking sp
				inner join account_move am on am.ref = sp.name
				inner join account_move_line aml on aml.move_id = am.id
				where sp.min_date at time zone 'utc' between x_fecha_inicio and x_fecha_final; 
			BEGIN	
				FOR r IN c LOOP			
					IF r.amdate <> r.mindate
						THEN
						update account_move set date = r.mindate where id = r.amid;
					END IF;
					IF r.amldate <> r.mindate
						THEN
						update account_move_line set date = r.mindate, date_maturity = r.mindate where id = r.amlid;
					END IF;	
				END LOOP;
				RETURN 'FUNCION EJECUTADA CON EXITO';  
			END;
			$BODY$
			LANGUAGE plpgsql VOLATILE
			COST 100;"""
		self.env.cr.execute(query_funcion)
#ORDEN DE PRODUCCION
	def _sql_ord_prod(self):
		query_funcion="""CREATE OR REPLACE FUNCTION public.changedatemanufactureorder(x_fecha_inicio date, x_fecha_final date, x_periodo integer)
			RETURNS character varying AS
			$BODY$
			DECLARE
  				r record;
  				c CURSOR FOR  select mp.id mpid,aml.id amlid,am.id amid,sm.id smid,sm.date smdate,aml.date amldate,am.date amdate,am.period_id period,mp.date_planned_start at time zone 'utc' as date_planned_start from mrp_production  mp
	        	inner join stock_move sm on sm.origin = mp.name
	        	inner join account_move_line aml on aml.name = mp.name
				inner join account_move am on am.id = aml.move_id
				where date_planned_start at time zone 'utc' between x_fecha_inicio and x_fecha_final and am.period_id <> x_periodo;
			BEGIN	
  				FOR r IN c LOOP	
        			IF r.smdate <> r.date_planned_start
        				THEN
						update stock_move set date = r.date_planned_start where id = r.smid;
					END IF;
					IF r.amldate <> r.date_planned_start
						THEN
						update account_move_line set date = r.date_planned_start,period_id = x_periodo where id = r.amlid;		
					END IF;
					IF r.amdate <> r.date_planned_start
						THEN
						update account_move set date = r.date_planned_start,period_id = x_periodo where id = r.amid;		
					END IF;
  				END LOOP;
  				RETURN 'FUNCION EJECUTADA CON EXITO';  
			END;
			$BODY$
  			LANGUAGE plpgsql VOLATILE
  			COST 100;"""
		self.env.cr.execute(query_funcion)
#ORDEN DE PRODUCCION POR DIA
	def _sql_ord_prod_dia(self):
		query_funcion="""CREATE OR REPLACE FUNCTION public.changedatemanufactureorder_per_day(x_fecha_inicio date, x_fecha_final date, x_periodo integer)
  			RETURNS character varying AS
  		  	$BODY$
  		  	DECLARE
  		  		r record;
  		  		c CURSOR FOR select mp.id mpid,aml.id amlid,am.id amid,sm.id smid,sm.date smdate,aml.date amldate,am.date amdate,am.period_id period,mp.date_planned_start at time zone 'utc' as date_planned_start from mrp_production  mp
		        inner join stock_move sm on sm.origin = mp.name
		        inner join account_move_line aml on aml.name = mp.name
  				inner join account_move am on am.id = aml.move_id
  				where date_planned_start at time zone 'utc' between x_fecha_inicio and x_fecha_final;
	  		BEGIN
				FOR r IN c LOOP	
  		  			IF r.smdate <> r.date_planned_start
  		  		  		THEN
  		  		  		update stock_move set date = r.date_planned_start where id = r.smid;
  		  			END IF;
  		  		  	IF r.amldate <> r.date_planned_start
  		  		  		THEN
  		  		  		update account_move_line set date = r.date_planned_start,period_id = x_periodo where id = r.amlid;
  		  		  	END IF;
  		  		  	IF r.amdate <> r.date_planned_start
  		  		  		THEN
  		  		  		update account_move set date = r.date_planned_start,period_id = x_periodo where id = r.amid;
  		  		  	END IF;
  		  		END LOOP;
  		  		RETURN 'FUNCION EJECUTADA CON EXITO';  
  		  	END;
  		  	$BODY$
  		  	LANGUAGE plpgsql VOLATILE
  		  	COST 100;"""
  		self.env.cr.execute(query_funcion)


# 	@api.multi
# 	def action_of_button(self):
# 		message_id = self.env['message.wizard'].create({'message': _("Funcion ejecutada")})
# 		return {
#             'name': _('Completada'),
#             'type': 'ir.actions.act_window',
#             'view_mode': 'form',
#             'res_model': 'message.wizard',
#             'view_id' : 'message_wizard_form',
#             # pass the id
#             'res_id': message_id.id,
#             'target': 'new'
#         }

# class MensajeWizard(models.TransientModel):
# 	_name = 'message.wizard'
# 	message = fields.Text('Message', required=True)

# 	@api.multi
# 	def action_ok(self):
# 		return {'type': 'ir.actions.act_window_close'}
# 		