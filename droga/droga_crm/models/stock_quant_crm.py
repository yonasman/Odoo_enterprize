from odoo import models, fields, api


# Stock Warehouse Model
class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'
    linked_analytic = fields.Many2one('account.analytic.account', string="Linked Analytic Account")


# Droga Stock Quant Model
class DrogaStockQuant(models.Model):
    _inherit = 'stock.quant'

    warehouse_id = fields.Many2one('stock.warehouse', related='location_id.warehouse_id', store=True)
    branch_id = fields.Many2one('account.analytic.account', related='warehouse_id.linked_analytic', store=True)
    wh_type = fields.Selection([
        ('IM', 'Import'),
        ('WS', 'Wholesale'),
        ('PT', 'Physiotherapy'),
        ('PH', 'Pharmacy'),
        ('PR', 'Project')
    ], related='warehouse_id.wh_type', store=True)

    unit_cost = fields.Float('Unit Price', compute='_compute_cost', store=True)
    total_amount = fields.Float('Amount', compute='_compute_cost', store=True)

    selling_price = fields.Float(related='product_id.product_tmpl_id.list_price_phar')
    pharmacy_group_id = fields.Many2one('droga.prod.categ.pharma',
                                        related='product_id.product_tmpl_id.pharmacy_group_id')

    @api.depends('product_id', 'quantity')
    def _compute_cost(self):
        for record in self:
            record.unit_cost = record.product_id.standard_price
            record.total_amount = record.unit_cost * record.quantity

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(DrogaStockQuant, self).read_group(
            domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy
        )
        if 'total_amount' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    total_amt = 0.0
                    for record in lines:
                        total_amt += record.total_amount
                    line['total_amount'] = total_amt
        return res


# Droga Stock Move Line Model
class DrogaStockMoveLine(models.Model):
    _inherit = 'stock.move'

    type = fields.Char('Type', compute='_compute_type', store=True)
    unit_price = fields.Float('Unit Price', compute='_compute_unit_price', store=True)
    tot_price = fields.Float('Total Amount', compute='_compute_unit_price', store=True)

    warehouse_id = fields.Many2one('stock.warehouse', related='location_id.warehouse_id', store=True)
    warehouse_dest_id = fields.Many2one('stock.warehouse', related='location_dest_id.warehouse_id', store=True)

    branch_id = fields.Many2one('account.analytic.account', string='Branch', related='warehouse_id.linked_analytic',
                                store=True)
    branch_dest_id = fields.Many2one('account.analytic.account', related='warehouse_dest_id.linked_analytic',
                                     store=True)

    branch = fields.Many2one('account.analytic.account', compute='_compute_branch', store=True)

    @api.depends('branch_id', 'branch_dest_id')
    def _compute_branch(self):
        for record in self:
            if record.branch_id:
                record.branch = record.branch_id
            else:
                record.branch = record.branch_dest_id

    @api.depends('state')
    def _compute_unit_price(self):
        for rec in self:
            layer = self.env['stock.valuation.layer'].search([('stock_move_id', '=', rec.id)])
            rec.unit_price = layer[0].unit_cost if layer else 0
            rec.tot_price = rec.unit_price * rec.quantity_done

    @api.depends('location_id', 'location_dest_id', 'state')
    def _compute_type(self):
        for rec in self:
            if rec.location_id.usage == 'internal' and rec.location_dest_id.usage == 'customer':
                rec.type = 'Sales issue'
            elif rec.location_id.usage == 'internal' and rec.location_dest_id.usage == 'supplier':
                rec.type = 'Return'
            elif (rec.location_id.usage == 'internal' and rec.location_dest_id.usage == 'inventory') or \
                    (rec.location_id.usage == 'inventory' and rec.location_dest_id.usage == 'internal'):
                rec.type = 'Adjustment'
            elif rec.location_id.usage == 'supplier' and rec.location_dest_id.usage == 'internal':
                rec.type = 'Purchase receipt'
            elif rec.location_id.usage == 'internal' and rec.location_dest_id.usage == 'internal':
                rec.type = 'Transfer'
            elif rec.location_id.usage == 'customer' and rec.location_dest_id.usage == 'internal':
                rec.type = 'Sales receipt'
            else:
                rec.type = 'Unknown'
