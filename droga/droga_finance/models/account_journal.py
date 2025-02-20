from odoo import models, fields, api


class Account_Journal(models.Model):
    _inherit = 'account.journal'

    check_setting = fields.Many2one("droga.account.check.setting")


class Account_Check_Setting(models.Model):
    _name = 'droga.account.check.setting'

    _order = 'name'

    name = fields.Char("Bank Name", required=True)

    name_width = fields.Float("Name Width")

    date_left_p = fields.Float("Date Left Padding")
    date_top_p = fields.Float("Date Top Padding")

    name_left_p = fields.Float("Name Left Padding")
    name_top_p = fields.Float("Name Top Padding")

    amount_left_p = fields.Float("Amount Left Padding")
    amount_top_p = fields.Float("Amount Top Padding")

    amount_word_left_p = fields.Float("Amount Word Left Padding")
    amount_world_top_p = fields.Float("Amount Word Top Spacing")
    amount_word_width = fields.Float("Amount Word Width 1")
    amount_word_width1 = fields.Float("Amount Word Width 2")

    amount_word_line_spacing = fields.Float("Amount Word Line Spacing")

    status = fields.Selection([("Active", "Active"), ("Closed", "Closed")])
