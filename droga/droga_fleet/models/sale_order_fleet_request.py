from odoo import models,fields,api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    fleet_request=fields.One2many('droga.fleet.request','sale_origin')
    def sale_order_fleet_request(self):
        task_ids=[]
        for lines in self.order_line:
             task_ids.append(
                {'delivered_to': self.partner_id.id, 'resource_name': lines.name,
                        'amount': lines.product_uom_qty})

        request_type = "resource_transportation"
        purpose = "Product Delivery"



        return {
            'type': 'ir.actions.act_window',
            'name': 'Fleet Request',
            'res_model': 'droga.fleet.request',
            'view_mode': 'form',
            'context': {
                'default_request_type': request_type,
                'default_purpose': purpose,
                'default_requested_by': self.env.user.id,
                'default_company': self.env.company.id,
                'default_department': self.env.user.department_id.id,
                'default_date': fields.Datetime.now(),
                'default_sale_origin':self.id,
                'default_task_ids':task_ids
            },
            'domain':([('sale_origin', '=', self.id)]),
            'res_id':self.fleet_request[0].id if self.fleet_request else False
        }

