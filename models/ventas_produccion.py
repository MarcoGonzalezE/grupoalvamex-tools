# -*- coding: utf-8 -*-

from odoo import _, fields, models, api
from odoo.exceptions import UserError, ValidationError
import datetime, exceptions, warnings

class SucursalesPlaneacion(models.Model):
    _name = 'sucursales.planeacion'

    name = fields.Char(string="Nombre")
    imagen = fields.Binary(string="Logo", attachment=True)

    #Planeacion - Ventas
    ventas_ids = fields.One2many('ventas.produccion', 'sucursal', string="Ventas")
    ventas_cont = fields.Integer(compute='get_contadores', store=False)

    #Inventario - Stock
    inventario_ids = fields.One2many('ventas.produccion.inventario', 'sucursal', string="Inventario")
    inventario_cont = fields.Integer(compute='get_contadores', store=False)

    @api.one
    @api.depends('ventas_ids','inventario_ids')
    def get_contadores(self):
        self.ventas_cont = len(self.ventas_ids.filtered(lambda s: s.estado in ('final')))
        self.inventario_cont = len(self.inventario_ids)

    @api.multi
    def act_ventas(self):
        action = self.env.ref('grupoalvamex_tools.ventas_produccion_action')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_type': action.view_type,
            'view_mode': action.view_mode,
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }

        result['domain'] = "[('id','in',["+','.join(map(str, self.ventas_ids.ids))+"])]"
        return result

    @api.multi
    def act_inventario(self):
        action = self.env.ref('grupoalvamex_tools.ventas_produccion_inventario_action')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_type': action.view_type,
            'view_mode': action.view_mode,
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        result['domain'] = "[('id','in',["+','.join(map(str, self.inventario_ids.ids))+"])]"
        return result


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
    cliente = fields.Many2one('res.partner',  string="Cliente", track_visibility='onchange')
    sucursal = fields.Many2one('sucursales.planeacion', string="CEDIS", track_visibility='onchange')
    estado = fields.Selection([('creado', 'Nuevo'),
                               ('enviado', 'Enviado a Produccion'),
                               ('aceptado', 'En proceso'),
                               ('cancel', 'Cancelado'),
                               ('final', 'Finalizado')], default='creado', string="Estado", track_visibility='onchange')
    ventas_id = fields.Many2many('sale.order', string="Ventas")
    aviso = fields.Text(string="Aviso")

    #ENVIAR A PRODUCCION
    @api.multi
    def enviado(self):
        for r in self:
            r.estado = 'final'
            r.fecha_inicio = datetime.datetime.now()

    #APROBAR PEDIDO
    @api.multi
    def aceptado(self):
        for r in self:
            r.estado = 'aceptado'
            r.fecha_produccion = datetime.datetime.now()

    #FINALIZAR
    @api.multi
    def listo(self):
        for r in self:
            r.estado = 'final'
            r.fecha_termino = datetime.datetime.now()
        """
         if self.enviado_pt == True:

         else:
             raise ValidationError(
                 _('Tiene que VALIDAR SALIDA el departamento de VENTAS'))
        """

    @api.multi
    def cancelado(self):
        for r in self:
            r.estado = 'cancel'

    #VALIDACION DE SALIDA
    @api.multi
    def check_aprobado(self):
        for r in self:
            r.enviado_pt = 'True'

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('ventas.produccion') or "Nuevo"
        return super(ventas_produccion, self).create(vals)

    #TODO: La comprobacion en la orden de planeacion solo muestra la sumatoria de productos
    #ERROR: Cuando tiene mas de un presupuesto en la pestaña de VENTAS marca error de parametros
    #IDEA: Con la sumatoria de productos compare con el stock que se tiene actualmente.
    def comprobar(self):
        for r in self:
            query="""Select pt.name as producto, sum(sol.product_uom_qty) as total
                    from sale_order so
                    inner join sale_order_line sol on sol.order_id = so.id
                    inner join product_product pp on sol.product_id = pp.id
                    inner join product_template pt on pp.product_tmpl_id = pt.id
                    where so.id in (%s)
                    group by sol.product_id, pt.name"""
            params = []
            for venta in r.ventas_id:
                venta_or = self.env['sale.order'].search([('id','=', venta.id)])
                venta_lin = self.env['sale.order.line'].search([('order_id', '=', venta_or.id)])
                params.append(venta_or.id)
                print(params)
            self.env.cr.execute(query, tuple(params))
            res = self.env.cr.dictfetchall()
            # for r in res:
            #     inventario = self.env['ventas.produccion.inventario'].search([('name.id','=', r.producto)])
            #     if r.sum < inventario.stock_total:
            #         mensaje = 'No hay suficiente producto en inventario de ' + inventario.name.name
            r.aviso = res

    # def comprobar(self):
    #     suma = 0
    #     count = 1
    #     for productos in self.producto:
    #         if productos[count].product_id == productos[count].product_id:
    #             count += 1
    #             suma += productos.product_uom_qty
    #         print("Producto:" + str(productos.name))
    #         print("Suma:" + str(suma))

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
class VentasProduccionInvetario(models.Model):
    _name = 'ventas.produccion.inventario'
    _description = "Inventario de Produccion"

    name = fields.Many2one('product.product', string="Producto")
    stock = fields.Float(string="Stock", compute="suma_entradas")
    stock_total = fields.Float(string="Stock Total", compute="stock_totales")
    entrada_ids = fields.One2many('inventario.entradas', 'entrada_id', string="Entradas de Inventario")
    devolucion_ids = fields.One2many('inventario.devoluciones', 'devolucion_id', string="Devoluciones de Inventario")
    ventas_ids = fields.Many2many('sale.order.line', string="Ventas")
    info = fields.Float(string="Stock", compute="total_info")
    imagen = fields.Binary(string="Imagen", attachment=True)
    ventas = fields.Float(string="Ventas", compute="suma_ventas")
    devoluciones = fields.Float(string="Devoluciones", compute="suma_devoluciones")
    s_min = fields.Float(string="Stock Minimo")
    s_fal = fields.Float(string="Stock Faltante", compute='stock_fl')
    mensaje = fields.Text(string="Mensaje", compute="total_info")
    sucursal = fields.Many2one('sucursales.planeacion', string="CEDIS")
    #faltante_info = fields.Float(string="Faltante", related="s_fal", store=True)

    @api.multi
    def act_entradas(self):
        action = self.env.ref('grupoalvamex_tools.inventario_entrada_action')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_type': action.view_type,
            'view_mode': action.view_mode,
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }

        result['domain'] = "[('id','in',[" + ','.join(map(str, self.entrada_ids.ids)) + "])]"
        return result

    @api.multi
    def act_salidas(self):
        action = self.env.ref('grupoalvamex_tools.inventario_salidas_action')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_type': action.view_type,
            'view_mode': action.view_mode,
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }

        result['domain'] = "[('id','in',[" + ','.join(map(str, self.ventas_ids.ids)) + "])]"
        return result

    @api.multi
    def act_devoluciones(self):
        action = self.env.ref('grupoalvamex_tools.inventario_devolucion_action')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_type': action.view_type,
            'view_mode': action.view_mode,
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        result['domain'] = "[('id','in',[" + ','.join(map(str, self.devolucion_ids.ids)) + "])]"
        return result

    @api.depends('s_min','stock_total')
    def stock_fl(self):
        for r in self:
            if r.stock_total < r.s_min:
                r.s_fal = r.s_min - r.stock_total
            else:
                r.s_fal = 0
            #r.s_fal = r.s_min - r.info
            # if r.stock_total < r.s_min:
            #     r.s_fal = r.stock_total - r.s_min
            # if r.stock_total >= r.s_min:
            #     r.s_fal = 0

    # SUMA LAS ENTRADAS
    @api.multi
    def suma_entradas(self):
        for r in self:
            entradas = self.env['inventario.entradas'].search([('entrada_id','=', r.id)])
            suma_stock = 0
            if entradas is not None:
                for rec in entradas:
                    suma_stock += rec.entrada_stock
                r.stock = suma_stock

        # try:
            
        #     for rec in range(entradas):
        #         if entradas > 0:
        #             self.stock = rec.entradas + self.stock
        #         else:
        #             self.stock = 0
        # except ValueError:
        #     return None

    # SUMA DEVOLUCIONES
    @api.multi
    def suma_devoluciones(self):
        for r in self:
            devolucion = self.env['inventario.devoluciones'].search([('devolucion_id','=', r.id)])
            suma_dev = 0
            if devolucion is not None:
                for rec in devolucion:
                    suma_dev = suma_dev + rec.devolucion_stock
                r.devoluciones = suma_dev

    @api.multi
    def suma_ventas(self):        
        for r in self:
            orden_pv = self.env['ventas.produccion'].search([('estado', '=', 'final'), ('sucursal', '=', r.sucursal.id)])
            i = 0
            suma_pv = 0
            for pv in orden_pv:
                for venta in pv.ventas_id:#campo many2many
                    venta_lines = self.env['sale.order.line'].search([('order_id', '=', venta.id),('product_id', '=', r.name.id)])
                    for rec in venta_lines:
                        suma_pv += rec.product_uom_qty
                    r.ventas = suma_pv
                    

    @api.multi
    def actualizar_ventas(self):        
        for r in self:
            r.ventas_ids = False
            orden_pv = self.env['ventas.produccion'].search([('estado', '=', 'final'), ('sucursal', '=', r.sucursal.id)])
            for pv in orden_pv:
                for venta in pv.ventas_id:
                    venta_lines = self.env['sale.order.line'].search([('order_id', '=', venta.id),('product_id', '=', r.name.id)])
                    for rec in venta_lines:
                        r.write({'ventas_ids':[(4, rec.id)]})


    @api.depends('stock_total')
    def total_info(self):
        for r in self:
            if r.stock_total < 1:
                r.info = r.s_min + r.stock_total
                #r.mensaje = _('Usando el Stock Minimo')
                #if r.info < 1:
                    #r.mensaje = _('Sin Stock')
            else:
                r.info = r.s_min
                r.mensaje = False

    @api.multi
    @api.depends('stock','ventas','devoluciones')
    def stock_totales(self):
        for r in self:
            r.stock_total = r.stock - r.ventas - r.devoluciones    

    @api.multi
    def registrar_entrada(self):
        return{
            'name': "Registrar Entrada",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_name': 'form',
            'res_model': 'inventario.entradas',
            'context': {'default_entrada_id': self.id},
            'target': 'new'
        }

    @api.multi
    def registrar_devolucion(self):
        return{
            'name': "Registrar Devolucion",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_name': 'form',
            'res_model': 'inventario.devoluciones',
            'context': {'default_devolucion_id': self.id},
            'target': 'new'
        }

#TODO: TRABAJANDO
    @api.multi
    def cantidad_producto(self):
        for venta in self.ventas_id:
            venta_or = self.env['sale.order'].search([('id','=', venta.id)])
            venta_lin = self.env['sale.order.line'].search([('order_id','=', venta_or.id)])
            #for lineas in venta_lin:

class InventarioEntradas(models.Model):
    _name = 'inventario.entradas'

    entrada_id = fields.Many2one('ventas.produccion.inventario', string="Entrada")
    entrada_stock = fields.Float(string="Cantidad")
    fecha_entrada = fields.Date(string="Fecha")
    lote = fields.Char(string="Lote")
    nota = fields.Text(string="Nota")

    @api.model
    def create(self, values):
         return super(InventarioEntradas, self).create(values)

    @api.multi
    def save(self):
        """ Used in a wizard-like form view, manual save button when in edit mode """
        return True

class InventarioDevoluciones(models.Model):
    _name = 'inventario.devoluciones'

    devolucion_id = fields.Many2one('ventas.produccion.inventario', string="Entrada")
    transferencia_id = fields.Many2one('stock.picking', string="Transferencia")
    devolucion_stock = fields.Float(string="Cantidad")
    fecha_devolucion = fields.Date(string="Fecha")
    lote = fields.Char(string="Lote")
    nota = fields.Text(string="Nota")

    @api.model
    def create(self, values):
         return super(InventarioDevoluciones, self).create(values)

    @api.multi
    def save(self):
        """ Used in a wizard-like form view, manual save button when in edit mode """
        return True

    @api.multi
    @api.onchange('transferencia_id')
    def cantidad_devolucion(self):
        cantidad = 0
        producto = self.env['stock.pack.operation'].search([('picking_id','=',self.transferencia_id.id),('product_id','=',self.devolucion_id.name.id)])
        for p in producto:
            cantidad = cantidad + p.qty_done
        self.devolucion_stock = cantidad

        

# VENDEDORES
class vendedoress(models.Model):
    _name = 'vendedores.ventas'

    name = fields.Char(string="Nombre")
    tel = fields.Integer(string="Numero de Celular")
    correo = fields.Char(string="Correo Electronico")
    imagen = fields.Binary(string="Imagen", attachment=True)

class ventas_vendedores(models.Model):
    _inherit = 'sale.order'

    vendedores = fields.Many2one('vendedores.ventas', string="Vendedor")
    es_promocion = fields.Boolean(string="Promocion")


class clientes_vendedores(models.Model):
    _inherit = 'res.partner'

    x_vendedores = fields.Many2one('vendedores.ventas', string="Vendedor Asignado")
