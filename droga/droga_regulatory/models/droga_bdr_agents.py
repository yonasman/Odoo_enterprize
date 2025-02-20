from odoo import models, fields, api

class droga_bdr_agents(models.Model):
    _name = 'droga.bdr.agents'
    _description = 'Company Information'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'company_name'


    company_name = fields.Char(string='Company Name')
    products_list = fields.Many2many('product.product',string='Products List')
    email = fields.Char(string='Email')
    phone_no = fields.Char(string='Phone Number')
    website = fields.Char(string='Website')
    partnership_status = fields.Selection([('active', 'Active'), ('inactive', 'Inactive'), ('pending', 'Pending')], string='Partnership Status')


