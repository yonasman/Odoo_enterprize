from odoo import models, fields, api
from odoo.tools.sql import drop_view_if_exists


class ProcurementLeadTimeReports(models.Model):
    _name = 'droga.purchase.foreign.procurement.lead.time.report'
    _auto = False

    id = fields.Integer("Id")
    pr_request_id = fields.Many2one('droga.purhcase.request', "Purchase Request")
    pr_date = fields.Date(string="PR Date")
    pr_state = fields.Char(string='PR State')
    rfq_request_id = fields.Many2one('droga.purhcase.request.rfq', string="RQF #")
    rfq_date = fields.Date(string='RFQ Date')
    rfq_state = fields.Char(string='RFQ State')
    po_request_id = fields.Many2one('purchase.order', string="PO #")
    po_date = fields.Date(string='PO Date')
    po_state = fields.Char(string="PO State")
    grn_request_id = fields.Many2one('stock.picking', string="GRN #")
    grn_date = fields.Date(string='GRN Date')
    grn_state = fields.Char(string='GRN State')
    lc_start_date = fields.Date(string='LC Approved Date')
    pr_to_grn_lead_time = fields.Float("PR to GRN Lead Time",group_operator="avg")
    pr_to_lc_lead_time=fields.Float("PR to LC Lead Time",group_operator="avg")
    company_id = fields.Many2one('res.company')

    def init(self):
        drop_view_if_exists(self.env.cr, 'droga_purchase_foreign_procurement_lead_time_report')
        self.env.cr.execute("""
                      create or replace view droga_purchase_foreign_procurement_lead_time_report as (

                          select  ROW_NUMBER () OVER () as id,
                                pr.id as pr_request_id,pr.request_date as pr_date,pr.state as pr_state,
                                rfq.id as rfq_request_id,rfq.date as rfq_date,rfq.state as rfq_state,
                                po.id as po_request_id,po.date_order as po_date,po.state as po_state,
                                sp.id as grn_request_id,sp.date_done as grn_date,sp.state as grn_state,
                                lc.start_date as lc_start_date,
                                DATE_PART('day',sp.date_done-pr.request_date) as pr_to_grn_lead_time,
                                DATE_PART('day',lc.start_date-pr.request_date) as pr_to_lc_lead_time,
                                pr.company_id
                            from droga_purhcase_request pr
                                inner join droga_purhcase_request_rfq rfq on pr.id=rfq.purhcase_request_id
                                inner join purchase_order po on po.rfq_id=rfq.id
                                inner join stock_picking sp on po.name=sp.origin
                                inner join droga_purchase_lc lc on lc.purchase_order_id=po.id

                      )""")
