from odoo import models, fields, api

class FleetRequest(models.Model):
    _name = 'fleet.request.rejection.reason.header'
    _description = 'Fleet Request Rejection Reasons'
    _rec_name = "name"

    rejection_reason_header = fields.One2many('fleet.request.rejection.reason', 'fleet_request_id',
                                              string='Rejection Reasons')
    name = fields.Char(string='Reason', required=True)


class FleetRequestRejectionReason(models.Model):
    _name = 'fleet.request.rejection.reason'
    _description = 'Fleet Request Rejection Reason'

    name = fields.Char(string='Reason', required=True)
    fleet_request_id = fields.Many2one('fleet.request.rejection.reason.header', string='Rejection Reason')
