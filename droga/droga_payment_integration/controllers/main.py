from odoo import http
from odoo.http import request

class TelebirrPaymentController(http.Controller):

    @http.route('/pay/telebirr', auth='user', methods=['POST'], website=True)
    def pay_telebirr(self, **post):
        # Logic for handling the payment confirmation and redirect to Telebirr API.
        acquirer = request.env['payment.acquirer'].search([('name', '=', 'Telebirr')], limit=1)
        amount = post.get('amount')
        partner = request.env.user.partner_id

        payment_url = acquirer._get_payment_url(amount, partner)
        return request.redirect(payment_url)
