from odoo import http
from odoo.http import request
import json
from werkzeug.utils import redirect

class PaymentController(http.Controller):
        @http.route('/payment/notify', type='json', auth='public', methods=['POST'], csrf=False)
        def payment_notify(self, **post):
            """ Handle Telebirr payment notification """
            try:
                print('hello')
                data = json.loads(request.httprequest.data)
                print(data)
                reference = data.get("reference")
                status = data.get("status")  # Example: "paid"

                # Find the invoice
                invoice = request.env['account.move'].sudo().browse(int(reference))
                print(invoice)

                if invoice and status == "paid":
                    # Register payment in Odoo
                    payment = request.env['account.payment'].sudo().create({
                        'payment_type': 'inbound',
                        'partner_id': invoice.partner_id.id,
                        'amount': invoice.amount_total,
                        'payment_method_line_id': request.env.ref('account.account_payment_method_manual_in').id,
                        'journal_id': request.env['account.journal'].sudo().search([('type', '=', 'bank')], limit=1).id,
                    })
                    payment.action_post()

                    # Mark invoice as paid
                    invoice.sudo().write({'payment_state': 'paid'})

                    # Redirect user to invoice page
                    return {'success': True, 'redirect_url': f"/web#id={invoice.id}&model=account.move&view_type=form"}

                return {'success': False, 'message': 'Payment failed or invoice not found'}

            except Exception as e:
                return {'success': False, 'message': str(e)}