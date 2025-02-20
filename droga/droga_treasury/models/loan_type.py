from odoo import api, fields, models

class AccountLoanType(models.Model):
    _name = "account.loan.type"
    _description = "This model is used to catagoraize difrent type of loan"

    name=fields.Char('Loan Type', required=True)
    isinterest= fields.Boolean(string="Compound Interest?")
    
class AccountLoanInt(models.Model):
    _name = "account.loan.int"
    _description = "This model is used to catagoraize difrent type of loan"
 
    daily_interest_amount=fields.Float('Interest Amount',readonly=True,digits=(12, 15))
    daily_penality_amount=fields.Float('Penalty Amount',readonly=True,digits=(12, 15))
    value_date= fields.Date(string="Value Date",readonly=True)
    acount_loan_id = fields.Many2one(comodel_name='account.loan', string="Parent ID")
    daily_penality_rate=fields.Float('Daily Penalty Rate',readonly=True,digits=(12, 15) )
    daily_interest_rate=fields.Float('Daily Penalty Rate',readonly=True,digits=(12, 15) )
    daily_interest_total=fields.Float('Daily Interest  Total',readonly=True,digits=(12, 15),compute='_compute_interest_toatal')
    posted=fields.Boolean(string="Posted?")
    payied=fields.Boolean(string="Payied?")
    calculate=fields.Boolean(string="Posted?")

    @api.depends("daily_interest_amount","daily_penality_amount")
    def _compute_interest_toatal(self):
        for record in self:
            record.daily_interest_total = record.daily_interest_amount+record.daily_penality_amount
    @api.model
    def write(self, values):
        result = super(AccountLoanInt, self).write(values)
        return result

    @api.model
    def create(self, values):
        return super(AccountLoanInt, self).create(values)