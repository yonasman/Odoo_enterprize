from odoo import models, fields, api
from datetime import date

class droga_pharma_stock_card(models.TransientModel):
    _name = 'droga.pharma.stock.card.inquiry'
    _descr = 'Stock card enquiry'

    warehouse = fields.Many2one('stock.warehouse', 'Warehouse')
    product = fields.Many2one('product.product', 'Product')
    date_from = fields.Date('Date from', default=date(2022, 12, 20))
    date_to = fields.Date('Date to', default=fields.Date.today())
    per_location = fields.Binary('Per location?')
    results=fields.One2many('droga.pharma.stock.card.detail','header')
    def load_results(self):
        loc_ids_under_wh=self.env['stock.location'].search([('complete_name', 'like', self.warehouse.code+'/%'),('usage', '=', 'internal'),('con_type','!=','SRL')])
        if self.product:
            stock_move_data=self.env['stock.move.line'].search(['|',('location_id', 'in', loc_ids_under_wh.ids),('location_dest_id', 'in', loc_ids_under_wh.ids),('state','=','done'),('date','>=',self.date_from),('date','<=',self.date_to),('product_id','=',self.product.id)],order="move_id desc").sorted(key=lambda r: r.date)
        else:
            stock_move_data = self.env['stock.move.line'].search(
                ['|', ('location_id', 'in', loc_ids_under_wh.ids), ('location_dest_id', 'in', loc_ids_under_wh.ids),
                 ('state', '=', 'done'), ('date', '>=', self.date_from), ('date', '<=', self.date_to)],
                order="move_id desc").sorted(key=lambda r: r.move_id.date)

        stock_products = list(dict.fromkeys(stock_move_data.sorted(key=lambda r: r.product_id.name)['product_id']))

        qty_rec=0
        qty_iss=0
        bal=0
        loss_adj=0
        self.results.unlink()
        for prod in stock_products:
            for move_line in stock_move_data:
                if move_line['product_id'].id==prod.id:

                    if move_line['location_id'] in loc_ids_under_wh:
                        loc= move_line.move_id.sale_line_id.order_id.partner_id.name if move_line.move_id.sale_line_id else move_line['location_dest_id'].complete_name
                    else:
                        loc= move_line['location_id'].complete_name

                    if move_line['location_id'] in loc_ids_under_wh:
                        if move_line['location_dest_id'].usage == 'inventory':
                            loss_adj= move_line['qty_done'] * -1
                            bal -= move_line['qty_done']
                            qty_rec=0
                            qty_iss=0
                        else:
                            qty_iss =move_line['qty_done']
                            bal -= move_line['qty_done']
                            loss_adj=0
                            qty_rec=0
                    else:
                        if move_line['location_id'].usage == 'inventory':
                            loss_adj=move_line['qty_done']
                            bal += move_line['qty_done']
                            qty_rec = 0
                            qty_iss = 0
                        else:
                            qty_rec=move_line['qty_done']
                            bal += move_line['qty_done']
                            loss_adj=0
                            qty_iss=0
                    fs_no=self.env['account.move'].search([('invoice_origin','=',move_line['origin'] if move_line['origin'] else move_line['reference'])])
                    fs_no_string=fs_no[0].FSInvoiceNumber if len(fs_no)>0 else ''
                    val = {
                        'header':self.id,
                        'date': move_line['move_id'].date,
                        'doc_no': move_line['origin'] if move_line['origin'] else move_line['reference'],
                        'fs_no':fs_no_string,
                        'rece_from': loc,
                        'qty_rec':qty_rec,
                        'qty_iss':qty_iss,
                        'loss_adj':loss_adj,
                        'bal':bal,
                        'uom':move_line['product_id'].uom_id.name,
                        'batch_no':move_line['lot_id'].name if move_line['lot_id'] else '-',
                        'exp_date':move_line['expiration_date'] if move_line['expiration_date'] else False
                    }
                    self.results.create(val)

class pharma_price_list(models.TransientModel):
    _name = 'droga.pharma.stock.card.detail'
    header = fields.Many2one('droga.pharma.stock.card.inquiry')
    date=fields.Date('Date')
    doc_no=fields.Char('Doc No.')
    fs_no = fields.Char('FS No.')
    rece_from=fields.Char('Received/issued to')
    qty_rec=fields.Float('Qty received')
    qty_iss = fields.Float('Qty issued')
    loss_adj = fields.Float('Qty loss/adj')
    bal=fields.Float('Balance')
    batch_no = fields.Char('Batch #')
    exp_date=fields.Date('Expiry date')
    uom=fields.Char('Unit')

