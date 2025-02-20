from odoo import models, fields, api


class droga_crm_settings_region(models.Model):
    _name = 'droga.crm.settings.region'

    _rec_name = "region_name"
    child_id = fields.One2many('droga.crm.settings.city','parent_id',required=True)
    region_name = fields.Char("Region name",required=True)
    region_descr = fields.Char("Region description",required=True)
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')],required=True,default='Active')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)


