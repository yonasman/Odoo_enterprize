from odoo import models, fields, api
from odoo.tools.sql import drop_view_if_exists
from datetime import datetime

class TrialBalanceByAnalytics(models.Model):
    _name = 'droga.finance.trial.balance.by.analytics'

    _auto = False
    _order = 'account_id asc'

    id = fields.Integer('Id')
    account_id = fields.Many2one('account.account',string='Account')
    analytic_account_id = fields.Many2one('account.analytic.account',string='Analytic Account')
    company_id = fields.Many2one('res.company',string='Company',default=lambda self: self.env.company.id)
    plan_id = fields.Many2one('account.analytic.plan',string='Analytic Plan')
    date=fields.Date('Date')
    debit=fields.Float('Debit')
    credit=fields.Float('Credit')

    def init(self):
        drop_view_if_exists(self.env.cr, 'droga_finance_trial_balance_by_analytics')
        self.env.cr.execute("""
                               create or replace view droga_finance_trial_balance_by_analytics as (

                                    select row_number()over() as id,aml.account_id,aal.account_id as analytic_account_id,aml.company_id,aml.date,aal.plan_id,sum(aml.debit) as debit,sum(aml.credit) as credit 
                                    from account_move_line aml 
                                    left join account_analytic_line aal on aml.id=aal.move_line_id
                                    where aml.parent_state='posted' and aml.company_id=1
                                    group by aml.account_id,aal.account_id,aml.company_id,aal.plan_id,aml.date

                               )""")


