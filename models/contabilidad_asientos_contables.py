# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    fleet_id = fields.Many2one(comodel_name='fleet.vehicle', string="Vehiculo", store=True)