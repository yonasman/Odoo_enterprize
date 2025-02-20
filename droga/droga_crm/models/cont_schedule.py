from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.http import request


class contacts_schedule(models.Model):
    _name='droga.crm.contacts.schedule'

    contact_custom=fields.Many2one('droga.crm.contacts',string='Contact')
    phone_no=fields.Char(related='contact_custom.mobile')
    sales_close_descr=fields.Char(string='Sales closed?')
    sales_avail=fields.Boolean('Sales available?',default=False)
    sales_closed = fields.Boolean('Sales Closed?', default=False)
    co_travel_crm = fields.Many2many('droga.pro.sales.master', string='Co-travelers')
    #leads=fields.Many2one('crm.lead','contacts_schedule')
    visits=fields.Many2one('droga.customer.visit.detail','contacts_schedule')
    visits_header = fields.Many2one(related='visits.visit_header',store=True)
    cust=fields.Many2one('res.partner',related='visits.visit_client')
    #custlead = fields.Many2one('res.partner', related='leads.partner_id')
    core_products = fields.Many2many('product.template')

    @api.model
    def create(self, vals_list):
        if len(self.env['droga.crm.contacts.schedule'].search(
                [('contact_custom', '=', vals_list['contact_custom']), ('visits', '=', vals_list['visits'])])) > 0:
            raise ValidationError("Visit with the same customer/client/date already exists.!")
        return super().create(vals_list)

class lead_ordred_products(models.Model):
    _name='droga.lead.ordered.products'
    leads=fields.Many2one('crm.lead')
    prod=fields.Many2one('product.template',string='Product')
    qty=fields.Float('Quantity')

