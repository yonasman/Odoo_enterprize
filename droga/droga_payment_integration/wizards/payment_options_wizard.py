
from odoo import models, fields,api
import requests



class PaymentOptions(models.TransientModel):
    _name = 'payment.options.wizard'
    _description = 'Wizard to select payment options'

    invoice_id = fields.Many2one('account.move', string="Invoice", required=True, domain=[('state', '=', 'posted'), ('move_type', '=', 'out_invoice')])
    payment_providers = fields.Selection([('telebirr','Telebirr'),('cbe','CBE')],string='Select Payment Provider')
    phone_number = fields.Char(string='Phone Number')
    status = fields.Selection([('pending','Pending'),('paid','Paid'),('failed','Failed')],default='pending',string='Payment Status')
    amount = fields.Float(string="Amount", store=True,readonly=True)


    @api.model
    def default_get(self, fields_list):
        """ Automatically fetch invoice amount when the wizard opens. """
        defaults = super(PaymentOptions, self).default_get(fields_list)
        invoice_id = self._context.get('active_id')  # Get invoice ID from context

        if invoice_id:
            invoice = self.env['account.move'].browse(invoice_id)
            if invoice:
                defaults['invoice_id'] = invoice.id
                defaults['amount'] = invoice.amount_total

        return defaults

    def action_pay_with_telebirr(self):
        """ Send Telebirr payment request using the invoice amount """
        if not self.invoice_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'Please select an invoice before making a payment.',
                    'sticky': False,
                }
            }

        api_url = "https://developerportal.ethiotelebirr.et:38443/payment/web/paygate?"
        headers = {'Content-Type': 'application/json'}

        # Replace with actual credentials
        app_id = "c4182ef8-9249-458a-985e-06d191f4d505"
        app_key = "fad0f06383c6297f545876694b974599"
        short_code = "992192"
        notify_url = "https://yonasnegese.netlify.app/payment/telebirr/webhook"

        payload = {
            "appid": app_id,
            "appkey": app_key,
            "shortcode": short_code,
            "notifyUrl": notify_url,
            "amount": self.amount,
            "phone": self.phone_number,
            "reference": self.invoice_id.id
        }

        print(api_url)
        response = requests.post(api_url, json=payload, headers=headers)
        response_data = response.json()
        print(response_data)

        if response_data.get("code") == 0:
            self.status = 'pending'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Telebirr Payment Sent!',
                    'message': 'Please confirm the payment on your phone.',
                    'sticky': False,
                }
            }
        else:
            self.status = 'failed'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Payment Failed',
                    'message': 'There was an issue processing the payment.',
                    'sticky': False,
                }
            }

    def action_cancel(self):
        print("cancelled")

