from email.policy import default

from odoo import models, fields,api
from odoo.addons.test_convert.tests.test_env import record


class PaymentOptions(models.TransientModel):
    _name = 'payment.options.wizard'
    _description = 'Wizard to select payment options'

    invoice_id = fields.Many2one('account.move', string="Invoice", required=True, domain=[('state', '=', 'posted'), ('move_type', '=', 'out_invoice')])
    payment_providers = fields.Selection([('telebirr','Telebirr'),('cbe','CBE')],string='Select Payment Provider')
    phone = fields.Char(string='Phone Number')
    # status = fields.Selection([('pending','Pending'),('paid','Paid'),('failed','Failed')],default='pending',string='Payment Status')
    amount = fields.Float(string="Amount", compute="_compute_amount", store=True)
    currency_id = fields.Many2one('res.currency',string="Currency",default=lambda self: self.env.company.currency_id)

    @api.model
    def default_get(self, fields_list):
        """ Automatically fetch invoice amount when the wizard opens. """
        defaults = super(PaymentOptions, self).default_get(fields_list)
        invoice_id = self._context.get('active_id')  # Get invoice ID from context

        if invoice_id:
            invoice = self.env['account.move'].browse(invoice_id)
            if invoice:
                print("amount",invoice.amount_total)
                defaults['invoice_id'] = invoice.id
                defaults['amount'] = invoice.amount_total
                print(f"Fetched Invoice Amount: {invoice.amount_total}")

        return defaults

    def action_pay_with_telebirr(self):
        print("It's paid")
        print(self.amount)
        print(self.phone)

    def action_cancel(self):
        print("cancelled")

