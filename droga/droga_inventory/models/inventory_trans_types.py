from odoo import models,fields

class inventory_trans_types(models.Model):
    _rec_name = 'type'
    _name='droga.inventory.transaction.types'
    from_loc=fields.Selection([('customer','Customer location'),('production','Production'),('view','View'),('transit','Transit location'),
                               ('supplier','Vendor location'),('inventory','Inventory loss'),('internal','Internal location')])
    qty_flag=fields.Selection([('-1','-1'),('1','1')])
    from_con_type = fields.Selection([
        ('CONI', 'Consignment customer location'),
        ('CONR', 'Consignment vendor location'),
        ('SIF', 'Free sample'),
        ('SIR', 'Sample issue to be returned'),
        ('SAR', 'Sample being returned'),
        ('DIL', 'Dispatch location'),
        ('ATL', 'Asset transit location'),
        ('SAP', 'Sales placement location'),
        ('SRL', 'Inter-store receive transit location'),
        ('INC', 'Internal consumption'),
        ('SUBL', 'Cleaning unit location')
    ], string='Cons/sample Type from')
    to_con_type = fields.Selection([
        ('CONI', 'Consignment customer location'),
        ('CONR', 'Consignment vendor location'),
        ('SIF', 'Free sample'),
        ('SIR', 'Sample issue to be returned'),
        ('SAR', 'Sample being returned'),
        ('DIL', 'Dispatch location'),
        ('ATL', 'Asset transit location'),
        ('SAP', 'Sales placement location'),
        ('SRL', 'Inter-store receive transit location'),
        ('INC', 'Internal consumption'),
        ('SUBL', 'Cleaning unit location')
    ], string='Cons/sample Type to')
    to_loc=fields.Selection([('customer','Customer location'),('production','Production'),('view','View'),('transit','Transit location'),
                               ('supplier','Vendor location'),('inventory','Inventory loss'),('internal','Internal location')])
    type=fields.Char(string='Transaction type')
    contra_account=fields.Many2one('account.account')
    summary_detail=fields.Selection([('summary','summary'),('detail','detail')])
    has_detail=fields.Boolean('Has detail type')