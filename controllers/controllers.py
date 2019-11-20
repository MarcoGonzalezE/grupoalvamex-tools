# -*- coding: utf-8 -*-
from odoo import http

# class PruebaOdoo(http.Controller):
#     @http.route('/prueba_odoo/prueba_odoo/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/prueba_odoo/prueba_odoo/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('prueba_odoo.listing', {
#             'root': '/prueba_odoo/prueba_odoo',
#             'objects': http.request.env['prueba_odoo.prueba_odoo'].search([]),
#         })

#     @http.route('/prueba_odoo/prueba_odoo/objects/<model("prueba_odoo.prueba_odoo"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('prueba_odoo.object', {
#             'object': obj
#         })