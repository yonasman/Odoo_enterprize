from odoo import http
from odoo.http import request
import json


class TelebirrWebhookController(http.Controller):

    @http.route('/telebirr/webhook', auth='public', methods=['POST'], csrf=False)
    def handle_telebirr_webhook(self, **post):
        # Get the JSON data from the POST request
        try:
            data = json.loads(request.httprequest.data)

            # Process the data here (save to database, update order status, etc.)
            # For example, you can create or update a payment record based on the data:
            self.process_telebirr_data(data)

            # Respond with a 200 OK status to Telebirr
            return "OK"

        except Exception as e:
            return "Error", 500

    def process_telebirr_data(self, data):
        # Example: Process the webhook data, update an order, or create a payment
        order_id = data.get('order_id')
        payment_status = data.get('status')

        if order_id and payment_status:
            # Find or create a payment record, depending on the webhook data
            order = request.env['sale.order'].search([('name', '=', order_id)], limit=1)
            if order:
                # Update order status based on the webhook data
                # order.write({'state': 'done' if payment_status == 'success' else 'cancel'})
                print("Order %s status updated to %s", order_id, order.state)
