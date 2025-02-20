from odoo import models,fields

class droga_export_status(models.Model):
    _name='droga.export.status'
    status_origin_sales = fields.Many2one('sale.order', readonly=True)
    status=fields.Char('Status')
    completed=fields.Boolean('Completed',default=False)
    remark=fields.Char('Remark')

class droga_export_status_list(models.Model):
    _name='droga.export.status.list'
    status_list=fields.Char('Export status')
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')],required=True,default='Active')

class droga_export_cost_types(models.Model):
    _name='droga.export.cost.type'
    _rec_name='type'
    type=fields.Char('Type')
    type_apply=fields.Selection([('Finished', 'Finished'), ('By-product', 'By-product'),('All','All')],required=True)