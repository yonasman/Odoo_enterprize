from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_open_payment_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment Options',
            'res_model': 'payment.options.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},  # Pass invoice ID
        }
