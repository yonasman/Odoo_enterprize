from odoo import models, fields, api
from odoo.http import request

class droga_crm_settings_prod_groups(models.Model):
    _name = 'droga.crm.settings.prod_group'

    _rec_name = "prod_group"
    prod_group = fields.Char("Product group",required=True)
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')],required=True,default='Active')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    parent_group=fields.Many2one('droga.crm.settings.prod_group')
    has_group_access = fields.Boolean('Has CRM product group access', search='_has_group_access',compute='_compute_group')
    def _has_group_access(self, operator, value):
        if not self.env.user.name.upper().startswith('CRM MEDICAL'):
            return [('id', 'in', [x.id for x in self.env['res.partner'].search([(1, '=', 1)])])]
        ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
        if not request or len(ses) == 0:
            return [('id', 'in', [])]
        is_prod_avail = self.env['droga.crm.settings.prod_group'].sudo().search(
            [('id', 'in', ses[0].pro_id[0].p_groups.ids)])
        return [('id', 'in', [x.id for x in is_prod_avail] if is_prod_avail else False)]

    def _compute_group(self):
        if not self.env.user.name.upper().startswith('CRM MEDIC'):
            for rec in self:
                rec.has_group_access = True
        else:
            ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
            if not request or len(ses) == 0:
                for rec in self:
                    rec.has_group_access = False
            is_prod_avail = self.env['droga.crm.settings.prod_group'].sudo().search(
                [('id', 'in', ses[0].pro_id[0].p_groups.ids)])
            for rec in self:
                if rec.id in is_prod_avail:
                    rec.has_group_access=True
                else:
                    rec.has_group_access = False


            for rec in self:
                if rec.city_name in rec.pr_avail_areas:
                    rec.is_cust_available = True
                else:
                    rec.is_cust_available = False
class product_link_group(models.Model):
    _inherit = 'product.category'
    crm_group=fields.Many2one('droga.crm.settings.prod_group')

class droga_product_template(models.Model):
    _inherit = 'product.template'
    crm_group=fields.Many2one('droga.crm.settings.prod_group',string='CRM Product Group',domain=[('status', '=', 'Active')])

    def _is_prod_avail(self):
        for rec in self:
            if rec.crm_group in rec.p_groups:
                rec.is_prod_available = True
            else:
                rec.is_prod_available = False

    is_prod_available = fields.Boolean('Prod available', store=False, compute="_is_prod_avail",
                                   search="_search_prod_avail")

    def _get_groups(self):
        ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
        return False if len(ses) == 0 else ses[0].pro_id[0].p_groups.ids

    pr_avail_groups = fields.Many2many('droga.crm.settings.prod_group', default=_get_groups)

    def _search_prod_avail(self, operator, value):
        ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
        if not request or len(ses) == 0:
            return [('id', 'in', [])]

        if self.env.user.has_group('droga_crm.crm_core_only'):
            is_prod_avail = self.env['product.template'].sudo().search(
                [('is_core_product','=','True'),('crm_group', 'in', ses[0].pro_id[0].p_groups.ids)])
        else:
            is_prod_avail = self.env['product.template'].sudo().search(
                [('crm_group', 'in', ses[0].pro_id[0].p_groups.ids)])

        return [('id', 'in', [x.id for x in is_prod_avail] if is_prod_avail else False)]

    @api.model
    def create(self,vals):
        res=super(droga_product_template, self).create(vals)
        #res.crm_group=res.categ_id.crm_group
        res.crm_group = res.categ_id.crm_group
        return res

class StockQuantityHistoryDisable(models.TransientModel):
    _inherit = 'stock.quantity.history'

    def open_at_date(self):
        pass