from odoo import models, fields, api
from odoo.http import request

class AccountPaymentRegister(models.Model):
    _inherit = 'account.move'

    def action_pay_with_telebirr(self):
        """Redirect to the Telebirr payment page with the invoice details."""
        # telebirr_acquirer = self.env['payment.acquirer'].search([('provider', '=', 'telebirr')], limit=1)
        # if not telebirr_acquirer:
        #     raise ValueError("Telebirr payment provider is not configured.")
        #
        # # Get payment details
        # amount = self.amount
        # partner = self.partner_id
        #
        # # Generate the payment URL using the acquirer method
        # payment_url = telebirr_acquirer._get_payment_url(amount, partner)
        #
        # return {
        #     'type': 'ir.actions.act_url',
        #     'url': payment_url,
        #     'target': 'new',  # Opens in a new tab
        # }
        print("Hello")
