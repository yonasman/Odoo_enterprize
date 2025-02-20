from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class LcMargin(models.Model):
    _name = 'droga.purchase.lc.margin'

    purchase_order_id = fields.Many2one("purchase.order")
    margin_percent = fields.Integer("Margin %", required=True)
    foreign_amount = fields.Float("Foreign Amount", digits=(12, 2), compute="compute_amount", store=True)
    exchange_rate = fields.Float("Exchange Rate", required=True, digits=(12, 6))
    amount_etb = fields.Float("ETB Amount", require=True, compute="compute_amount", digits=(12, 2))
    margin_order = fields.Selection([('1', 'First Margin'), ('2', 'Last Margin'), ('3', 'Partial Margin')])
    margin_calculation = fields.Selection([('1', 'Post full amount'), ('2', 'Post the Difference')])
    account = fields.Many2one("account.account", required=True)
    lc = fields.Many2one('account.analytic.account', domain=[
        ('plan_id', '=', 'LC')])
    move_id = fields.Many2one("account.move")

    @api.model
    def create(self, vals):
        self.margin_percent_constraint()
        self.update_exchange_rate_po(vals)
        return super(LcMargin, self).create(vals)

    def write(self, vals):
        self.margin_percent_constraint()
        self.update_exchange_rate_po(vals)
        return super(LcMargin, self).write(vals)

    def unlink(self):
        if self.move_id:
            raise ValidationError("You can't delete margin with journal entry")
        return super(LcMargin, self).unlink()

    def update_exchange_rate_po(self, vals):
        if 'purchase_order_id' in vals and 'margin_order' in vals:
            if vals['margin_order'] == '2':
                # search purchase order
                purchase_orders = self.env['purchase.order'].search([('id', '=', vals['purchase_order_id'])])
                for purchase_order in purchase_orders:
                    purchase_order.exchange_rate = vals['exchange_rate']

    @api.depends('margin_percent', 'exchange_rate', 'margin_calculation', 'margin_order', 'foreign_amount')
    def compute_amount(self):
        for record in self:

            if record.margin_order == '3':
                record.amount_etb = record.foreign_amount * record.exchange_rate
            else:
                # get usd total amount
                usd_total_amount = record.purchase_order_id.amount_total_usd
                record.foreign_amount = usd_total_amount * (record.margin_percent / 100)
                record.amount_etb = (usd_total_amount * record.exchange_rate) * (record.margin_percent / 100)

                if record.margin_order == '2':
                    if record.margin_calculation == '1':  # Calculate 100%
                        usd_total_amount = record.purchase_order_id.amount_total_usd
                        record.foreign_amount = usd_total_amount * (100 / 100)
                        record.amount_etb = (usd_total_amount * record.exchange_rate) * (100 / 100)
                    elif record.margin_calculation == '2':  # Calculate the difference
                        usd_total_amount = record.purchase_order_id.amount_total_usd
                        # get first margin
                        first_margin_amount_etb = self.get_first_margin_etb_amount(record.purchase_order_id.ids[0])

                        record.foreign_amount = usd_total_amount * (record.margin_percent / 100)
                        record.amount_etb = ((usd_total_amount * record.exchange_rate) * (
                                100 / 100)) - first_margin_amount_etb

    def margin_percent_constraint(self):
        margin_percent = 0
        for record in self:
            margin_percent += record.margin_percent

        if margin_percent > 100:
            raise ValidationError("Margin percent can't be greater than 100")

    def create_vendor_invoice(self):
        # get vendor id
        vendor_id = self.purchase_order_id.partner_id.id
        invoice_date = datetime.now()

        # get
        for record in self:

            # get margin order
            amount_etb = record.amount_etb
            first_margin_exchange_rate = self.get_first_margin_exchange_rate(self.purchase_order_id.id)

            if record.margin_order == 2 and first_margin_exchange_rate != 0:
                # compare first and second margin exchange rate
                if record.exchange_rate != first_margin_exchange_rate:
                    # update exchange rate for the purchase order
                    self.update_exchange_rate_po()

            invoice_lines = [
                {
                    'name': 'Goods in transit',
                    'quantity': 1,
                    'price_unit': amount_etb,
                    'account_id': record.account.id,
                    'analytic_distribution': {str(record.lc.id): 100.00},
                },
            ]
            vendor_invoice = self.env['account.move'].create({
                'move_type': 'in_invoice',
                'partner_id': vendor_id,
                'invoice_date': invoice_date,
                'invoice_line_ids': [(0, 0, {
                    'name': line['name'],
                    'quantity': line['quantity'],
                    'price_unit': line['price_unit'],
                    'analytic_distribution': line['analytic_distribution'],
                    'account_id': line['account_id'],
                }) for line in invoice_lines],
            })

            record.move_id = vendor_invoice

    def get_first_margin_exchange_rate(self, purchase_order_id):
        for record in self:
            margin_exchange_rate = self.env['droga.purchase.lc.margin'].search(
                [('purchase_order_id', '=', purchase_order_id), ('margin_order', '=', '1')])

            for rec in margin_exchange_rate:
                return rec.exchange_rate

        return 0

    def get_first_margin_etb_amount(self, purchase_order_id):
        for record in self:
            margin_exchange_rate = self.env['droga.purchase.lc.margin'].search(
                [('purchase_order_id', '=', purchase_order_id), ('margin_order', '=', '1')])

            for rec in margin_exchange_rate:
                return rec.amount_etb

        return 0
