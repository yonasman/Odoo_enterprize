from odoo import models, fields, api
from odoo.http import request


class droga_crm_settings_city(models.Model):
    _name = 'droga.crm.settings.city'

    _rec_name = "city_name"
    parent_id=fields.Many2one('droga.crm.settings.region','Region',required=True)
    child_id = fields.One2many('droga.crm.settings.area', 'parent_id')
    city_name = fields.Char("City/sub-city name",required=True)
    city_descr = fields.Char("City/sub-city description",required=True)
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')],required=True,default='Active')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    city_avail=fields.Boolean(search="_city_avail",compute="is_city_avail")

    def is_city_avail(self):
        ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
        if self.env.user.has_group('droga_crm.crm_cust'):
            for rec in self:
                rec.city_avail = True
        elif not request or len(ses) == 0:
            for rec in self:
                rec.city_avail = False
        else:
            for rec in self:
                if rec.city_name in ses[0].pro_id[0].p_regions.ids:
                    rec.city_avail = True
                else:
                    rec.city_avail = False
    def _city_avail(self, operator, value):
        if self.env.user.has_group('droga_crm.crm_cust'):
            return [('id', 'in', [x.id for x in self.env['droga.crm.settings.city'].search([(1, '=', 1)])])]
        ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
        if not request or len(ses) == 0:
            return [('id', 'in', [])]
        else:
            return [('id', 'in', ses[0].pro_id[0].p_regions.ids)]


    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id, record.parent_id.region_name+'-'+record.city_name))
        return result