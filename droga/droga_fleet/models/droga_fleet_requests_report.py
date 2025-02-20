from odoo import models, fields, api
from odoo.exceptions import UserError

class DrogaFleetReport(models.Model):
    _name = "droga.fleet.report"
    _description = "Droga Fleet Report"

    requested_by = fields.Many2one("res.users", string="Requested by", index=True, default=lambda self: self.env.user,
                                   readonly=True)

    requested_for = fields.Char(string='Requested For', compute='get_requested_for', required=True)
    resource_name = fields.Char(string='Resource Transported', compute='get_resource_name', required=True)
    amount = fields.Char(string='Quantity', compute='get_amount', required=True)
    chauffeur = fields.Char(string='Chauffeur', compute='get_chauffeur', required=True)
    vehicle_used = fields.Char(string='Vehicle Used', compute='get_vehicle_used', required=True)
    travel_log = fields.Char(string='Travel Log', compute='get_travel_log', required=True)
    date = fields.Datetime("Requested Date", default= fields.Datetime.now(), readonly=True)
    status = fields.Selection( [("draft", "Draft"), ("submitted", "submitted"), ("approved", "Approved"),("queued", "Queued"),("assigned", "Assigned"), ("completed", "Completed"),("cancelled", "Cancelled")], default='draft',tracking=True,required=True)



    @api.model
    def create(self, vals_list):
        fleet_requests = self.env['droga.fleet.request'].search([])
        for request in fleet_requests:
            self.create({
                'requested_by': request.requested_by,
                'requested_for': request.requested_for,
                'resource_name': request.resource_name,
                'amount': request.amount,
                'chauffeur': request.chauffeur,
                'vehicle_used': request.vehicle_used,
                'travel_log': request.travel_log,
                'date': request.date,
                'status': request.status,


            })
        return super().create(vals_list)
