from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import ValidationError
from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountLoanRenew(models.Model):
    _name = 'account.loan.renew'
    
    name=fields.Char(string='Extension Reason')
    #payment_date = fields.Date(string="Payment Date")
 
    acount_loan_id = fields.Many2one(comodel_name='account.loan', string="Parent ID") 
    payment_amount=fields.Float(string="Repayment",required=True) 
    anual_interest_rate=fields.Float(string="Anual Interest %",required=True) 
    anual_penality_rate=fields.Float(string="Anual Penalty %",required=True) 
    #payment_range=fields.Integer(string="Period Range in Month")
    addtional_payment=fields.Integer(string="Addtional Loan Period",required=True)
    renew_date=fields.Date(string="Renewed Date",required=True)
    renew_start_date=fields.Date(string="New Calculation Start Date",required=True)
    cumulative_interest  =fields.Float('Cumulative interest',related='acount_loan_id.cumulative_interest',copy=True,store=True)
    cumulative_balance = fields.Float(related='acount_loan_id.cumulative_balance',string="Cumulative Principal Balance",copy=True,store=True)
    payment_month=fields.Integer('Payment Ranage in Month',related='acount_loan_id.payment_month',copy=True,store=True,)
    
    @api.constrains('renew_date','renew_start_date')
    def _check_date(self):
        for loans in self:
            current_date=datetime.today()
            cday = current_date.date()
            #if isinstance(record.id, models.NewId):
            if loans.renew_start_date<loans.acount_loan_id.contract_date:

                raise ValidationError("Check The Renew Start Date and Contract_date")
            # if loans.renew_date>loans.acount_loan_id.contract_date:

            #     raise ValidationError("Check The Renew Date")
            if loans.anual_interest_rate<=0  or loans.payment_amount<=0:
                raise ValidationError("Check The Interest rate and payment amount")
            if not loans.name:
                raise ValidationError("Please enter the Extension Reason")
    def write(self, values):
        result = super(AccountLoanRenew, self).write(values)
        return result

    @api.model
    def create(self, values):
        return super(AccountLoanRenew, self).create(values)

class AccountLoanRenewSchedule(models.Model):
    _name = 'account.loan.renew.schedule'
    
    name=fields.Char(string='Peyment term')
    payment_date = fields.Date(string="Payment Date")
 
    acount_loan_id = fields.Many2one(comodel_name='account.loan', string="Parent ID") 
    payment_amount=fields.Float(string="Payment") 
    interest=fields.Float(string="Interest") 
    prencipal=fields.Float(string="Prencipal")
    balance=fields.Float(string="Remaining Balance")
    
    @api.depends("payment_date")
    def _compute_penalitydaily(self):
        schedule = self.env['account.loan.schedule'].search(
            [('name', '!=', False)])              
        for predone in schedule:
            loan = self.env['account.loan.repayment'].create({'expected_payment_date': predone.payment_date, 'payment_term': predone.name,
                 })
    @api.model
    def write(self, values):
        result = super(AccountLoanRenewSchedule, self).write(values)
        return result

    @api.model
    def create(self, values):
        return super(AccountLoanRenewSchedule, self).create(values)

# class AccountLoanRenews(models.AbstractModel):
#     _name = 'account.loan.renews'
#     _description = ''
   
#     payment_amount=fields.Float(string="Payment",required=True) 
#     anual_interest_rate=fields.Float(string="Anual Interest %",required=True) 
#     anual_penality_rate=fields.Float(string="Anual Penality %",required=True) 
#     #payment_range=fields.Integer(string="Period Range in Month")

#     addtional_payment=fields.Integer(string="Addtional No. Payments",required=True)
#     renew_date=fields.Date(string="Renewed Date",required=True)
#     renew_start_date=fields.Date(string="New Calculation Start Date",required=True)
#     # account_loan_id = fields.Many2one(
#     #     'account.loan',
    #     string='Account Loan',
    #     ) 