# -*- coding: utf-8 -*-

from odoo import _, fields, models, api
from odoo.exceptions import UserError, ValidationError
import datetime, exceptions, warnings

class ventas_produccion(models.Model):
    _name = 'ventas.produccion'
    _inherit = ['mail.thread']

    name = fields.Char(string="Folio", track_visibility='onchange', default="Nuevo")
    producto = fields.Many2many('sale.order.line', string="Productos")
    fecha_pedido = fields.Datetime(string="Fecha de Pedido", default=fields.Date.today(), track_visibility='onchange')
    fecha_produccion = fields.Datetime(string="Fecha aceptacion", track_visibility='onchange')
    enviado_pt = fields.Boolean(string="Validacion de Salida", default=False, track_visibility='onchange')
    fecha_inicio = fields.Datetime(string="Fecha Inicio", track_visibility='onchange')
    fecha_termino = fields.Datetime(string="Fecha Terminacion", track_visibility='onchange')
    cliente = fields.Many2one('res.partner',  string="Cliente:", track_visibility='onchange')
    estado = fields.Selection([('creado', 'Nuevo'),
                               ('enviado', 'Enviado a Produccion'),
                               ('aceptado', 'En proceso'),
                               ('cancel', 'Cancelado'),
                               ('final', 'Finalizado')], default='creado', string="Estado", track_visibility='onchange')
    ventas_id = fields.Many2many('sale.order', string="Ventas")

    #ENVIAR A PRODUCCION
    @api.multi
    def enviado(self):
        self.estado = 'enviado'
        self.fecha_inicio = datetime.datetime.now()

    #APROBAR PEDIDO
    @api.multi
    def aceptado(self):
        self.estado = 'aceptado'
        self.fecha_produccion = datetime.datetime.now()

    #FINALIZAR
    @api.multi
    def listo(self):
        if self.enviado_pt == True:
             self.estado = 'final'
             self.fecha_termino = datetime.datetime.now()
        else:
            raise ValidationError(
                _('Tiene que VALIDAR SALIDA el departamento de VENTAS'))

    @api.multi
    def cancelado(self):
        self.estado = 'cancel'

    #VALIDACION DE SALIDA
    @api.multi
    def check_aprobado(self):
        self.enviado_pt = 'True'

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('ventas.produccion') or "Nuevo"
        return super(ventas_produccion, self).create(vals)       

class sale_order(models.Model):
    _inherit = 'sale.order'

  
    def open_wizard_button(self, cr, uid, ids, context=None):
        return {
            'name': ('Assignment Sub'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ru.assignments.sub',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

class VentasPlaneacionProduccion(models.TransientModel):
    _name = 'ventas.produccion.planeacion'

    @api.model
    def default_get(self, default_fields):
        res = super(VentasPlaneacionProduccion, self).default_get(default_fields)
        ventas_id = self._context.get('active_ids')
        ventas = self.env['sale.order'].browse(ventas_id)
        self.validate(ventas)
        return res

    @api.multi
    def planeacion(self):
        ventas = self.env['sale.order'].browse(self._context.get('active_ids'))        
        planeacion = self.env['ventas.produccion'].create({
            'cliente': ventas[0].partner_id.id,
            'fecha_pedido': ventas[0].date_order,
            #'ventas_id': ventas[0].id,
            # 'productos': ventas[0].order_line.id,
        })
        # for record in lineas_ventas:
        #     planeacion.write({'producto':[(4, record.id)]})

        for venta in ventas:
        #     record.write({'planeacion': order_line.id})
            planeacion.write({'ventas_id': [(4, venta.id)]})
            lineas_ventas = self.env['sale.order.line'].search([('order_id','=',venta.id)])
            message = _('<strong>Planeacion:</strong> %s </br>') % (', '.join(planeacion.mapped('name')))
            venta.message_post(body=message)
            for linea in lineas_ventas:
                planeacion.write({'producto':[(4, linea.id)]})

        return{
            'name': 'Planeacion',
            'view_id': self.env.ref('grupoalvamex_tools.ventas_produccion_form').id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ventas.produccion',
            'res_id': planeacion.id,
            'type': 'ir.actions.act_window'
        }

    @api.model
    def validate(self, reports):
        # if len(reports.mapped('operating_unit_id')) > 1:
        #     raise ValidationError(
        #         _('All reports must be in the same Operating Unit'))
        if len(reports.mapped('partner_id')) > 1:
            raise ValidationError(
                _('Todos los pedidos deben de tener el mismo CLIENTE'))
        # if reports.mapped('order_id'):
        #     raise ValidationError(
        #         _('All least one record has an order assigned'))




