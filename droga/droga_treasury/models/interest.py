from odoo import api, fields, models

class AccountLoanInterest(models.Model):
    _name = 'account.loan.interest'
    
   
    daily_interest_amount=fields.Float('Interest Amount',readonly=True,digits=(12, 6))
    daily_penality_amount=fields.Float('Penalty Amount',readonly=True, digits=(12, 6))
    daily_interest_rate=fields.Float('Daily Interest Rate',readonly=True,)
    daily_penality_rate=fields.Float('Daily Penalty Rate',readonly=True, )
    daily_interest_total=fields.Float('Daily Interest  Total',readonly=True,)
 
    #cumulative_interest_total = fields.Float(string="Cumulative Interest",related='acount_loan_id.daily_penalit_rate', readonly=True, store=True,)
    value_date= fields.Date(string="Value Date",readonly=True)
    posted=fields.Boolean(string="Posted?",readonly=True)
    calculate=fields.Boolean(string="Posted?",readonly=True)
    acount_loan_id = fields.Many2one(comodel_name='account.loan', ondelete='cascade', required=True,
                                   copy=True)
                                  


    @api.depends('daily_penality_amount','daily_interest_amount')
    def _compute_daily_interest_total(self):
        for record in self:
   
            record.daily_interest_total = record.daily_interest_amount+record.daily_penality_amount
    
    @api.model
    def write(self, values):
        result = super(AccountLoanInterest, self).write(values)
        return result

    @api.model
    def create(self, values):
        return super(AccountLoanInterest, self).create(values)