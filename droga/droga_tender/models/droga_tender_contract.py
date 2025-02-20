from odoo import models, fields, api
from datetime import timedelta

class droga_tender_master(models.Model):
    _name = 'droga.tender.contract'

    # Text fields
    lot_number = fields.Char("Lot number")
    item_des = fields.Char("Item description")
    cont_num = fields.Char("Contract number")
    remark = fields.Char("Remark")

    # decimal fields
    cont_period = fields.Integer("Contract period")
    ext_period = fields.Integer("Extension period")
    amount = fields.Float("Amount")

    # relational fields
    type_item = fields.Many2one('droga.tender.settings.type.item', string='Type or items')
    parent_tender_contract = fields.Many2one('droga.tender.master', required=True)
    name=fields.Char(related='parent_tender_contract.ten_id')
    performance_security = fields.One2many('droga.tender.security.detail', 'performance_security')
    advance_security = fields.One2many('droga.tender.security.detail', 'advance_security')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    #date fields
    signing_date = fields.Date("Signing date GRE")
    agree_deadline = fields.Date("Agreement deadline GRE",compute="compute_agreement_deadline",store=True)

    #alert bool fields
    agree_alert_sent=fields.Boolean('Agreement deadline alert sent')
    ext_alert_sent = fields.Boolean('Extension deadline alert sent')
    @api.depends("signing_date", "cont_period")
    def compute_agreement_deadline(self):
        for record in self:
            if record.signing_date:
                record.agree_deadline = record.signing_date + timedelta(days=record.cont_period)
            else:
                record.agree_deadline = record.signing_date
    ext_deadline = fields.Date("Extension deadline GRE",compute="compute_ext_deadline",store=True)
    @api.depends("agree_deadline", "ext_period")
    def compute_ext_deadline(self):
        for record in self:
            if record.signing_date:
                record.ext_deadline = record.agree_deadline + timedelta(days=record.ext_period)
            else:
                record.ext_deadline = record.agree_deadline

    def adv_security_open(self):
        return {
            'name': 'Advance security',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'droga.tender.contract',
            'view_id': self.env.ref('droga_tender.droga_tender_advance_view_form').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
            'context': {
                'default_tender_id': self.parent_tender_contract.id,
                'default_security_for': 'Advance security'
            }
        }

    def sales_order_open(self):
        return {
            'name': 'Sales order',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'view_id': self.env.ref('sale.view_order_form').id,
            'type': 'ir.actions.act_window',
            'context': {
                'default_tender_origin_form_tender': self.parent_tender_contract.id,
                'default_partner_id': self.parent_tender_contract.customer.master_cust_id.id,
            }
        }

    def performance_security_open(self):
        return {
            'name': 'Performance security',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'droga.tender.contract',
            'view_id': self.env.ref('droga_tender.droga_tender_performance_view_form').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
            'context': {
                'default_tender_id': self.parent_tender_contract.id,
                'default_security_for': 'Performance security'
            }
        }

    def performance_security_open_not_used_left_for_reference(self):
        return {
            'name': 'Performance security',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'droga.tender.security.detail',
            'view_id': self.env.ref('droga_tender.droga_tender_sec_detail_view_form').id,
            'type': 'ir.actions.act_window',

            #This will pass the detail ID if a record is present
            'res_id': self.performance_security.id,

            #When target is new, it will popup else it will use it's own form, wow ferenj
            'target': 'new',

            #Context is used to pass information, on another note domain is used to filter information
            'context':{
                'default_performance_security':self.id,
                'default_tender_id':self.parent_tender_contract.id,
            }
        }