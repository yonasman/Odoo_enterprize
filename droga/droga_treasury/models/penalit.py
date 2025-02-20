from odoo import api, fields, models
from odoo.exceptions import ValidationError
class AccountLoanPenalityRange(models.Model):
    _name = 'account.loan.penality.range'
    
    name= fields.Selection( [('upto', 'UPTo'),('morethan', 'Morethan')],string="Range") 
    
    daily_penality_rate=fields.Float(string="Daily Penalty %",required=True,compute="_compute_penalitydaily") 
    anual_penality_rate=fields.Float(string="Anual Penalty %",required=True)
    num_days=fields.Integer(string="Days",required=True)
    acount_loan_penality_id = fields.Many2one(comodel_name='account.loan', string="Parent ID", index=True, ondelete='cascade', required=True)
    
    @api.constrains('renew_date','renew_start_date')
    def _check_date(self):
        for loans in self:
           
            if loans.anual_penality_rate<=0 :
                raise ValidationError("Check The Penalty rate")
            if not loans.name:
                raise ValidationError("Please enter the Range on Penalty")
    @api.depends("anual_penality_rate",'name')
    def _compute_penalitydaily(self):
        for record in self:
            record.daily_penality_rate = record.anual_penality_rate/365
            if record.name=='morethan':
                num_days=0

    
  
        
    @api.model
    def write(self, values):
        result = super(AccountLoanPenalityRange, self).write(values)
        return result

    @api.model
    def create(self, values):
        return super(AccountLoanPenalityRange, self).create(values)