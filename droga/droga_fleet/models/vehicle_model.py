from odoo import fields, models

class MyVehicle(models.Model):
    _inherit = 'fleet.vehicle.model'

    cc = fields.Float(string='CC')
    power = fields.Float(invisible=True)
    horsepower_tax = fields.Float(invisible=True)
    horsepower = fields.Float(invisible=True)

    avalaible = fields.Boolean(string="Available For Assignment")



