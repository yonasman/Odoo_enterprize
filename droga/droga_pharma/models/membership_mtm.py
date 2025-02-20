from odoo import fields, models, api
from odoo.exceptions import UserError
import datetime

class droga_pharma_membership_status(models.Model):
    _name='droga.pharma.membership'
    parent_customer=fields.Many2one('res.partner', string='Customer Name')
    parent_employee = fields.Many2one('droga.pharma.cust.employees', string='Employee Name')

    prod=fields.Char('Product code')
    prod_descr = fields.Char('Product description')
    sales_ref = fields.Char('Sales reference')
    paid_amount=fields.Float('Paid amount')
    left_amount=fields.Float('Left amount',compute='_get_left_amount')
    def _get_left_amount(self):
        for rec in self:
            rec.left_amount=0
    date_from=fields.Datetime('Date From')
    date_to = fields.Datetime('Date To')
    status=fields.Char(compute='get_status')
    def get_status(self):
        for rec in self:
            if rec.date_to>datetime.datetime.today():
                rec.status='Active'
            else:
                rec.status = 'Closed'

    usages=fields.One2many('droga.pharma.membership.usage','membership')

    def sales_req(self):
        return {
            'name': 'Sales order',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'views': [[self.env.ref('droga_pharma.view_order_tree_pharma_no_invoice').id, 'tree'],
                      [self.env.ref('droga_pharma.view_order_form_pharma').id, 'form']],
            'type': 'ir.actions.act_window',
            'context': {
                'default_membership_origin': self.id,
                'default_partner_id': self.parent_employee.parent_customer.id if self.parent_employee.id else self.parent_customer.id,
                'default_customer_emp':self.parent_employee.id,
                'default_state':'memb',
                'default_order_from':'PH',
                'default_payment_term_id':11
            },
            'domain':
                ([('membership_origin', '=', self.id)])
        }

class droga_pharma_membership_status_usage(models.Model):
    _name='droga.pharma.membership.usage'
    membership=fields.Many2one('droga.pharma.membership')

    sales_ref = fields.Char('Sales reference')
    used_amount=fields.Float('Used amount')
