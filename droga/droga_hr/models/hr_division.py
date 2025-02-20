from odoo import models, fields, api


class Division(models.Model):
    _name = 'droga.hr.division'

    name = fields.Char("Name", required=True)
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')], default="Active")
