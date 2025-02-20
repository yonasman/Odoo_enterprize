from odoo import models, fields, api

class droga_tender_settings_media(models.Model):
    _name = 'droga.tender.settings.media'

    _rec_name="media_name"
    media_name = fields.Char("Media Name",required=True)
    media_descr=fields.Char("Media Description",required=True)
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')],required=True,default='Active')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    