# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/


from odoo import fields, models, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    hide_menu_access_ids = fields.Many2many('ir.ui.menu', 'ir_ui_hide_menu_rel', 'uid', 'menu_id',domain=([('parent_id','=',False)]),
                                            string='Hide Access Menu')
