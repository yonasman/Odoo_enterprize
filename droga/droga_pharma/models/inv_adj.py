from odoo import models,fields
from odoo.exceptions import UserError


class droga_inv_adj(models.Model):
    _inherit = 'droga.stock.adjustment.request'
    has_access = fields.Boolean('is_adj_available', default=False, compute='_compute_has_access',
                                search='_search_has_access')

    def _search_has_access(self, operator,value):
        if operator == '=' and len(self.env['res.groups'].search([('name', 'in', ('Pharmacy finance manager','Finance inventory workflow approver'))]))>0:
            has_access = self.env['droga.stock.adjustment.request'].sudo().search([('order_from','=','PH'),('state','in',('waiting','processed','done','finmgp'))])
            return [('id', 'in', [x.id for x in has_access] if has_access else False)]
        else:
            return [('id', 'in', [])]

    def _compute_has_access(self):
        for rec in self:
            if len(self.env['res.groups'].search([('name', 'in', ('Pharmacy finance manager','Finance inventory workflow approver'))]))>0 and rec.order_from=='PH' and rec.state in ('waiting','finmgp','processed','done'):
                rec.has_access = True
            else:
                rec.has_access = False

    def requestp(self):
        if len(self['stock_adjustment_detail_entries']) == 0:
            raise UserError("At least one product must be filled to request adjustement.")
        if len(self.env.ref("droga_inventory.stores_manager").users.ids)==0 or len(self.env.ref("droga_inventory.inv_prod_fin_wf").users.ids)==0 or len(self.env.ref("droga_inventory.inv_prod_fin").users.ids)==0:
            raise UserError("Pharmacy manager or finance manger not configured, please contact IT for support.")
        self.set_activity_done()
        self.ensure_one()
        self.state = 'stmgp'

    def stmgp_approve(self):
        self.set_activity_done()
        self.state = 'finmgp'

    def finp_approve(self):
        self.set_activity_done()
        self.state = 'waiting'

    def set_activity_done(self):
        activity = self.env["mail.activity"].search(
            [('res_name', '=', self.name)])
        for act in activity:
            act.sudo().action_done()