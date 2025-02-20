from odoo import models, fields

class PaymentAcquirerTelebirr(models.Model):
    _inherit = 'telebirr.payment.acquirer'

    telebirr_api_key = fields.Char(string='Telebirr API Key')
    telebirr_api_url = fields.Char(string='Telebirr API URL', default='https://api.telebirr.com')

    def _get_payment_url(self, amount, partner):
        # Build the URL for redirecting to Telebirr for payment
        # You would probably interact with Telebirr's API here to create a transaction
        payment_url = f"{self.telebirr_api_url}?amount={amount}&partner_id={partner.id}&api_key={self.telebirr_api_key}"
        return payment_url
