from odoo import models, fields, api

class droga_pharma_reward_gain(models.Model):
    _name = 'droga.pharma.reward.gain'

    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']

    points_to_gain=fields.Float(string='Points to gain', tracking=True)
    remark = fields.Char('Remark')
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')], required=True, default='Active',
                              tracking=True)
    type=fields.Selection([('Stocked', 'Stocked'), ('Services', 'Services')], required=True, default='Stocked',
                              tracking=True)