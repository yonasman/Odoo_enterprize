


from odoo import _, api, fields, models
from odoo import models, fields, tools
class AccountLoanDailyReport(models.Model):

    _inherit = 'account.loan'
    _name="account.loan.report"
    _description = "Loanreport "
    
    daily_report_ids = fields.One2many(
        'droga.loan.daily.report','acount_loan_id' )
 
class LoanDailyReport(models.Model):

    _name = 'droga.loan.daily.report'
    _description = 'Report that show loan daily report'
    _auto = False

    description = fields.Text('Description')
    interst_payment =  fields.Float('Interest Payment')
    daily_interest_amount = fields.Float('Interest')
    principal_repayment = fields.Float('repayment')
    #Outstanding_balance = fields.Float('Out Standing Balance')
    value_date = fields.Date('value date')
    date = fields.Date('date')
    
    pdate = fields.Date('Payment Date')
    receipt = fields.Float('Receipt')
    #customer_status = fields.Char('Customer Status')
    daily_penality_amount=fields.Float('Penalty')
    interest_cumulative_balance = fields.Float('interest Cumulative')
    total_outstanding_balnce = fields.Float('total_outstanding_balnce')
    acount_loan_id= fields.Many2one('account.loan')
    is_penality=fields.Float('Penality')
    

    
   

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table,
                                                                       """ select row_number()over() as id,a.id as identifier,a.id as acount_loan_id,d.value_date,c.value_date as date,b.value_date as date1,'' as description,c.receipt,b.value_date as payment_date,e.principal_repayment,'' as cumulative_balance,
d.daily_interest_amount,d.daily_penality_amount,e.is_interest as interst_payment,'' as interest_cumulative_balance,'' as total_outstanding_balnce,e.value_date as pdate,e.is_penality

 from account_loan a 
LEFT join account_loan_repayment b on a.id=b.acount_loan_id
LEFT join account_loan_repayment_detail e on b.id=e.acount_loan_id
LEFT join account_loan_receipt c on a.id=c.acount_loan_id
LEFT join account_loan_int d on a.id=d.acount_loan_id

order by value_date
 """))