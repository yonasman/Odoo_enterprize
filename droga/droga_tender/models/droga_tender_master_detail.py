from email.policy import default
from odoo import models, fields, api

class droga_tender_master_detail(models.Model):
    _name = 'droga.tender.master.detail'

    #Text fields
    lot_number=fields.Char("Lot Number",required=True)
    remark = fields.Char("Description and remark")
    quantity=fields.Float("Quantity")

    # relational fields
    type_item = fields.Many2many('droga.tender.settings.type.item', string='Type or items')
    parent_tender=fields.Many2one('droga.tender.master',required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    def bid_detail(self):
        return {
            'name': 'Bid detail',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'droga.tender.master.detail',
            'view_id': self.env.ref('droga_tender.droga_tender_master_detail_view_form').id,
            'type': 'ir.actions.act_window',
            #'res_id': self.bid_security.id,
        }
