from odoo import models, fields, api


class droga_tender_settings_submission_place(models.Model):
    _name = 'droga.tender.settings.submission.place'

    _rec_name = "submission_place_name"
    submission_place_name = fields.Char("Submission place Name",required=True)
    submission_place_descr = fields.Char("Submission place Description",required=True)
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')],required=True,default='Active')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)


