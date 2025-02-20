import calendar

from odoo import models, fields, api
from odoo.http import request


class droga_crm_grade_vs_schedule(models.Model):
    _name='droga.crm.grade.vs.schedule.view'
    _auto = False

    userid=fields.Char('User ID')
    user_id = fields.Char('User ID')
    city_descr=fields.Char('City description')
    month=fields.Char('Month')
    month_des = fields.Char('Month')
    date_from=fields.Date('Date from')
    date_to = fields.Date('Date to')
    year=fields.Char('Year')
    state = fields.Char('State')
    cust_name = fields.Char('Customer name')
    visit_header_id = fields.Integer('Visit header id')
    grade = fields.Char('Grade')
    required_visits = fields.Integer('Required visits')
    planned_visits = fields.Integer('Planned visits')
    required_vs_planned=fields.Char('Req. vs plan.',compute='_compute_diff')
    required_vs_planned_status=fields.Char(compute='_compute_diff')
    customer_type=fields.Char('Organization type')
    diff=fields.Integer('Req. vs plan.')
    cust_type = fields.Char('Customer type')
    cust_id=fields.Integer('Customer ID')
    plan_descr=fields.Char('Plan description',compute='_get_plan_description')
    pr_sales=fields.Char('User ID')

    def _get_pr_sales_logged(self):
        if not request:
            return False
        ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
        return False if len(ses) == 0 else ses[0].pro_id[0].p_name

    pr_sales_logged = fields.Char(string="Logged user",
                                      default=_get_pr_sales_logged)

    @api.depends('pr_sales_logged')
    def _is_record_owner(self):
        for rec in self:
            if rec.pr_sales == rec.pr_sales_logged:
                rec.is_record_owner = True
            else:
                rec.is_record_owner = False

    is_record_owner = fields.Boolean('Show plan', store=False, compute="_is_record_owner", search="_search_field")
    def _search_field(self, operator, value):
        if operator=='=':
            ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
            if len(ses)==0:
                return [('id','in',[])]
            else:
                is_rec_owner=self.env['droga.crm.grade.vs.schedule.view'].sudo().search([('pr_sales','=',ses[0].pro_id[0]['p_name'])])
                return [('id', 'in', [x.id for x in is_rec_owner] if is_rec_owner else False)]
        else:
            return [('id','in',[])]

    def _get_plan_description(self):
        for rec in self:
            rec.plan_descr=rec.userid+' - '+calendar.month_name[int(rec.month)]+', '+rec.year
    def _compute_diff(self):
        for rec in self:
            rec.required_vs_planned=str(rec.planned_visits-rec.required_visits)
            if rec.planned_visits-rec.required_visits==0:
                rec.required_vs_planned_status='equal'
            elif rec.planned_visits-rec.required_visits>0:
                rec.required_vs_planned_status = 'greater'
            else:
                rec.required_vs_planned_status='less_than'


    def init(self):
        self._cr.execute(""" 
           create or replace view droga_crm_grade_vs_schedule_view as 
           (
                select row_number() over () as id,g.* from (
                (select z.userid,y.city_descr,z.month,z.year,z.state,y.name as cust_name,z.id as visit_header_id,y.grade,y.visit_times_per_month as required_visits,(select count(m.*) from droga_customer_visit_detail m where m.visit_header=z.id and m.visit_client=y.id) as planned_visits,y.full_name as customer_type,y.cust_type,y.id as cust_id,z.user_id,(select count(m.*) from droga_customer_visit_detail m where m.visit_header=z.id and m.visit_client=y.id)-y.visit_times_per_month as diff,z.date_from as date_from,z.date_to as date_to,TO_CHAR(TO_TIMESTAMP (z.month::text, 'MM'), 'Month') as month_des,(select y.p_name from droga_pro_sales_master y where y.id=z.pr_sales) as pr_sales from droga_customer_visit_header z join 
                (select a.name,b.grade,b.visit_times_per_month,c.full_name,d.city_descr,a.city_name,'Customer' as cust_type,a.id,a.company_id from res_partner a left join droga_cust_grade b on a.cust_grade=b.id left join droga_cust_type c on a.cust_type_ext=c.id left join droga_crm_settings_city d on a.city_name=d.id where a.is_company=true and a.city_name is not null) y on 1=1 limit 1000)
                union
                (select z.userid,y.city_descr,z.month,z.year,z.state,y.contact_name as cust_name,z.id as visit_header_id,y.grade,y.visit_times_per_month as required_visits,(select count(m.*) from droga_crm_contacts_schedule m where m.visits_header=z.id and m.contact_custom=y.id) as planned_visits,y.full_name as customer_type,y.cust_type,y.id as cust_id,z.user_id,(select count(m.*) from droga_crm_contacts_schedule m where m.visits_header=z.id and m.contact_custom=y.id)-y.visit_times_per_month as diff,z.date_from as date_from,z.date_to as date_to,TO_CHAR(TO_TIMESTAMP (z.month::text, 'MM'), 'Month') as month_des,(select y.p_name from droga_pro_sales_master y where y.id=z.pr_sales) as pr_sales from droga_customer_visit_header z join 
                (select a.parent_name||' - '||a.contact_name as contact_name,b.grade,b.visit_times_per_month,c.full_name,d.city_descr,a.contact_area,'Contact' as cust_type,a.id,a.company_id from droga_crm_contacts a left join droga_cust_grade b on a.cont_grade=b.id left join droga_cust_type c on a.contact_type=c.id left join droga_crm_settings_city d on a.contact_area=d.id where a.contact_area is not null) y on 1=1 limit 1000)) g 
           ) 
         """)

