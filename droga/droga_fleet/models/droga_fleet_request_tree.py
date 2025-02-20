from odoo import models, fields, api


class RequestReport(models.Model):
    _name = 'droga.fleet.requests.tree'

    fleet_request_id = fields.Many2one('droga.fleet.request', string="Fleet Request")
    resource_transported_id = fields.Many2one('resource.transported', string="Transported Resource")
    employee_transport_id = fields.Many2one('employee.transport', string="Employee Transport")
    task_id = fields.Many2one('droga.fleet.request.task', string="Task")


    request_date = fields.Datetime(related='fleet_request_id.date', string="Request Date")
    request_type = fields.Selection(related='fleet_request_id.request_type', string="Request Type")


    travel_log = fields.Char(related='employee_transport_id.travel_log', string="Travel Log")
    requested_for = fields.Many2one('res.users', related='employee_transport_id.requested_for', string="Requested For")

    transported_resource = fields.Char(related='resource_transported_id.resource_name', string="Transported Resource")
    deliver_to = fields.Many2one('res.partner',related='resource_transported_id.deliver_to', string="Deliver To")

    task_status = fields.Selection(related='task_id.status', string="Task Status")










#droga.fleet.requests.tree.request_type
#droga.fleet.request.request_type

