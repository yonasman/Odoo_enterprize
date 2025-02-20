from odoo import _, api, fields, models
from datetime import datetime


class Lc(models.Model):
    _name = 'droga.purchase.lc'
    _description = 'LC Tracking'

    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']

    rfq_id = fields.Many2one('droga.purhcase.request.rfq')
    purchase_order_id = fields.Many2one("purchase.order")

    # related fields
    rfq_no = fields.Many2one(related="purchase_order_id.rfq_id", store=True)
    supplier_id = fields.Many2one(
        related='purchase_order_id.partner_id', store=True)

    name = fields.Char("LC/TT Number", required=True)
    bank_name = fields.Char("Bank")
    bank = fields.Many2one("res.bank", required=True)
    branch = fields.Char("Branch", required=True)
    start_date = fields.Date("Issue Date")
    expire_date = fields.Date("Expire Date")
    last_day_shipment = fields.Date("Last Day of Shipment")
    request_approved_date = fields.Date(
        "Request Approved Date", help="Foregin Currency Request Approved Date", store=True)
    count_days = fields.Integer(compute='_count_days', store=True)
    lc_details = fields.One2many('droga.purchase.lc.detail', 'lc_id')
    shipping_details = fields.One2many(
        'droga.purchase.shipping.detail', 'lc_id')

    lc_recived_date_from_supplier = fields.Date("LC Recived Date from Bank")
    lc_send_date_to_supplier = fields.Date("LC Send Date to Supplier")
    draft_lc_approved_date = fields.Date("Draft LC Approved Date")
    draft_lc_approved_date_supplier = fields.Date(
        "Draft LC Approved Date by Supplier")

    exchange_rate = fields.Float(related='purchase_order_id.exchange_rate', store=True)
    total_amount_etb = fields.Float("Total Amount ETB", compute='calculate_exchange_amount', store=True)
    total_amount_usd = fields.Float("Total Amount USD/Others")
    state = fields.Selection(
        [('Draft', 'Draft'), ('Active', 'Active'), ('Expired', 'Expired'), ('Closed', 'Closed')], default='Active',
        tracking=True)

    def create(self, vals):
        # get lc Reconciliation Documents types
        lc_reconciliation_docs = self.env['droga.purchase.reconciliation.docs'].search([
            ('doc_type', '=', 'LC')])
        Shipping_reconciliation_docs = self.env['droga.purchase.reconciliation.docs'].search([
            ('doc_type', '=', 'Shipping')])

        vals[0]['lc_details'] = []
        vals[0]['shipping_details'] = []

        for line in lc_reconciliation_docs:
            lc_lines = (0, 0, {
                'name': line.name,
                'order': line.order,
            })

            vals[0]['lc_details'].append(lc_lines)

        for line in Shipping_reconciliation_docs:
            shipping_lines = (0, 0, {
                'name': line.name,
                'order': line.order,
            })

            vals[0]['shipping_details'].append(shipping_lines)

        return super(Lc, self).create(vals)

    def action_approved(self):
        self.write({"state": "Active"})

    def open_lc_detail(self):
        view = self.env.ref('droga_procurement.droga_purchase_lc_view_form')

        return {
            'name': 'LC Reconciliation',
            'view_mode': 'form',
            'res_model': 'droga.purchase.lc',
            'view_id': view.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id
        }

    @api.depends('start_date')
    def _count_days(self):
        for record in self:
            if record.start_date:
                start_date = fields.Date.from_string(record.start_date)
                now = fields.Date.from_string(datetime.now())
                record.count_days = (now - start_date).days

    @api.depends('')
    def _get_currency_request_detail(self):
        rfq_id = self.purchase_order_id.rfq_id.id

        # search
        records = self.env['droga.account.foreign.currency.request'].search(
            [('rfq_id', '=', rfq_id)])

        for record in records:
            if record.state == "Approved":
                self.request_approved_date = record.request_approved_date
                self.bank = record.bank
                self.branch = record.bank_branch

    # submit request
    def submit_request(self):
        self.write({'state': 'Active'})

    def cancel_request(self):
        self.write({'state': 'Closed'})

    @api.depends('purchase_order_id', 'exchange_rate', 'total_amount_usd', 'total_amount_etb')
    def calculate_exchange_amount(self):
        for record in self:
            record.total_amount_etb = record.total_amount_usd * record.exchange_rate

    def update_lc_status(self):
        lcs = self.env['droga.purchase.lc'].search([('state', '!=', 'Expired')])
        for record in lcs:
            if record.state != 'Closed':
                record.state = 'Active'
                if record.expire_date:
                    if record.expire_date <= datetime.now().date():
                        record.state = 'Expired'

    def update_amount(self):
        lcs = self.env['droga.purchase.lc'].search([])
        for record in lcs:
            record.total_amount_etb = record.exchange_rate * record.total_amount_usd


class LcDetail(models.Model):
    _name = 'droga.purchase.lc.detail'
    _description = 'LC Reconciliation'

    lc_id = fields.Many2one('droga.purchase.lc')
    name = fields.Char("Name", required=True)
    order = fields.Integer("Step Order", required=True)
    state = fields.Selection([('Right', 'Right'), ('Wrong', 'Wrong')])
    remark = fields.Char("Remark")


class LcDetail(models.Model):
    _name = 'droga.purchase.shipping.detail'
    _description = 'Shipping Reconciliation'

    lc_id = fields.Many2one('droga.purchase.lc')
    name = fields.Char("Name", required=True)
    order = fields.Integer("Step Order", required=True)
    state = fields.Selection([('Right', 'Right'), ('Wrong', 'Wrong')])
    remark = fields.Char("Remark")
