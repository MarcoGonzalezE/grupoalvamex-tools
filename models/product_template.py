# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = 'Costo de produccion'

    manufacture_cost = fields.Float(string="Costo de Produccion")
    manufacture_origin = fields.Char(string="Formula")
    last_date_cost = fields.Date(string="Ultima Fecha de Costeo")