from datetime import datetime, date, time, timedelta
from pydoc import classname
from turtle import write_docstringdict
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


from odoo import api, fields, models

from odoo.tools.convert import RecordDictWrapper


class AccountLoanModifaied(models.Model):
    _inherit = 'account.loan'
    _rec_name='descrip'

    future_payment=fields.Date(string="Next Payments" , readonly=True)
    next_payment_date = fields.Date(string="Payment Date", readonly=True)
    descrip=fields.Char(string="Description",readonly=True, compute="_commpute_description")
    state=fields.Selection([
        ('draft','Draft'),('active','Active'),
            ('overdue', 'Arrears'),
            ('done', 'Closed')],
            string="Status",default='draft', required=True
    )
    principal_recipt = fields.Float( 'Principal Receipt', compute='_compute_principal_interest')
    principal_paied_interest = fields.Float(  compute='_compute_principal_interest',string="Principal interest")
    principal_paied_penality = fields.Float(  compute='_compute_principal_interest', string="Principal penalty")
    principal_paied_payment = fields.Float(  compute='_compute_principal_interest', string="Principal Payment") 
    arrears=fields.Float(  compute='_compute_principal_interest', string="Arrears")
   
 
    @api.depends('loan_repayment_ids','loan_repayment_ids','next_payment_date','future_payment')
    def _compute_principal_interest(self):
        
        for allrecords in self:
            payment=0
            arrears=0
            npayments=0
            if allrecords.state!= 'done':
                state=True
            else:
                state=False
                if allrecords.next_payment_date or allrecords.future_payment:
                    allrecords.next_payment_date = None
                    allrecords.future_payment = None  
            
                
            
            if allrecords.next_payment_date and allrecords.future_payment and allrecords.next_payment_date < allrecords.future_payment:
                payment=allrecords.future_payment.month-allrecords.future_payment.month
                npayments=1+payment/allrecords.payment_month
                arrears=int(npayments)*allrecords.payment
            else:
                arrears=0    
            allrecords.arrears=arrears    
            arecipt=0
            for records in allrecords.loan_receipt_ids:
                arecipt+=records.receipt
            allrecords.principal_recipt=arecipt 
            interest=0
            penality=0
            repayment=0
            for payment in allrecords.loan_repayment_ids:
                for pay_detail in payment.loan_repayment_detail_ids:
                    interest +=pay_detail.is_interest
                    repayment +=pay_detail.principal_repayment
                    penality +=pay_detail.is_penality
            allrecords.principal_paied_interest=interest
            allrecords.principal_paied_penality=penality
            allrecords.principal_paied_payment=repayment
                    
            # arecipt+=records.receipt
            # principal_recipt=arecipt   

    def compute_daily_cron_future_payment(self):
        acount_loandraft = self.env['account.loan'].search(
            [('state','=','draft')])
        for rec in acount_loandraft:
            
            if rec.next_payment_date:
                rec.future_payment= rec.next_payment_date
                rec.state="active"
                rec.isactive=True            

        acount_loan = self.env['account.loan'].search(
            [('isactive', '=', True),('state','!=','done')])

        for record in acount_loan:
            
            current_date = datetime.today().date()
            valuedate=record.next_payment_date
            if record.next_payment_date>current_date:
                record.state="active"
            else:
                payment=self.env['account.loan.repayment'].search(
            [('value_date', '=', record.next_payment_date),('acount_loan_id','=',record.id)]) 
                for pay in payment:
                    payment_date=pay.expected_payment_date+relativedelta(months=record.payment_month)
                    account_schedule=self.env['account.loan.schedule'].search([('acount_loan_id','=',record.id),('payment_date','=',payment_date)])
                    if not account_schedule:
                        account_schedule=self.env['account.loan.renew'].search([('acount_loan_id','=',record.id),('renew_date','=',payment_date)])
                    if account_schedule:
                        record.next_payment_date=payment_date

                
            if not record.future_payment:
                record.future_payment=record.next_payment_date
            elif record.future_payment:
                if record.future_payment<current_date:
                    futurepay=record.future_payment
                    while( futurepay<=current_date):
                        futurepay=futurepay+relativedelta(months=record.payment_month)
                        account_schedule=self.env['account.loan.schedule'].search([('acount_loan_id','=',record.id),('payment_date','=',futurepay)])
                        if not account_schedule:
                            account_schedule=self.env['account.loan.renew'].search([('acount_loan_id','=',record.id),('renew_date','=',futurepay)])
                        if account_schedule:
                            record.future_payment=futurepay#-relativedelta(days=1)
            for paymentws in record.loan_repayment_ids:
                if paymentws.value_date:
                    if not record.next_payment_date:
                        record.next_payment_date=record.payment_start_date
                    elif record.next_payment_date < paymentws.value_date or record.next_payment_date == paymentws.value_date:
                        record.next_payment_date= record.next_payment_date+relativedelta(months=record.payment_month)
            if record.next_payment_date and   record.next_payment_date > current_date:
                record.state="active"  

            if record.next_payment_date:
                record.remaining_days = (
                    record.next_payment_date-current_date)/timedelta(days=1)
                if record.remaining_days <0:
                    record.overdue_days=0-record.remaining_days
                    
                    if record.overdue_days>0 and record.isactive and record.interest_start_date:
                        record.state="overdue"
                else:
                     record.overdue_days=0
                
                if record.overdue_days==0 and record.isactive and record.interest_start_date:
                    record.state="active"    
                            
   
    @api.depends('name')
    def _commpute_description(self):
        for record in self:
            name=""
            if record.name and record.id:
                num=record.id

                string_num=str(num)
                if len(string_num)<2:
                    string_num="0000"+string_num
                elif len(string_num)<3:
                    string_num="000"+string_num
                if len(string_num)<4:
                    string_num="00"+string_num
                if len(string_num)<5:
                    string_num="0"+string_num

                name=record.loan_type.name
                short_name=name[0:3].upper()
                name=short_name+"/"+ record.name.name+ "/"+string_num
            record.descrip=name             


class AccountLoanRepayment(models.Model):
    
    _inherit = 'account.loan.repayment'
    @api.onchange('value_date')
    def _onchange_Next_Date(self):
        for record in self:
            if record.value_date:
                date=record.acount_loan_id.next_payment_date
                term=record.acount_loan_id.payment_month
                next_date= record.expected_payment_date+relativedelta(months=term)
                ids=record.acount_loan_id.id.origin
                account_schedule=self.env['account.loan.schedule'].search([('acount_loan_id','=',ids),('payment_date','=',next_date)])
                if not account_schedule:
                    account_schedule=self.env['account.loan.renew'].search([('acount_loan_id','=',ids),('renew_date','=',next_date)])
                current_date= datetime.today().date()
                if account_schedule:
                   

                    if date< next_date:
                        account=self.env['account.loan'].search([('id','=',ids)])
                        for accounts in account:
                            accounts.next_payment_date=next_date
                            if accounts.next_payment_date and   accounts.next_payment_date > current_date:
                                accounts.state="active"  

                            if accounts.next_payment_date:
                                accounts.remaining_days = (
                                    accounts.next_payment_date-current_date)/timedelta(days=1)
                                if accounts.remaining_days <0:
                                    accounts.overdue_days=0-accounts.remaining_days
                                    
                                    if accounts.overdue_days>0 and accounts.isactive and accounts.interest_start_date:
                                        accounts.state="overdue"
                                else:
                                    accounts.overdue_days=0
                                # if not predone.isactive and predone.interest_start_date and predone.overdue_days>0:
                                #     predone.state="overdue"
                                if accounts.overdue_days==0 and accounts.isactive and accounts.interest_start_date:
                                    accounts.state="active" 


                        
                    