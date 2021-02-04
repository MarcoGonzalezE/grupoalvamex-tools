# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = 'Costo de produccion'

    manufacture_cost = fields.Float(string="Costo de Produccion")
    manufacture_origin = fields.Char(string="Formula")
    last_date_cost = fields.Date(string="Ultima Fecha de Costeo")

    product_related_id = fields.Many2one(comodel_name='product.product', string="Producto a Consumir")
    qty_consum = fields.Float(string="Consumo")