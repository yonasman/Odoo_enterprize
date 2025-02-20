from odoo import _, api, fields, models


class AccountFiscalYear(models.Model):
    _inherit = 'account.fiscal.year'

    periods = fields.One2many("account.fiscal.year.period", "fiscal_year_id")


class AccountFiscalYear(models.Model):
    _name = 'account.fiscal.year.period'

    fiscal_year_id = fields.Many2one("account.fiscal.year", required=True)
    name = fields.Char("Name", required=True)
    description = fields.Char("Description", required=True)
    date_from = fields.Date("Date From", required=True)
    date_to = fields.Date("Date To", required=True)

    def name_get(self):
        res = []
        for record in self:
            name = record.description
            res.append((record.id, name))
        return res



