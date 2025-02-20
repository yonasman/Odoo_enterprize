from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountLoanReceipt(models.Model):
    _name = 'account.loan.receipt'
    
    receipt=fields.Float('Receipt')
    cumulative_total = fields.Float(string="Tota")
    value_date= fields.Date(string="Date")
    acount_loan_id = fields.Many2one(comodel_name='account.loan', string="Parent ID")
    posted=fields.Boolean(string="Posted?")
    reference=fields.Char(string='Reference',required=True)
    desc=fields.Char(string='Description',)
    post=fields.Many2one(string='Account Move',comodel_name='account.move')
   

    @api.constrains('value_date')
    def _check_date(self):
        for payment in self:
            #if isinstance(record.id, models.NewId):
            cu_payment = self.env['account.loan.repayment'].search([('value_date', '>', payment.value_date),('acount_loan_id','=',payment.acount_loan_id.id)])
            current_date=datetime.today()
            cday = current_date.date()

            ##if cu_payment:
                ##raise ValidationError("The Value Date cannot be set in the past of The Previous record Value Date")
              
            if payment.value_date>cday:
                raise ValidationError("The Value Date cannot be set in the Future")
              
    def compute_postt(self):
        for record in self:
            current_date = datetime.today()

            cday = current_date.date()
            pday=cday
            t=0
            acount_recipt = self.env['account.loan'].search([('id', '=', record.acount_loan_id.id)])
              
            journal=record.acount_loan_id.account_jornal.id
            account_bank=record.acount_loan_id.account_bank.id
            account_disbursement=record.acount_loan_id.disbursement.id
            accrued_interest_payable=record.acount_loan_id.accrued_interest_payable.id
            lines_vals_list = []

            if  record.value_date:
                pday=record.value_date
            receipt = self.env['account.move'].create(
                                    {'date':pday,'journal_id':journal
                                    ,'ref':record.reference,
                                     })                                    
            if receipt and not record.post:
                t=receipt.id
                lines_vals_list.append({
                    'move_id': t,                   
                    'credit':record.receipt,
                    'account_id': account_disbursement                   
                 })
                
                lines_vals_list.append({  
                    'move_id': t,
                    'debit':record.receipt,
                    'account_id': account_bank 
                 })
                self.env['account.move.line'].create(lines_vals_list)
                record.post=t

    @api.model
    def write(self, values):
        result = super(AccountLoanReceipt, self).write(values)
        return result

    @api.model
    def create(self, values):
        return super(AccountLoanReceipt, self).create(values)