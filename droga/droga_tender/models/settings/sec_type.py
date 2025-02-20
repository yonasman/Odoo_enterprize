from odoo import models, fields, api

class droga_tender_settings_security_type(models.Model):
    _name = 'droga.tender.settings.sec.type'

    _rec_name = "sec_type_name"
    sec_type_name = fields.Char("Security type name",required=True)
    sec_type_descr = fields.Char("Security type description",required=True)
    exp_status = fields.Selection([('Expire', 'Expire'), ('No Expire', 'No Expire')],string="Expiry status", required=True, default='Expire')
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')],required=True,default='Active')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)



