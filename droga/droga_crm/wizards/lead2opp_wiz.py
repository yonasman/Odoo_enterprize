from odoo import models,fields,api
from odoo.http import request


class lead2opp_inherit(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'
    name = fields.Selection([
        ('convert', 'Convert to opportunity')
    ], 'Conversion Action', readonly=True, compute='_compute_name', store=True, compute_sudo=False)

    action = fields.Selection([
        ('create', 'Create a new customer'),
        ('exist', 'Link to an existing customer'),
        ('nothing', 'Do not link to a customer')
    ], string='Related Customer', compute='_compute_action', readonly=False, store=True, compute_sudo=False)


    def _get_pr_sales_logged(self):
        if not request:
            return False
        ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
        logged_user= False if len(ses) == 0 else ses[0].pro_id[0]
        if logged_user:
            location_pr=self.env['droga.pro.sales.master'].search(['&',('p_regions','in',logged_user.p_regions.ids),('employee_access_users.login','like','crm_sr%')])
            if len(location_pr)>0:
                return location_pr[0].id
            else:
                return False
        else:
            return False

    pr_sales = fields.Many2one('droga.pro.sales.master',domain=(['&',('employee_access_users.login','!=','crm_mr'),('employee_access_users.login','not like','crm_pm%')]), string="Sales rep",
                               default=_get_pr_sales_logged, required=True)
    closed_sales = fields.Boolean('Sales is closed')

    @api.depends('duplicated_lead_ids')
    def _compute_name(self):
        for convert in self:
            if not convert.name:
                convert.name = 'convert'

    @api.depends('lead_id')
    def _compute_action(self):
        for convert in self:
            convert.action = 'exist'

    def _convert_and_allocate(self, leads, user_ids, team_id=False):
        self.ensure_one()

        for lead in leads:
            lead.sudo().write({'pr_sales': self.pr_sales})
            lead.sudo().write({'closed_sales': self.closed_sales})
            lead.sudo().write({'user_id': self.pr_sales.employee_access_users})
            if lead.active and self.action != 'nothing':
                self._convert_handle_partner(
                    lead, self.action, self.partner_id.id or lead.partner_id.id)

            lead.sudo().convert_opportunity(lead.partner_id, user_ids=False, team_id=False)


class lead_ext(models.Model):
    _inherit = 'crm.lead'

    def redirect_lead_opportunity_view(self):
        pass

