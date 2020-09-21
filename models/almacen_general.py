# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime, timedelta, date


class PurchaseOrderAlmacenGeneral(models.Model):
    _inherit = 'purchase.order'
    _description = 'Recepcion de material en almacen general'

    received = fields.Selection([('completed_received', 'Recibido Completo'), ('partial_received', 'Recibido Incompleto'), ('pending', 'Pendiente de Recibir')], string='Status Almacen General', default='pending')
    received_date = fields.Date('Fecha Recibido')

    @api.onchange('received')
    def notificacion(self):
        compra = self.env['purchase.order'].search([('name', '=', self.name)])
        followers = self.env['mail.followers'].search(
            [('res_model', '=', 'purchase.order'), ('res_id', '=', compra.id)])
        if self.received == 'completed_received' or self.received == 'partial_received':
            for follow in followers:
                print(follow.partner_id.name)
                notificacion_template = self.env['ir.model.data'].sudo().get_object('grupoalvamex_tools', 'notificacion_compra_almacen')
                values = notificacion_template.generate_email(compra.id)
                values['model'] = 'purchase.order'
                values['res_id'] = self.id  # OJO AQUI
                if self.received == 'completed_received':
                    self.received_date = date.today()
                    values['body_html'] = values['body_html'].replace("_estado_compra_", "Recibido Completo")
                if self.received == 'partial_received':
                    self.received_date = False
                    values['body_html'] = values['body_html'].replace("_estado_compra_", "Recibido Incompleto")
                if self.received == 'pending':
                    self.received_date = False
                values['email_to'] = follow.partner_id.email
                send_mail = self.env['mail.mail'].sudo().create(values)
                send_mail.send()