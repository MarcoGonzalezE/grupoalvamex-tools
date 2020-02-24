# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class PurchaseOrderAlmacenGeneral(models.Model):
    _inherit = 'purchase.order'
    _description = 'Recepcion de material en almacen general'


    received = fields.Selection([('completed_received','Recibido Completo'),('partial_received','Recibido Incompleto'),('pending','Pendiente de Recibir')],string='Status Almacen General',default='pending')
    received_date = fields.Date('Fecha Recibido')
