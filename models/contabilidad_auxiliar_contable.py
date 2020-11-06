from openerp import api, fields, models, _ 

class AccountAccountLines(models.Model):
    _inherit = "account.account_lines"

    name = fields.Char()
    check_number = fields.Char(string="Numero de Cheque", compute="fnNumeroCheque")

    @api.depends('name')
    def fnNumeroCheque(self):
    	pagos = self.env['account.payment'].search([('name','=',self.name)])
    	if pagos:
    		self.check_number = pagos.check_number
    	else:
    		self.check_number = False