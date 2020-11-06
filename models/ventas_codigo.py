# -*- coding: utf-8 -*-

from odoo import _, fields, models, api
from odoo.exceptions import UserError, ValidationError
import exceptions, warnings
from datetime import datetime, timedelta

class VentasQR(models.Model):
	_name = 'ventas.qr'
	_rec_name = 'cliente_id'

	cliente_id = fields.Many2one('res.partner', string="Cliente")
	vendedor_id = fields.Many2one('vendedores.ventas', related="cliente_id.x_vendedores", string="Vendedor Asignado")
	productos_ids = fields.Many2many('product.product', string="Productos")
	codigo_qr = fields.Binary(string="Codigo QR")

	@api.model
	def default_get(self, default_fields):
		res = super(VentasQR, self).default_get(default_fields)
		ventasqr_ids = self._context.get('active_ids')
		venta_qr = self.env['ventas.qr'].browse(ventasqr_ids)
		return res

	@api.multi
	def registrar_venta(self):
		venta_qr = self.env['ventas.qr'].browse(self._context.get('active_ids'))
		orden_venta = self.env['sale.order'].create({
			'partner_id': self.cliente_id.id,
			'vendedores': self.vendedor_id.id,
			'date_order': datetime.today(),
			'picking_policy': 'direct',
		})
		for qr in self.productos_ids:
			orden_venta_lineas = self.env['sale.order.line'].create({
				'product_id': qr.id,
				'name': qr.name,
				'order_id': orden_venta.id,
				'product_uom_qty': 1,
				'price_unit': 1.0,
				})
		return {
			'name': 'Ventas',
			'view_id': self.env.ref('sale.view_order_form').id,
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'sale.order',
			'res_id': orden_venta.id,
			'type': 'ir.actions.act_window'
		}
