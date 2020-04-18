from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, ValidationError


class ReporteClientesSaldos(models.TransientModel):
    _name = 'reporte.clientes.saldos'
    _inherit = 'trial.balance.report.wizard'

    date_from = fields.Date(required=True, string="Fecha Inicial")
    date_to = fields.Date(required=True, string="Fecha Final", default=fields.Datetime.now)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id, required=False,
                                 string='Compania')
    show_partner_details = fields.Boolean(default=True)
    receivable_accounts_only = fields.Boolean(default=True)
    account_ids = fields.Many2many(comodel_name='account.account', compute="_compute_cuentas")
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries')], string='Target Moves', required=True, default='posted')

    @api.multi
    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref(
            'account_financial_report_qweb.action_report_trial_balance')
        vals = action.read()[0]
        context1 = vals.get('context', {})
        if isinstance(context1, basestring):
            context1 = safe_eval(context1)
        model = self.env['report_trial_balance_qweb']
        report = model.create(self._prepare_report_trial_balance())
        report.compute_data_for_report()
        context1['active_id'] = report.id
        context1['active_ids'] = report.ids
        vals['context'] = context1
        return vals


    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        report_type = 'qweb-pdf'
        return self._export(report_type)

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        report_type = 'xlsx'
        return self._export(report_type)



    @api.depends('receivable_accounts_only')
    def _compute_cuentas(self):
            self.account_ids = self.env['account.account'].search([('code', 'like', '105.01'),('internal_type', '=', 'receivable')])

    def _prepare_report_trial_balance(self):
        self.ensure_one()
        return {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'only_posted_moves': self.target_move == 'posted',
            'hide_account_at_0': self.hide_account_at_0,
            'foreign_currency': self.foreign_currency,
            'company_id': self.company_id.id,
            'filter_account_ids': [(6, 0, self.account_ids.ids)],
            'filter_partner_ids': [(6, 0, self.partner_ids.ids)],
            'filter_journal_ids': [(6, 0, self.journal_ids.ids)],
            'fy_start_date': self.fy_start_date,
            'hierarchy_on': self.hierarchy_on,
            'limit_hierarchy_level': self.limit_hierarchy_level,
            'show_hierarchy_level': self.show_hierarchy_level,
            'show_partner_details': self.show_partner_details,
        }

# CONSULTA SQL
# Select rp.name as Cliente,
# CONCAT(aa.code,' ',aa.name) as Cuenta,
# round(sum(ai.amount_total),2) as cargo,
# round((sum(ai.amount_total) - sum(ai.residual)),2) as abono,
# round(((sum(ai.amount_total))-(sum(ai.amount_total) - sum(ai.residual))),2) as saldo_final
# from account_invoice ai
# inner join res_partner rp ON ai.partner_id = rp.id
# inner join account_account aa ON ai.account_id = aa.id
# where rp.customer = 't'
# and ai.journal_id = 1
# and ai.state = 'open'
# group by rp.name, Cuenta
# limit 100

class ReporteProveedoresSaldos(models.TransientModel):
    _name = 'reporte.proveedores.saldos'
    _inherit = 'trial.balance.report.wizard'

    date_from = fields.Date(required=True, string="Fecha Inicial")
    date_to = fields.Date(required=True, string="Fecha Final", default=fields.Datetime.now)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id, required=False, string='Compania')
    show_partner_details = fields.Boolean(default=True)
    receivable_accounts_only = fields.Boolean(default=True)
    account_ids = fields.Many2many(comodel_name='account.account', compute="_compute_cuentas")

    @api.multi
    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref(
            'account_financial_report_qweb.action_report_trial_balance')
        vals = action.read()[0]
        context1 = vals.get('context', {})
        if isinstance(context1, basestring):
            context1 = safe_eval(context1)
        model = self.env['report_trial_balance_qweb']
        report = model.create(self._prepare_report_trial_balance())
        report.compute_data_for_report()
        context1['active_id'] = report.id
        context1['active_ids'] = report.ids
        vals['context'] = context1
        return vals


    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        report_type = 'qweb-pdf'
        return self._export(report_type)

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        report_type = 'xlsx'
        return self._export(report_type)



    @api.depends('receivable_accounts_only')
    def _compute_cuentas(self):
            self.account_ids = self.env['account.account'].search([('code', 'like', '105.01'),('internal_type', '=', 'receivable')])

    def _prepare_report_trial_balance(self):
        self.ensure_one()
        return {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'only_posted_moves': self.target_move == 'posted',
            'hide_account_at_0': self.hide_account_at_0,
            'foreign_currency': self.foreign_currency,
            'company_id': self.company_id.id,
            'filter_account_ids': [(6, 0, self.account_ids.ids)],
            'filter_partner_ids': [(6, 0, self.partner_ids.ids)],
            'filter_journal_ids': [(6, 0, self.journal_ids.ids)],
            'fy_start_date': self.fy_start_date,
            'hierarchy_on': self.hierarchy_on,
            'limit_hierarchy_level': self.limit_hierarchy_level,
            'show_hierarchy_level': self.show_hierarchy_level,
            'show_partner_details': self.show_partner_details,
        }
