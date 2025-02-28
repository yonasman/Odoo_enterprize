from odoo import models, fields

class AccountMove(models.Model):
    _inherit = "account.move"

    # CRM Lead: Links this invoice to a CRM lead
    crm_lead_id = fields.Many2one(
        'crm.lead',
        string="CRM Lead",
        help="Links this invoice to a CRM lead."
    )

