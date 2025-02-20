from odoo import  models,fields
from odoo.http import request

class consi_inherit(models.Model):
    _inherit = 'droga.inventory.consignment.issue'

    def _get_pr_sales_logged(self):
        if not request:
            return self.env.user.name
        ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
        return self.env.user.name if len(ses) == 0 else self.env.user.name + ', ' + ses[0].pro_id[0].p_name

    user_id_des = fields.Char('Requested by', default=_get_pr_sales_logged, store=True)


class consi_inherit(models.Model):
    _inherit = 'droga.inventory.consignment.receive'

    def _get_pr_sales_logged(self):
        if not request:
            return self.env.user.name
        ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
        return self.env.user.name if len(ses) == 0 else self.env.user.name + ', ' + ses[0].pro_id[0].p_name

    user_id_des = fields.Char('Requested by', default=_get_pr_sales_logged, store=True)
