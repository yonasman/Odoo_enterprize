from odoo import models, fields, api


class droga_tender_settings_incoterm(models.Model):
    _name = 'droga.tender.settings.incoterm'

    _rec_name = "incoterm_name"
    incoterm_name = fields.Char("Incoterm Name",required=True)
    incoterm_descr = fields.Char("incoterm Description",required=True)
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')],required=True,default='Active')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)


