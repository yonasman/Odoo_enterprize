from odoo import models, fields, api


class droga_crm_settings_days(models.Model):
    _name = 'droga.crm.settings.day'
    _rec_name = 'day'
    day = fields.Char("Day",required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    def create_days(self):
        self.env['droga.crm.settings.day'].sudo().create({
            'day': 'Monday',
        })
        self.env['droga.crm.settings.day'].sudo().create({
            'day': 'Tuesday',
        })
        self.env['droga.crm.settings.day'].sudo().create({
            'day': 'Wednesday',
        })
        self.env['droga.crm.settings.day'].sudo().create({
            'day': 'Thursday',
        })
        self.env['droga.crm.settings.day'].sudo().create({
            'day': 'Firday',
        })
        self.env['droga.crm.settings.day'].sudo().create({
            'day': 'Saturday',
        })