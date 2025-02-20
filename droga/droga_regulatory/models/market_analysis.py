from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools.safe_eval import datetime


class MarketAnalysis(models.Model):
    _name = 'droga.bdr.market.analysis'
    _description = 'Market Analysis'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'local_agent'

    mark_an_number = fields.Char(string='Market Analysis Number', default=lambda self: self.env['ir.sequence'].next_by_code('droga.reg.market.analysis.sequence'), readonly=True)
    header = fields.Many2one('droga.bdr.market.analysis', string="Merge with")
    entries = fields.One2many('droga.bdr.market.analysis', 'header')
    total_price = fields.Float(string='Total Price', compute='_compute_total_sales', readonly=True)
    details = fields.One2many('add.market.sale', 'header', string='Sales')

    local_agent = fields.Char(string='Local Agent')
    manufacturer = fields.Char(string='Manufacturer')
    application_number = fields.Char(string='Application Number')
    generic_name = fields.Char(string='Generic Name')
    brand_name = fields.Char(string='Brand Name')
    country = fields.Char(string='Country')

    unit = fields.Char(string='Unit')
    quantity = fields.Float(string='Quantity', default=1)
    unit_price = fields.Float(string='Unit Price in $', default=1)


    pfi_date = fields.Date(string='Date of PFI', date_format='%m-%d-%Y')
    ip_approval_date = fields.Date(string='Date of IP Approval', date_format='%m-%d-%Y')
    date_sold = fields.Date("Date Recorded", date_format='%d-%m-%Y',default=fields.Date.today())

    product_type = fields.Selection([('medicine', 'Medicine'), ('medical_device', 'Medical Device'), ],
                                    string="Product Type")

    _product_type = fields.Char(string="Product Type")
    pharma_category = fields.Char('Pharmacological Category')

    dosage_form = fields.Char(string="Dosage Form")

    def _compute_total_sales(self):
        for rec in self:
            if rec.unit_price and rec.quantity:
                rec.total_price = rec.unit_price * rec.quantity
            else:
                rec.total_price = 0


class AddSale(models.Model):
    _name = 'add.market.sale'

    header = fields.Many2one('droga.bdr.market.analysis')

    local_agent = fields.Char(string='Local Agent', realted='header.local_agent')
    manufacturer = fields.Char(string='Manufacturer')
    application_number = fields.Char(string='Application Number')
    generic_name = fields.Char(string='Generic Name')
    brand_name = fields.Char(string='Brand Name')

    unit = fields.Char(string='Unit')
    quantity = fields.Float(string='Quantity', default=1)
    unit_price = fields.Float(string='Unit Price in $', default=1)
    total_price = fields.Float(string='Total Price in $', compute='_get_total', readonly=True, store=True)

    pfi_date = fields.Date(string='Date of PFI')
    ip_approval_date = fields.Date(string='Date of IP Approval')
    date_sold = fields.Date("Date Sold")

    product_type = fields.Selection([('medicine', 'Medicine'), ('medical_device', 'Medical Device'), ('unassigned', 'Unassigned')], string="Product Type",required=True)
    pharma_category = fields.Char('Pharmacological Category')

    @api.depends('unit_price', 'quantity')
    def _get_total(self):
        for rec in self:
            rec.total_price = rec.unit_price * rec.quantity
