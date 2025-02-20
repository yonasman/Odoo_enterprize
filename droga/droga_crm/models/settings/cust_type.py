from odoo import models, fields, api

class customer_type(models.Model):
    _name = 'droga.cust.type'
    _rec_name = 'full_name'
    _order='full_name'
    full_name=fields.Char('Customer type',compute='_get_name',store=True)
    cust_type = fields.Char('Customer type', required=True)
    cust_org_type=fields.Selection([('Government', 'Government'),('NGO', 'NGO'), ('Private', 'Private')], required=True,string='Customer organization type')
    cust_type_descr = fields.Char('Customer type description')
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')], required=True, default='Active')
    @api.depends('cust_type','cust_org_type')
    def _get_name(self):
        for record in self:
            record.full_name=record.cust_org_type+' '+record.cust_type
