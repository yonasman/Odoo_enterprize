from odoo import models, fields, api

class droga_pharma_referral_reward(models.Model):
    _name = 'droga.pharma.referral.reward'

    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    from_amt=fields.Float(string='From amount', tracking=True)
    to_amt = fields.Float(string='To amount', tracking=True)
    points_to_gain = fields.Float(string='Referral points to gain', tracking=True)
    remark=fields.Char('Remark')
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')], required=True, default='Active',
                              tracking=True)