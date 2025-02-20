import calendar

from odoo import models, fields, api
from odoo.http import request


class droga_top_supp_pharma(models.Model):
    _name = 'droga.top.supp.pharma'
    _auto = False

    partner_id = fields.Many2one('res.partner', 'Supplier')
    yr = fields.Char('Year')
    total_purchase = fields.Float('Total purchase')
    rank = fields.Float('Rank')

    def init(self):
        self._cr.execute(""" 
           create or replace view droga_top_supp_pharma as 
           (
                select row_number() over () as id,g.* from (
                
                select t.* from (SELECT *,
         ROW_NUMBER() OVER (PARTITION BY yr ORDER BY total_purchase DESC) AS rank
  FROM (
    SELECT partner_id,
          date_part('year', date_planned) as yr,
           SUM((price_total / product_qty) * qty_received) AS total_purchase
    FROM purchase_order_line
    WHERE qty_received > 0
      AND (SELECT i.request_type
            FROM purchase_order i
            WHERE i.id = purchase_order_line.order_id) = 'Pharmacy'
    GROUP BY date_part('year', date_planned), partner_id
    ORDER BY yr DESC, total_purchase DESC
  ) AS base_data) t where t.rank<=20
                
                ) g 
           ) 
         """)
