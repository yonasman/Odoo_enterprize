from odoo import models, fields

class RegisteredProduct(models.Model):
    _name = 'registered.product'
    _description = 'Registered Product'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    company = fields.Char(string='Company')
    product = fields.Many2many('product.product',string='List of Registered Product')

    eris_no = fields.Char(string='eRIS No')
    debit_note_request = fields.Date(string='Debit Note Request')
    actual_sample = fields.Char(string='Actual Sample and Others')
    batch_number = fields.Char(string='Batch Number')
    date_of_submission = fields.Date(string='Date of Submission')

    payment_details = fields.One2many('registered.product.detail','header', string='Payment Details')





