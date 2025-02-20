

from odoo import api, fields, models
class AccountLoanRenews(models.Model):
    _name = 'account.loan.renews'
    
    receipt=fields.Float('Receipt')
    cumulative_total = fields.Float(string="Total Receipt")
    value_date= fields.Date(string="Receipt Date")
    acount_loan_id = fields.Many2one(comodel_name='account.loan', string="Parent ID",)

    
    @api.model
    def write(self, values):
        result = super(AccountLoanRenews, self).write(values)
        return result

    @api.model
    def create(self, values):
        return super(AccountLoanRenews, self).create(values)