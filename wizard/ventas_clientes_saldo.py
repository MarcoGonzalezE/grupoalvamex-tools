from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, ValidationError

class ReporteClientesSaldos(models.TransientModel):
	_name = 'reporte.clientes.saldos'

	fecha_inicio = fields.Date(string="Fecha Inicial")
	fecha_final = fields.Date(string="Fecha Final", default=fields.Datetime.now)
	company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id, required=False, string='Compania')
	


#CONSULTA SQL
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
