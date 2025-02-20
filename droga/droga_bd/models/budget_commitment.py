from odoo import _, api, fields, models


class BudgetCommitment(models.Model):
    _name = 'droga.budget.commitment.budget'
    _description = 'Commitement Budget'

    @api.depends('purchase_request_id', 'purchase_order_id', 'purchase_request_local_id')
    def _compute_amount(self):
        for record in self:
            record.amount = record.purchase_request_total_amount + \
                            record.purchase_order_total_amount

            if record.purchase_request_id:
                record.refrence_no = record.purchase_request_id.name
            elif record.purchase_request_local_id:
                record.refrence_no = record.purchase_request_local_id.name
            elif record.payment_request_id:
                record.refrence_no = record.payment_request_id.name
            else:
                record.refrence_no = record.purchase_order_id.name

    document_type = fields.Selection(
        [("PR", "Purchase Request"), ("PO", "Purchase Order"), ("PMR", "Payment Request")])
    purchase_request_id = fields.Many2one("droga.purhcase.request")
    purchase_request_local_id = fields.Many2one("droga.purchase.request.local")
    payment_request_id=fields.Many2one("droga.account.payment.request")
    purchase_request_total_amount = fields.Float(
        "Purhcase Request Total Amount", default=0)
    purchase_order_id = fields.Many2one('purchase.order')
    purchase_order_total_amount = fields.Float(
        "Purhcase Order Total Amount", default=0)
    paid_amount = fields.Float("Paid Amount", default=0)
    remaining_amount = fields.Float(
        "Remaining Amount", compute="_compute_remaining_amount", store=True)
    budgetary_position = fields.Many2one("account.budget.post")
    expense_account = fields.Many2one("account.account")
    budget_date = fields.Date("Date")
    analytic_account_id = fields.Many2one("account.analytic.account")
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 index=True, default=lambda self: self.env.company.id)
    state = fields.Selection([("Active", "Active"), ("Closed", "Closed")])

    #
    amount = fields.Float("amount", compute="_compute_amount")
    refrence_no = fields.Char("Refrence No", compute="_compute_amount")

    @api.depends('purchase_order_total_amount', 'paid_amount')
    def _compute_remaining_amount(self):
        for record in self:
            record.remaining_amount = record.purchase_order_total_amount - record.paid_amount

    # method for updating the paid amount

    def update_paid_amount(self):
        # get active purchase order items
        purchase_orders = self.env['droga.budget.commitment.budget'].search(
            [('state', '=', 'Active'), ('remaining_amount', '>', 0)])

        for record in purchase_orders:
            # search paid purchase order in account.move
            paid_invoices = self.env['account.move'].search(
                [('state', '=', 'posted'), ('invoice_origin', '=', record.purchase_order_id.name)])

            if paid_invoices:
                # update paid amount
                paid_invoice_total_amount = 0
                for paid_invoice in paid_invoices:
                    paid_invoice_total_amount += paid_invoice.amount_total

                # update the record
                record.write({'paid_amount': paid_invoice_total_amount})

                # close the status if the remaining amount is zero
                if record.remaining_amount <= 0:
                    record.write({'state': 'Closed'})

    # load accounts related with budgetary position
    @api.onchange('budgetary_position')
    def _load_budgetary_position_accounts(self):
        accounts = self.budgetary_position.account_ids.ids
        return {'domain': {'expense_account': [('id', 'in', (accounts))]}}
