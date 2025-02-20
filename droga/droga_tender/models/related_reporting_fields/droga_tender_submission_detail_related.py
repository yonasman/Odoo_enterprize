from odoo import models, fields, api


class droga_tender_sub_detail_related(models.Model):
    _inherit = 'droga.tender.submission.detail'
    customer=fields.Many2one(related='parent_tender_submission.customer',store=True)
    customer_type = fields.Many2one('droga.cust.type', string='Customer type', related='customer.customer_type',
                                    store=True)
    ten_id = fields.Char(related='parent_tender_submission.ten_id',store=True)
    procurement_title=fields.Char(related='parent_tender_submission.procurement_title')

    # Alert booleans
    fin_alert_sent = fields.Boolean('Finance alert sent status')