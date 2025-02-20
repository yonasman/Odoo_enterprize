from odoo import _, api, fields, models


class committee(models.Model):
    _name = 'droga.purhcase.committee'
    _description = 'Procurement Committee'

    date_from = fields.Date("Date From", required=True)
    date_to = fields.Date("Date To", required=True)
    names = fields.Many2many("hr.employee", required=True)
    status = fields.Selection(
        [('Active', 'Active'), ('Closed', 'Closed')], default="Active")


class foregin_purchase_phases(models.Model):
    _name = "droga.foregin.purchase.phases"
    _description = "Foregin Purhcase Phases"
    _order = "phase_name,order asc"

    phase_name = fields.Selection([('1', 'Request For Quotation Phase'), ('2', 'Ordering Phase'), (
        '3', 'Pre-Arrival /Shipping Phase'), ('4', 'Good Clearance Phase'), ('5', 'Post Clearance Phase')])
    order = fields.Integer("Step Order", required=True)
    step = fields.Char("Step", required=True)
    is_final_step = fields.Boolean("Final Step")

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.phase_name))

        return result


class Reconciliation_Doc(models.Model):
    _name = 'droga.purchase.reconciliation.docs'
    _description = 'Reconciliation Documents'

    name = fields.Char('Name', required=True)
    order = fields.Integer("Step Order", required=True)
    doc_type = fields.Char('Document Type')


class PortOfLoading(models.Model):
    _name = 'droga.purchase.port.of.loading'
    _description = 'Port of Loading'

    name = fields.Char("Name", required=True)
    country = fields.Many2one('res.country', required=True)

    port_type = fields.Selection(
        [('Loading', 'Loading'), ('Discharge', 'Discharge'), ('Final Destination', 'Final Destination')], required=True)
    shipment_type = fields.Selection([('Air', 'Air'), ('Sea', 'Sea')], required=True)
    state = fields.Selection(
        [('Active', 'Active'), ('Closed', 'Closed')], default="Active")
