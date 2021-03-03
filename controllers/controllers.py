# -*- coding: utf-8 -*-
from odoo import http

# class PickingAvicampo(http.Controller):
#     @http.route('/picking_avicampo/picking_avicampo/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/picking_avicampo/picking_avicampo/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('picking_avicampo.listing', {
#             'root': '/picking_avicampo/picking_avicampo',
#             'objects': http.request.env['picking_avicampo.picking_avicampo'].search([]),
#         })

#     @http.route('/picking_avicampo/picking_avicampo/objects/<model("picking_avicampo.picking_avicampo"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('picking_avicampo.object', {
#             'object': obj
#         })