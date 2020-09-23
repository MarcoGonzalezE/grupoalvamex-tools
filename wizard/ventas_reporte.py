# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)
import xlwt
from cStringIO import StringIO
import base64
from xlwt import easyxf

#TODO: Reporte de Ventas (Recepcion de Datos)
class ReporteVentas(models.TransientModel):
	_name = 'reporte.ventas'

	tipo = fields.Selection([('fecha','Por Fecha'),('periodo','Por Periodo')], string="Tipo")
	fecha_inicio = fields.Date(string="Fecha Inicial")
	fecha_final = fields.Date(string="Fecha Final", default=fields.Datetime.now)
	periodo = fields.Many2one('account.period', string="Periodo")

	file_name_xls = fields.Char()
	file_name_pdf = fields.Char()
	reporte_ventas_file_xls = fields.Binary('File XLS', readonly=True)
	reporte_ventas_file_pdf = fields.Binary('File PDF', readonly=True)
	report_exported = fields.Boolean()

	@api.multi
	def imprimirPDF(self):
		data={}		
		self._sql_consulta_ventas_periodo()
		self.env['reporte.ventas.object'].search([]).unlink()
		self.parametros()
		data['form'] = self.read(['fecha_inicio','fecha_final'])[0]
		data['form'].update(self.read(['fecha_inicio','fecha_final'])[0])
		return self.env['report'].get_action(self,'grupoalvamex_tools.reporte_ventas', data=data)

	# @api.multi
	# def imprimirPDF(self):
	# 	self._sql_consulta_ventas_periodo()
	# 	self.env['reporte.ventas.object'].search([]).unlink()
	# 	self.parametros()
	# 	self.render_pdf()
	# 	return {
	# 		'view_mode': 'form',
	# 		'res_id': self.id,
	# 		'res_model': 'reporte.ventas',
	# 		'view_type': 'form',
	# 		'type': 'ir.actions.act_window',
	# 		'view_id': self.env.ref('grupoalvamex_tools.reporte_ventas_wizard_form').id,
	# 		'context': self.env.context,
	# 		'target': 'new',
	# 	}


	@api.multi
	def imprimirXLS(self):
		self._sql_consulta_ventas_periodo()
		self.env['reporte.ventas.object'].search([]).unlink()
		self._sql_consulta_facturas_periodo()
		self.env['reporte.facturas.object'].search([]).unlink()
		self.parametros()
		self.render_xls()
		return {
			'view_mode': 'form',
			'res_id': self.id,
			'res_model': 'reporte.ventas',
			'view_type': 'form',
			'type': 'ir.actions.act_window',
			'view_id': self.env.ref('grupoalvamex_tools.reporte_ventas_wizard_form').id,
			'context': self.env.context,
			'target': 'new',
		}		

	def parametros(self):
		query = """INSERT INTO reporte_ventas_object
			(default_code,
			product,
			invoice_units,
			sale_price_unit,
			invoice_kgs,
			sale_price_kgs,
			invoice_total)
			SELECT * FROM sales_report_period(%s,%s)"""
		query_fact = """INSERT INTO reporte_facturas_object
			(customer,invoice,date_invoice,month,state,residual,paid_in_cash,
			category,
			invoice_units,
			invoice_kgs,
			invoice_total, amount_paid)
			SELECT * FROM invoice_report_period(%s,%s)"""
		params = [self.fecha_inicio, self.fecha_final]
		self.env.cr.execute(query, tuple(params))
		self.env.cr.execute(query_fact, tuple(params))

	def _sql_consulta_ventas_periodo(self):
		query = """CREATE OR REPLACE FUNCTION public.sales_report_period(x_fecha_inicio date, x_fecha_final date)
			RETURNS TABLE(sku character varying, 
				producto character varying, 
				unidades_facturadas numeric, 
				precio_vta_unidad numeric,
				kgs_facturados numeric, 
				precio_vta_kg numeric,
				facturado_total numeric) AS
			$BODY$
			DECLARE

			BEGIN
				CREATE TEMP TABLE CONSULTA_VENTAS ON COMMIT DROP AS(
				SELECT
				pt.default_code as SKU,
				pt.name as PRODUCTO,
				sum(ail.quantity) UNIDADES_FACTURADAS,
				round((sum(ail.amount_subtotal) / sum(ail.quantity)),2) as PRECIO_VENTA_POR_UNIDAD,
				sum(cast(sol.kilograms as numeric)) as KILOGRAMOS_FACTURADOS,
				round((sum(ail.amount_subtotal) / NULLIF(sum(cast(sol.kilograms as numeric)),0)),2) as PRECIO_VENTA_POR_KILOGRAMO,
				round(sum(ail.amount_subtotal),2) as FACTURADO_TOTAL_$
				from account_invoice ai
				inner join account_invoice_line ail on ai.id = ail.invoice_id
				inner join product_product pp on pp.id = ail.product_id
				inner join product_template pt on pt.id = pp.product_tmpl_id
				inner join sale_order_line_invoice_rel rel on rel.invoice_line_id  = ail.id
				inner join sale_order_line sol on sol.id = rel.order_line_id
				where ai.date between x_fecha_inicio and x_fecha_final and (ai.state = 'open' or ai.state = 'paid')
				and pt.default_code like 'PT%'
				group by pt.default_code,pt.name
				order by pt.default_code
				);

				RETURN QUERY

				SELECT *
				FROM CONSULTA_VENTAS k
				order by k.sku;

			END;
			$BODY$
			LANGUAGE plpgsql VOLATILE"""
		self.env.cr.execute(query)

	def _sql_consulta_facturas_periodo(self):
		query = """CREATE OR REPLACE FUNCTION public.invoice_report_period(x_fecha_inicio date, x_fecha_final date)
			RETURNS TABLE(cliente character varying,factura character varying, fecha character varying,mes float,
			    estado TEXT, 
			    residual numeric, pagado_en_caja TEXT, 
				categoria TEXT, 
				unidades_facturadas numeric,				
				kgs_facturados numeric, 
				facturado_total numeric,
				importe_pagado numeric) AS
			$BODY$
			DECLARE

			BEGIN
				CREATE TEMP TABLE CONSULTA_FACTURAS ON COMMIT DROP AS(
				SELECT
				CAST(rp.name as character varying) as CLIENTE,
				ai.number as FACTURA,
				CAST(ai.date_invoice as character varying) as Fecha,
				EXTRACT(MONTH FROM ai.date_invoice) as Mes,
				CASE WHEN ai.state = 'paid' then 'PAGADO' else 'ABIERTA' END as Estado,
				ai.residual as Adeudo,
				CASE When ai.paid_in_cash = 't' then 'PAGADO' else 'NO PAGADO' END as Pagado_En_Caja,
				CASE When pc.name like 'PT HUEVO%' then 'PT HUEVO' else 
				CASE When pc.name like 'PT CERDO%' then 'PT CERDO' else 'PT VARIOS' end end as CATEGORIA,
				sum(ail.quantity) UNIDADES_FACTURADAS,
				sum(cast(sol.kilograms as numeric)) as KILOGRAMOS_FACTURADOS,
				round(sum(ail.price_subtotal),2) as FACTURADO_TOTAL_$,
				round(sum(ail.price_subtotal),2) - ai.residual as Importe_Pagado
				
				from account_invoice ai
				inner join account_invoice_line ail on ai.id = ail.invoice_id
				inner join product_product pp on pp.id = ail.product_id
				inner join product_template pt on pt.id = pp.product_tmpl_id
				inner join product_category pc on pc.id = pt.categ_id
				inner join sale_order_line_invoice_rel rel on rel.invoice_line_id  = ail.id
				inner join sale_order_line sol on sol.id = rel.order_line_id
				inner join res_partner rp on rp.id = ai.partner_id
				where ai.date between x_fecha_inicio and x_fecha_final and (ai.state = 'open' or ai.state = 'paid')
				and pt.default_code like 'PT%'
				group by rp.name,ai.number,ai.date_invoice, ai.state,8,ai.paid_in_cash,ai.residual
				order by ai.date_invoice);
				RETURN QUERY
				SELECT * FROM CONSULTA_FACTURAS q 
				order by q.factura;
				END;
				$BODY$
				LANGUAGE plpgsql VOLATILE"""
		self.env.cr.execute(query)

	def render_xls(self):
		self.env['reporte.ventas.object'].search([])
		self.env['reporte.facturas.object'].search([])
		rep = self.env['reporte.ventas']

		sum_total_invoiced_poultry = 0
		sum_total_kgs_poultry = 0
		sum_total_invoiced_pig = 0
		sum_total_kgs_pig = 0

		for i in self.env['reporte.ventas.object'].search([]):
			default_code = i.default_code
			if "PT41" in str(default_code) or "PT42" in str(default_code):
				sum_total_invoiced_poultry += i.invoice_total
				sum_total_kgs_poultry += i.invoice_kgs

			if "PT43" in str(default_code):
				sum_total_invoiced_pig += i.invoice_total
				sum_total_kgs_pig += i.invoice_kgs

		workbook = xlwt.Workbook()
		miles_style = xlwt.easyxf("", "#,##0.00")
		currency_style = xlwt.easyxf("",'"$"#,##0.00_);("$"#,##',)

		column_heading_style = easyxf('font:height 200;font:bold True;')
		worksheet = workbook.add_sheet('Reporte de Ventas')
		worksheet.write(1, 3, 'REPORTE DE VENTAS'),easyxf('font:bold True;align: horiz center;')
		worksheet.write(2, 3, 'Resumen del: '+ str(self.fecha_inicio) + ' al ' + str(self.fecha_final), easyxf('font:height 200;font:bold True;align: horiz center;'))
		#worksheet.write(4, 0, _('Fecha'), column_heading_style)
		worksheet.write(4, 0, _('Codigo'), column_heading_style)
		worksheet.write(4, 1, _('Producto'), column_heading_style)
		worksheet.write(4, 2, _('Unidades Facturadas'), column_heading_style)
		worksheet.write(4, 3, _('Precio Venta/Unidad'), column_heading_style)
		worksheet.write(4, 4, _('Kg. Facturados'), column_heading_style)
		worksheet.write(4, 5, _('Precio Venta/Kilo'), column_heading_style)
		worksheet.write(4, 6, _('Total Facturado'), column_heading_style)

		worksheet.col(0).width = 4000
		worksheet.col(1).width = 12000
		worksheet.col(2).width = 4000
		worksheet.col(3).width = 4000
		worksheet.col(4).width = 4000
		worksheet.col(5).width = 4000
		worksheet.col(6).width = 4000
		worksheet.col(7).width = 4000

		row = 5
		resumen = self.env['reporte.ventas.object'].search([])
		for r in resumen:
			#worksheet.write(row, 0, r.date_invoice)
			worksheet.write(row, 0, r.default_code)
			worksheet.write(row, 1, r.product)
			worksheet.write(row, 2, r.invoice_units, miles_style)
			worksheet.write(row, 3, r.sale_price_unit, currency_style)
			worksheet.write(row, 4, r.invoice_kgs, miles_style)
			worksheet.write(row, 5, r.sale_price_kgs, currency_style)
			worksheet.write(row, 6, r.invoice_total, currency_style)
			row += 1
		sig = row
		worksheet.write(sig + 1, 1, 'AVICOLA'),easyxf('font:bold True;align: horiz center;')
		worksheet.write(sig + 2, 0, _('Total Facturado'), column_heading_style)
		worksheet.write(sig + 2, 1, sum_total_invoiced_poultry,currency_style)
		worksheet.write(sig + 3, 0, _('Total Kilogramos Facturados '), column_heading_style)
		worksheet.write(sig + 3, 1, sum_total_kgs_poultry,miles_style)

		worksheet.write(sig + 1, 5, 'PORCICOLA'),easyxf('font:bold True;align: horiz center;')
		worksheet.write(sig + 2, 4, _('Total Facturado'), column_heading_style)
		worksheet.write(sig + 2, 5, sum_total_invoiced_pig,currency_style)
		worksheet.write(sig + 3, 4, _('Total Kilogramos Facturados '), column_heading_style)
		worksheet.write(sig + 3, 5, sum_total_kgs_pig,miles_style)

		#FACTURAS
		worksheet_f = workbook.add_sheet('Reporte de Facturas')
		#worksheet_f.write(1, 3, 'FACTURAS'),easyxf('font:bold True;align: horiz center;')
		worksheet_f.write(0, 0, _('Cliente'), column_heading_style)
		worksheet_f.write(0, 1, _('Factura'), column_heading_style)
		worksheet_f.write(0, 2, _('Mes'), column_heading_style)
		worksheet_f.write(0, 3, _('Fecha'), column_heading_style)
		worksheet_f.write(0, 4, _('Estado'), column_heading_style)
		worksheet_f.write(0, 5, _('Pagado en Caja'), column_heading_style)
		worksheet_f.write(0, 6, _('Categoria'), column_heading_style)
		#worksheet_f.write(2, 5, _('Codigo'), column_heading_style)
		#worksheet_f.write(2, 6, _('Producto'), column_heading_style)
		worksheet_f.write(0, 7, _('Unidades Facturadas'), column_heading_style)
		#worksheet_f.write(2, 7, _('Precio Venta/Unidad'), column_heading_style)
		worksheet_f.write(0, 8, _('Kg. Facturados'), column_heading_style)
		#worksheet_f.write(2, 9, _('Precio Venta/Kilo'), column_heading_style)
		worksheet_f.write(0, 9, _('Total Facturado'), column_heading_style)
		worksheet_f.write(0, 10, _('Importe Adeudado'), column_heading_style)
		worksheet_f.write(0, 11, _('Importe Pagado'), column_heading_style)
		row = 1
		resumen_f = self.env['reporte.facturas.object'].search([])
		for r in resumen_f:
			worksheet_f.write(row, 0, r.customer)
			worksheet_f.write(row, 1, r.invoice)
			worksheet_f.write(row, 2, r.month)
			worksheet_f.write(row, 3, r.date_invoice)
			worksheet_f.write(row, 4, r.state)
			worksheet_f.write(row, 5, r.paid_in_cash)
			worksheet_f.write(row, 6, r.category)
			#worksheet_f.write(row, 5, r.default_code)
			#worksheet_f.write(row, 6, r.product)
			worksheet_f.write(row, 7, r.invoice_units, miles_style)
			#worksheet_f.write(row, 7, r.sale_price_unit, currency_style)
			worksheet_f.write(row, 8, r.invoice_kgs, miles_style)
			#worksheet_f.write(row, 9, r.sale_price_kgs, currency_style)
			worksheet_f.write(row, 9, r.invoice_total, currency_style)
			worksheet_f.write(row, 10, r.residual, currency_style)
			worksheet_f.write(row, 11, r.amount_paid, currency_style)
			row += 1

		fp = StringIO()
		workbook.save(fp)
		excel_file = base64.encodestring(fp.getvalue())
		self.reporte_ventas_file_xls = excel_file
		self.file_name_xls = 'Reporte de Ventas.xls'
		self.report_exported = True
		fp.close()

	# def render_pdf(self):
	# 	self.model = self.env.context.get('active_model')
	# 	docs = self.env[self.model].browse(self.env.context.get('active_id'))
	# 	invoices = self.env['reporte.ventas.object'].search([])
	# 	if invoices:
	# 		sum_total_invoiced_poultry = 0
	# 		sum_total_kgs_poultry = 0

	# 		sum_total_invoiced_pig = 0
	# 		sum_total_kgs_pig = 0

	# 		for i in invoices:
	# 			default_code = i.default_code
	# 			if "PT41" in str(default_code) or "PT42" in str(default_code):
	# 				sum_total_invoiced_poultry += i.invoice_total
	# 				sum_total_kgs_poultry += i.invoice_kgs
	# 			if "PT43" in str(default_code):
	# 				sum_total_invoiced_pig += i.invoice_total
	# 				sum_total_kgs_pig += i.invoice_kgs

	# 		docargs = {
	# 			'docs': docs,
	# 			'invoice': invoices,
	# 			'sum_total_invoiced_poultry': sum_total_invoiced_poultry,
	# 			'sum_total_kgs_poultry': sum_total_kgs_poultry,
	# 			'sum_total_invoiced_pig': sum_total_invoiced_pig,
	# 			'sum_total_kgs_pig': sum_total_kgs_pig
	# 		}
	# 		return self.env['report'].render('grupoalvamex_tools.reporte_ventas', docargs)
	# 	else:
	# 		raise UserError("No se encontraron datos")


#TODO: Reporte de Ventas (Datos base)
class ReporteVentasObject(models.Model):
	_name = 'reporte.ventas.object'

	#date_invoice = fields.Char() #Fecha
	default_code = fields.Char() #Codigo del Producto
	product = fields.Char() #Producto
	invoice_units = fields.Float() #Unidades Facturadas
	sale_price_unit = fields.Float() #Precio de Venta por Unidad
	#cost_unit = fields.Float()
	invoice_kgs = fields.Float() #Kilogramos Facturados
	sale_price_kgs = fields.Float() #Precio de Venta por Kilo
	#cost_kgs = fields.Float()
	invoice_total = fields.Float() #Total Facturado
	#cancel_nc = fields.Float()
	#invoice_total_nc = fields.Float()
	#cost_total = fields.Float()

#TODO: Reporte de Facturas (Datos Base)
class ReporteFacturasObject(models.Model):
	_name = 'reporte.facturas.object'

	customer = fields.Char()
	invoice = fields.Char() #Factura
	date_invoice = fields.Char()
	month = fields.Float()
	state = fields.Char()
	residual = fields.Float()
	paid_in_cash = fields.Char()
	#default_code = fields.Char() #Codigo del Producto
	#product = fields.Char() #Producto
	category = fields.Char()
	invoice_units = fields.Float() #Unidades Facturadas
	#sale_price_unit = fields.Float() #Precio de Venta por Unidad
	invoice_kgs = fields.Float() #Kilogramos Facturados
	#sale_price_kgs = fields.Float() #Precio de Venta por Kilo
	invoice_total = fields.Float() #Total Facturado
	amount_paid = fields.Float()

#TODO: Reporte de Ventas PDF
class ReporteVentasPDF(models.AbstractModel):
    _name ="report.grupoalvamex_tools.reporte_ventas"

    @api.model
    def render_html(self,docids,data = None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        invoices = self.env['reporte.ventas.object'].search([])
        dates = self.env['reporte.ventas'].search([], order='id desc', limit=1)
        if invoices:
            #poultry variables
            sum_total_invoiced_poultry = 0
            #sum_total_cancel_poultry = 0
            sum_total_cost_poultry = 0
            sum_total_invoiced_minus_cancel_poultry = 0
            sum_total_kgs_poultry = 0
            utility_poultry = 0

            #pig variables
            sum_total_invoiced_pig = 0
            sum_total_cancel_pig = 0
            #sum_total_cost_pig = 0
            sum_total_invoiced_minus_cancel_pig = 0
            sum_total_kgs_pig = 0
            utility_pig = 0

            fecha_inicio = dates.fecha_inicio
            fecha_final = dates.fecha_final

            for i in invoices:
                default_code = i.default_code
                if "PT41" in str(default_code) or "PT42" in str(default_code):
                    sum_total_invoiced_poultry += i.invoice_total
                    #sum_total_cancel_poultry += i.cancel_nc
                    #sum_total_cost_poultry += i.cost_total
                    #sum_total_invoiced_minus_cancel_poultry += i.invoice_total_nc
                    sum_total_kgs_poultry += i.invoice_kgs


                if "PT43" in str(default_code):
                    sum_total_invoiced_pig += i.invoice_total
                    #sum_total_cancel_pig += i.cancel_nc
                    #sum_total_cost_pig += i.cost_total
                    #sum_total_invoiced_minus_cancel_pig += i.invoice_total_nc
                    sum_total_kgs_pig += i.invoice_kgs

            #utility_poultry = sum_total_invoiced_minus_cancel_poultry - sum_total_cost_poultry
            #utility_pig = sum_total_invoiced_minus_cancel_pig - sum_total_cost_pig

            docargs = {
              'docs': docs,
              'invoice': invoices,
              'sum_total_invoiced_poultry': sum_total_invoiced_poultry,
              #'sum_total_cancel_poultry': sum_total_cancel_poultry,
              #'sum_total_cost_poultry': sum_total_cost_poultry,
              #'sum_total_invoiced_minus_cancel_poultry': sum_total_invoiced_minus_cancel_poultry,
              'sum_total_kgs_poultry':sum_total_kgs_poultry,
              'utility_poultry':utility_poultry,
              'sum_total_invoiced_pig': sum_total_invoiced_pig,
              #'sum_total_cancel_pig': sum_total_cancel_pig,
              #'sum_total_cost_pig': sum_total_cost_pig,
              #'sum_total_invoiced_minus_cancel_pig': sum_total_invoiced_minus_cancel_pig,
              'sum_total_kgs_pig':sum_total_kgs_pig,
              'utility_pig': utility_pig,
              'fecha_inicio': fecha_inicio,
              'fecha_final': fecha_final
            }
            return self.env['report'].render('grupoalvamex_tools.reporte_ventas', docargs)
        else:
            raise UserError("No se encontraron datos")


class ReporteVentasXLS(models.TransientModel):
    _name = "report.xls.reporte_ventas"

    reporte_ventas_file = fields.Binary('Reporte de Ventas')
    file_name = fields.Char('File Name')
    report_exported = fields.Boolean('Resumen de Ventas Exportado')    

    def render_xls(self):
        self.env['reporte.ventas.object'].search([])
        rep = self.env['reporte.ventas']

        workbook = xlwt.Workbook()
        column_heading_style = easyxf('font:height 200;font:bold True;')
        worksheet = workbook.add_sheet('Reporte de Ventas')
        worksheet.write(2, 3, 'Resumen del: '+ rep.fecha_inicio + 'al' + rep.fecha_final,
                        easyxf('font:height 200;font:bold True;align: horiz center;'))

        fp = StringIO()
        workbook.save(fp)
        excel_file = base64.encodestring(fp.getvalue())
        self.reporte_ventas_file = excel_file
        self.file_name = 'Reporte de ventas.xls'
        self.report_exported = True
        fp.close()
        return {
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'report.xls.reporte_ventas',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'target': 'current',
        }
