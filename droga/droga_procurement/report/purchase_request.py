from odoo import models, fields, api
from odoo.tools.sql import drop_view_if_exists


class Purchase_Request_Report_By_Amount(models.Model):
    _name = 'droga.purchase.request.foreign.by.amount.report'

    _auto = False
    _order = 'rank'

    id = fields.Integer("Id")
    product_id = fields.Many2one('product.product')
    total_price_etb = fields.Float("Total Amount")
    quantity = fields.Float("Quantity")
    rank = fields.Integer("Rank")

    def init(self):
        drop_view_if_exists(self.env.cr, 'droga_purchase_request_foreign_by_amount_report')
        self.env.cr.execute("""
                   create or replace view droga_purchase_request_foreign_by_amount_report as (

                         select x.id,x.product_id,x.total_price_etb,x.quantity,RANK () OVER ( ORDER BY x.total_price_etb desc) rank  from(
                            select  ROW_NUMBER () OVER () as id,prl.product_id,sum(prl.total_price) as total_price_etb ,sum(prl.product_qty) as quantity
                            from droga_purhcase_request pr inner join droga_purhcase_request_line prl on pr.id =prl.purhcase_request_id 
                            where pr.state ='Approved'
                            group by prl.product_id )x 
                            
                   )""")


class Purchase_Request_Report_By_Quantity(models.Model):
    _name = 'droga.purchase.request.foreign.by.quantity.report'

    _auto = False
    _order = 'rank'

    product_id = fields.Many2one('product.product')
    total_price_etb = fields.Float("Total Amount")
    quantity = fields.Float("Quantity")
    rank = fields.Integer("Rank")

    def init(self):
        drop_view_if_exists(self.env.cr, 'droga_purchase_request_foreign_by_quantity_report')
        self.env.cr.execute("""
                   create or replace view droga_purchase_request_foreign_by_quantity_report as (
                         
                        select x.id,x.product_id,x.total_price_etb,x.quantity,RANK () OVER ( ORDER BY x.quantity desc) rank  from(
                            select  ROW_NUMBER () OVER () as id,prl.product_id,sum(prl.total_price) as total_price_etb ,sum(prl.product_qty) as quantity  
                            from droga_purhcase_request pr inner join droga_purhcase_request_line prl on pr.id =prl.purhcase_request_id 
                            where pr.state ='Approved'
                            group by prl.product_id )x 

                   )""")
