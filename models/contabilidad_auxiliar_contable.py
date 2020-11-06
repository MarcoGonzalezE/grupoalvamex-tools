from openerp import api, fields, models, _ 

class AccountAccountLines(models.Model):
    _inherit = "account.account_lines"

    name = fields.Char()
    check_number = fields.Char(string="Numero de Cheque", compute="fnNumeroCheque")

    @api.depends('name')
    def fnNumeroCheque(self):
        for r in self:
        	pagos = self.env['account.payment'].search([('name','=',r.name)])
        	if pagos:
        		r.check_number = pagos.check_number
        	else:
        		r.check_number = False