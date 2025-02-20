from odoo import fields,models

class points_storage(models.Model):
    _name='droga.pharma.points.earned'

    customer=fields.Many2one('res.partner')
    type= fields.Selection([
        ('Purchase reward', 'Purchase reward'),
        ('Speciality service reward', 'Speciality service reward'),
        ('Referral reward', 'Referral reward'),
        ('Discount for high value purchase','Discount for high value purchase'),
        ('Discount for repeat purchase', 'Discount for repeat purchase'),
        ('Discount for loyal customer', 'Discount for loyal customer'),
        ('Discount for breast feed', 'Discount for breast feed'),
        ('Manual discount', 'Manual discount'),
        ('Discount for health professional', 'Discount for health professional')
    ])
    sales_ref=fields.Many2one('sale.order',string='Sales order')
    earned_date=fields.Date('Date')
    points_earned = fields.Float('Points')

    def open_sales(self):
        return {
            'name': 'Sales order',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'view_id': self.env.ref('droga_pharma.view_order_form_pharma').id,
            'type': 'ir.actions.act_window',

            'res_id': self.sales_ref.id,
        }

