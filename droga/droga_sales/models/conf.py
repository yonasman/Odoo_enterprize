from datetime import datetime
from odoo import models, fields
from odoo import http
from odoo.http import request, Response
import json
from odoo.exceptions import UserError

class CustomPostController(http.Controller):

    @http.route('/success/', type='http', auth='none', methods=['POST','GET'], csrf=False)
    def handle_post_request(self, **post_data):
        try:
            id = post_data.get('id')

            account_move_update = request.env['account.move'].search(['trans_gui_id','=',id])
            if len(account_move_update)>0:
                account_move_update[0].payment_state='paid'
                self.action_register_payment_automatically(account_move_update[0])
                return 'Records updated'
            else:
                return 'Records not found - '+post_data.get('id')
        except Exception as e:
            return Response(post_data.get('id')+json.dumps({"error": str(e)}), status=500)

    def action_register_payment_automatically(self,payment):
        payment.ensure_one()  # Ensure we're working with a single account.move

        if payment.payment_state == 'paid':
            raise UserError("This invoice is already paid.")

        if payment.move_type not in ('out_invoice', 'in_invoice'):  # Only for invoices
            raise UserError("Automatic payment registration is only available for invoices.")

        # 1. Determine Payment Method
        payment_method = payment.env['account.payment.method'].search([('type', '=', 'manual')],
                                                                   limit=1)  # Default manual method.  Customize as necessary
        if not payment_method:
            raise UserError("No manual payment method found. Please configure one.")

        payment_values = {
            'payment_type': 'inbound' if payment.move_type == 'out_invoice' else 'outbound',  # Important for correct flow
            'partner_id': payment.partner_id.id,
            'partner_type': 'customer' if payment.move_type == 'out_invoice' else 'supplier',
            'amount': payment.amount_residual,  # Pay the remaining amount
            'payment_date': fields.Date.today(),  # Or a specific date if needed
            'journal_id': payment.journal_id.id,
            'payment_method_id': payment_method.id,
            'communication': payment.name,
            'ref': payment.name,
            'currency_id': payment.currency_id.id,
            'move_line_ids': [(6, 0, payment.line_ids.filtered(lambda line: line.account_id == payment.account_id).ids)],
        }

        payment = request.env['account.payment'].create(payment_values)

        payment.action_post()

        request.refresh()

        return True