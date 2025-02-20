from odoo import models, fields, api


class droga_tender_settings_type_or_item(models.Model):
    _name = 'droga.tender.settings.type.item'

    _rec_name = "type_or_item_name"
    type_or_item_name = fields.Char("Type or item name",required=True)
    type_or_item_descr = fields.Char("Type or item description",required=True)
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')],required=True,default='Active')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
