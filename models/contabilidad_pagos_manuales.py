# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
import amount_to_text_es_MX

def _default_currency(self):
        return self.env['res.currency'].search([('name','=','MXN')])

class cheque_manual(models.Model):
    _name = 'contabilidad.pagos.cheque'
    _inherit = ['mail.thread']

    name = fields.Char(string="Numero de Cheque")
    nombre = fields.Many2one('res.partner', string="Nombre")
    nombre2 = fields.Char(string="Nombre sin registro", track_visibility='onchange')
    cantidad = fields.Float(string="Cantidad", track_visibility='onchange')
    cantidad_letra = fields.Char(compute='_get_amount_to_text', store=True, track_visibility='onchange')
    currency_id = fields.Many2one("res.currency", string="Moneda", default=_default_currency)
    concepto = fields.Text(string="Concepto", track_visibility='onchange')
    fecha = fields.Date(string="Fecha", default=fields.Datetime.now, track_visibility='onchange')

    @api.onchange('nombre')
    def _onchange_nombre(self):
        self.nombre2 = self.nombre.name

    @api.one 
    @api.depends('cantidad','currency_id')
    def _get_amount_to_text(self):
        self.cantidad_letra = amount_to_text_es_MX.get_amount_to_text(self, self.cantidad, self.currency_id.name)

class transferencia_solicitud(models.Model):
    _name = 'contabilidad.pagos.transferencia'
    _inherit = ['mail.thread']    

    name = fields.Char(string="Solicitud Transferecia", default="Nueva")
    nombre = fields.Many2one('res.partner', string="Nombre")
    nombre2 = fields.Char(string="Nombre sin registro", track_visibility='onchange')
    vencimiento = fields.Date(string="Vencimiento", track_visibility='onchange')
    cantidad = fields.Float(string="Cantidad", track_visibility='onchange')
    cantidad_letra = fields.Char(compute='_get_amount_to_text', store=True, track_visibility='onchange')
    currency_id = fields.Many2one('res.currency', string="Moneda", default=_default_currency)
    cuenta = fields.Char(string="Cuenta", track_visibility='onchange')
    clabe = fields.Char(string="Clabe", track_visibility='onchange')
    banco = fields.Char(string="Banco", track_visibility='onchange')
    concepto = fields.Text(string="Concepto", track_visibility='onchange')
    fecha = fields.Date(string="Fecha", default=fields.Datetime.now, track_visibility='onchange')

    @api.onchange('nombre')
    def _onchange_nombre(self):
        self.nombre2 = self.nombre.name
        cuentas = self.env['res.partner.bank'].search([('partner_id','=',self.nombre.id)], limit=1)
        self.cuenta = cuentas.acc_number
        self.clabe = cuentas.clabe
        self.banco = cuentas.bank_id.name

    @api.one 
    @api.depends('cantidad','currency_id')
    def _get_amount_to_text(self):
        self.cantidad_letra = amount_to_text_es_MX.get_amount_to_text(self, self.cantidad, self.currency_id.name)

    @api.model
    def create(self, vals):
        if vals.get('name', "Nueva") == "Nueva":
            vals['name'] = self.env['ir.sequence'].next_by_code('contabilidad.pagos.transferencia') or "Nueva"
            return super(transferencia_solicitud, self).create(vals)