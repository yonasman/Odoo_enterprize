from odoo import models, fields, api


class BranchAddress(models.Model):
    _name = 'droga.sales.branch.address'

    profit_center = fields.Many2one("account.analytic.account", domain=[('plan_id', '=', 2)])
    sub_city = fields.Char("Sub City")
    woreda = fields.Char("Woreda")
    house_no = fields.Char("House No")
    telephone1 = fields.Char("Telephone 1")
    telephone2 = fields.Char("Telephone 2")
    fax = fields.Char("Fax")
