
from odoo import models, fields,api
import requests,re
from odoo.exceptions import ValidationError


class PaymentOptions(models.TransientModel):
    _name = 'payment.options.wizard'
    _description = 'Wizard to select payment options'

    invoice_id = fields.Many2one('account.move', string="Invoice", required=True, domain=[('state', '=', 'posted'), ('move_type', '=', 'out_invoice')])
    payment_providers = fields.Selection([('telebirr','Telebirr'),('cbe','CBE')],string='Select Payment Provider')
    phone_number = fields.Char(string='Phone Number',required=True)
    status = fields.Selection([('pending','Pending'),('paid','Paid'),('failed','Failed')],default='pending',string='Payment Status')
    amount = fields.Float(string="Amount", store=True, readonly=True)


    @api.constrains('phone_number')
    def _check_phone_number_format(self):
        "validate the phone number format"
        pattern = re.compile(r'^(?:\+2519\d{8}|09\d{8})$')
        for record in self:
            if not pattern.match(record.phone_number):
                raise ValidationError("Invalid phone number! Please enter a valid Ethiopian phone number (e.g., +251912345678 or 0912345678).")

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
        print("I am in pay telebirr")
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

        api_url = "https://developerportal.ethiotelebirr.et:38443/payment/web/paygate"
        headers = {'Content-Type': 'application/json'}

        # credentials
        config_param = self.env['ir.config_parameter'].sudo()
        app_id = config_param.get_param('payment.telebirr.app_id')
        app_key = config_param.get_param('payment.telebirr.app_key')
        short_code = config_param.get_param('payment.telebirr.app_id')
        notify_url = config_param.get_param('payment.telebirr.app_id')

        # app_id = "c4182ef8-9249-458a-985e-06d191f4d505"
        # app_key = "fad0f06383c6297f545876694b974599"
        # short_code = "992192"
        # notify_url = "https://drogaerp.odoo.com/payment/notify"

        if not all([app_id,app_key,short_code,notify_url]):
            print("Not all configs are set")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Configuration Error',
                    'message': 'Payment configuration is missing. Please check System Parameters.',
                    'sticky': False,
                }
            }

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
        response = requests.post(api_url, json=payload, headers=headers,verify=False)
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

