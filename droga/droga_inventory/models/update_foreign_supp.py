from odoo import models,fields,api


class update_foreign(models.Model):
    _name = "update.foreign"

    def update_ledger(self):
        supp = self.env['purchase.order'].sudo().search([('request_type', '=', 'Foregin')]).mapped('partner_id')
        acc_moves=self.env['account.move.line'].search([('partner_id','in',supp.ids),('account_id','=',2468),('company_id','=',1)])
        for mv in acc_moves:
            mv.write({'account_id':990})

    def update_cost_ref(self):
        acc_moves = self.env['droga.inventory.consignment.receive'].search([])
        for mv in acc_moves:
            for mvv in mv.cons_ref:
                for mvvv in mvv.move_ids:
                    mvvv.write({'origin': mv.subcontractor_return_origin_form.subcontract_issue_origin_form.name})

        acc_moves = self.env['droga.inventory.consignment.issue'].search([('consignment_reference','like','EE%')])
        for mv in acc_moves:
            if mv.consignment_reference != False:
                mvp = self.env['stock.picking'].search([('name','=',mv.consignment_reference.replace('\n', ''))])
                for mvv in mvp:
                    for mvvv in mvv.move_ids:
                        mvvv.write({'origin': mv.subcontract_issue_origin_form.name})