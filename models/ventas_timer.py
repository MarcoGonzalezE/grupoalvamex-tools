# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api,_
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    duration = fields.Float(
        'Duracion Real', compute='_compute_duration',
        readonly=True, store=True)
    time_ids = fields.One2many(
        'sale.order.times', 'sale_order_id')
    duration_expected = fields.Float(
        'Duracion esperada')
    is_user_working = fields.Boolean(
        'Is Current User Working', compute='_compute_is_user_working',
        help="Technical field indicating whether the current user is working. ")

    def _compute_is_user_working(self):
        """ Checks whether the current user is working """
        for order in self:
            if order.time_ids.filtered(lambda x: (x.user_id.id == self.env.user.id) and (not x.date_end)):
                order.is_user_working = True
            else:
                order.is_user_working = False

    @api.one
    @api.depends('time_ids.duration')
    def _compute_duration(self):
        for each in self:
            each.duration = sum(each.time_ids.mapped('duration'))

    @api.multi
    def button_start(self):
        timeline = self.env['sale.order.times']
        for saleorder in self:
            timeline.create({
                'sale_order_id': saleorder.id,
                'description': _('Time Tracking: ') + self.env.user.name,
                'date_start': datetime.now(),
                'user_id': self.env.user.id
            })

    @api.multi
    def button_finish(self):
        self.ensure_one()
        self.end_all()
        return self.write({'date_finished': fields.Datetime.now()})

    @api.multi
    def end_all(self):
        return self.end_previous(doall=True)

    @api.multi
    def end_previous(self, doall=False):
        """
        @param: doall:  This will close all open time lines on the open work orders when doall = True, otherwise
        only the one of the current user
        """
        # TDE CLEANME
        timeline_obj = self.env['sale.order.times']
        domain = [('sale_order_id', 'in', self.ids), ('date_end', '=', False)]
        if not doall:
            domain.append(('user_id', '=', self.env.user.id))
        not_productive_timelines = timeline_obj.browse()
        for timeline in timeline_obj.search(domain, limit=None if doall else 1):
            wo = timeline.sale_order_id
            if wo.duration_expected <= wo.duration:
                timeline.write({'date_end': fields.Datetime.now()})
            else:
                maxdate = fields.Datetime.from_string(timeline.date_start) + relativedelta(
                    minutes=wo.duration_expected - wo.duration)
                enddate = datetime.now()
                if maxdate > enddate:
                    timeline.write({'date_end': enddate})
                else:
                    timeline.write({'date_end': maxdate})
                    not_productive_timelines += timeline.copy({'date_start': maxdate, 'date_end': enddate})
        return True


class SaleOrderTimes(models.Model):
    _name = "sale.order.times"
    _description = "Sale order times"
    _order = "id desc"

    sale_order_id = fields.Many2one('sale.order', 'Sale Order')
    user_id = fields.Many2one(
        'res.users', "Usuario",
        default=lambda self: self.env.uid)
    description = fields.Text('Descripcion')
    date_start = fields.Datetime('Fecha de inicio', default=fields.Datetime.now, required=True)
    date_end = fields.Datetime('Fecha finalizacion')
    duration = fields.Float('Duracion', compute='_compute_duration', store=True)

    @api.depends('date_end', 'date_start')
    def _compute_duration(self):
        for blocktime in self:
            if blocktime.date_end:
                diff = fields.Datetime.from_string(blocktime.date_end) - fields.Datetime.from_string(blocktime.date_start)
                blocktime.duration = round(diff.total_seconds() / 60.0, 2)
            else:
                blocktime.duration = 0.0

