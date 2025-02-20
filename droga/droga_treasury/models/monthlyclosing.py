from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import fields, models


class DrogaMonthlyclose(models.Model):

    _name = 'droga.monthly.close'
    _description = ''

    closing_day = fields.Date(string='Closing Day',readonly=False)
    starting_day= fields.Date(string='Starting Day',readonly=False)
    et_year=fields.Integer(string="Ethiopian Year",readonly=False)
    Principal_payment=fields.Float(string='Principal Payment',readonly=False)
    Interest_payment=fields.Float(string='Interest Payment',readonly=False)
    interest=fields.Float(string='Interest',readonly=False)
    penality=fields.Float(string='Penalty',readonly=False)
    recipt=fields.Float  (string='Recipt',readonly=False)
   # end_day=fields.Date("Closing Day",compute="_compute_start_field")
    post=fields.Many2one(string='Account Move',comodel_name='account.move')
   
    name= fields.Char(string="Month",readonly=False)
    acount_monthly_closing_id = fields.Many2one(comodel_name='account.loan', string="Bank") 
    _sql_constraints = [ ('unique_closing', 'unique(et_year, name,acount_monthly_closing_id)', 'Cannot Use one tr')	]
    
    # @api.depends('closing_day')
    def compute_post(self):
        for record in self:
            current_date = datetime.today()

            cday = current_date.date()
            pday=cday
            t=0
            acount_recipt = self.env['account.loan'].search([('id', '=', record.acount_monthly_closing_id.id)])
              
            journal=record.acount_monthly_closing_id.account_jornal_inte.id
            account_penality=record.acount_monthly_closing_id.account_penality.id
            account_interest=record.acount_monthly_closing_id.account_interest.id
            accrued_interest_payable=record.acount_monthly_closing_id.accrued_interest_payable.id
            lines_vals_list = []

            if  record.closing_day:
                pday=record.closing_day-relativedelta(days=-1)
            penality = self.env['account.move'].create(
                                    {'date':pday,'journal_id':journal
                                     })                                    
            if penality and not record.post:
                t=penality.id
                lines_vals_list.append({
                    'move_id': t,                   
                    'credit':record.interest,
                    'account_id': account_penality                   
                 })
                lines_vals_list.append({
                    'move_id': t,                   
                    'credit':record.penality,
                    'account_id': account_interest                   
                 })
                lines_vals_list.append({  
                    'move_id': t,
                    'debit':record.penality+record.interest,
                    'account_id': accrued_interest_payable 
                 })
                self.env['account.move.line'].create(lines_vals_list)
                record.post=t
            else:
                return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'message': 'Requested foreign currency is not approved ',
                                'type': 'danger',
                                'sticky': False
                            }
                        }

                    
               
               