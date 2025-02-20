import calendar

from odoo import models, fields, api
from odoo.http import request

class droga_crm_grade_vs_schedule(models.TransientModel):
    _name='droga.crm.grade.vs.schedule.trans'

    month=fields.Char('Month')
    month_des = fields.Char('Month')
    year=fields.Char('Year')
    state = fields.Char('State')
    cust_name = fields.Char('Customer name')
    visit_header_id = fields.Many2one('droga.customer.visit.header')
    grade = fields.Char('Grade')
    required_visits = fields.Integer('Required visits')
    planned_visits = fields.Integer('Planned visits')
    planned_visits_all = fields.Integer('Planned visits everyone')
    customer_type=fields.Char('Organization type')
    cust_type = fields.Char('Customer type')
    cust_id=fields.Integer('Customer ID')
    diff = fields.Integer('Req. vs plan.')

    date_from = fields.Date('Date from',related='visit_header_id.date_from')
    date_to = fields.Date('Date to',related='visit_header_id.date_to')
    pr_sales = fields.Many2one('droga.pro.sales.master',string='User ID',related='visit_header_id.pr_sales')

    required_vs_planned = fields.Char('Req. vs plan.', compute='_compute_diff')
    required_vs_planned_status = fields.Char(compute='_compute_diff')
    plan_descr=fields.Char('Plan description',compute='_get_plan_description')

    def _get_plan_description(self):
        for rec in self:
            rec.plan_descr=rec.userid+' - '+calendar.month_name[int(rec.month)]+', '+rec.year
    def _compute_diff(self):
        for rec in self:
            rec.required_vs_planned=str(rec.planned_visits_all-rec.required_visits)
            if rec.planned_visits_all-rec.required_visits==0:
                rec.required_vs_planned_status='equal'
            elif rec.planned_visits_all-rec.required_visits>0:
                rec.required_vs_planned_status = 'greater'
            else:
                rec.required_vs_planned_status='less_than'


