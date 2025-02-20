from odoo import _, api, fields, models


class PreImportPermit(models.Model):

    _inherit = 'droga.purhcase.request.rfq.line'

    hs_code = fields.Char("HS Code")
    hs_code_description = fields.Char("HS Code Description")
    specification_code = fields.Char("Specification Code")
    specification_description = fields.Char("Specification Description")
    description_of_goods = fields.Char("Description of Goods")
    common_name = fields.Char("Common Name")
    state = fields.Selection(
        [('Approved', 'Approved'), ('Rejected', 'Rejected'), ('Suspended', 'Suspended')])
    no_of_packages = fields.Char("Number of Packages")
    package_unit = fields.Char("Package Unit")
    net_weight = fields.Char("Net Weight")
    gross_weight = fields.Char("Gross Weight")
    weight_unit_code = fields.Char("Weight Unit Code")
    country_of_origin = fields.Many2one("res.country")
