from odoo import _, api, fields, models


class PurchaseRequest(models.Model):
    _inherit = 'droga.purhcase.request'
    _description = 'Purchase Request'

    store_request_id = fields.Many2one(
        "droga.inventory.office.supplies.request", string="Store Request ID")


class PurchaseRequestLocal(models.Model):
    _inherit = 'droga.purchase.request.local'
    _description = 'Purchase Request'

    store_request_id = fields.Many2one(
        "droga.inventory.office.supplies.request", string="Store Request ID")