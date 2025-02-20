import datetime

from odoo import models, fields, api
from dateutil import relativedelta

from odoo.exceptions import UserError


class picking_inherit(models.Model):
    _inherit = 'stock.picking'
    from_pharmacy_menu = fields.Boolean('Pharmacy transfer', default=False)
    picking_type_id_pharmacy = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        required=False, check_company=True)
    show_set_to_draft = fields.Boolean(compute='_show_set_to_draft')

    def _show_set_to_draft(self):
        for rec in self:
            if not rec.name.startswith('MT') and not self.env.user.has_group('droga_pharma.pharma_director'):
                #This hides it
                rec.show_set_to_draft = True
            else:
                rec.show_set_to_draft = False

    def set_to_draft(self):
        for rec in self:
            rec.do_unreserve()
            for mv in rec.move_ids:
                mv.write({'state': 'draft'})
            rec.write({'state': 'draft'})

    @api.onchange("picking_type_id_pharmacy")
    def _on_picking_type_id_pharmacy(self):
        for record in self:
            record.picking_type_id = record.picking_type_id_pharmacy

    from_wh_rep = fields.Char('From warehouse', compute='_get_info')
    to_wh_rep = fields.Char('To warehouse', compute='_get_info')
    from_user = fields.Char('From user', compute='_get_info')
    to_user = fields.Char('To user', compute='_get_info')

    def _get_info(self):
        for rec in self:
            if rec.picking_type_id.sequence_code == "MTOV":
                rec.from_wh_rep = rec.from_wh
                rec.to_wh_rep = rec.to_wh

                rec_message_ids = self.env['mail.message'].search([('res_id', '=', rec.id)]).ids
                rec.from_user = self.env['mail.tracking.value'].search(
                    [('model', '=', 'stock.picking'), ('field_desc', '=', 'Status'), ('new_value_char', '=', 'Done'),
                     ('mail_message_id', 'in', rec_message_ids)])[0].create_uid.name if self.env[
                    'mail.tracking.value'].search(
                    [('model', '=', 'stock.picking'), ('field_desc', '=', 'Status'), ('new_value_char', '=', 'Done'),
                     ('mail_message_id', 'in', rec_message_ids)]) else '-'
                receiver_pick = self.env['stock.picking'].search([('origin', '=', rec.name)])[0] if self.env[
                    'stock.picking'].search([('origin', '=', rec.name)]) else False
                if receiver_pick:
                    receiver_message_ids = self.env['mail.message'].search([('res_id', '=', receiver_pick.id)]).ids
                    rec.to_user = self.env['mail.tracking.value'].search(
                        [('model', '=', 'stock.picking'), ('field_desc', '=', 'Status'),
                         ('new_value_char', '=', 'Done'), ('mail_message_id', 'in', receiver_message_ids)])[
                        0].create_uid.name if self.env['mail.tracking.value'].search(
                        [('model', '=', 'stock.picking'), ('field_desc', '=', 'Status'),
                         ('new_value_char', '=', 'Done'), ('mail_message_id', 'in', receiver_message_ids)]) else '-'
                else:
                    rec.to_user = '-'
            else:
                sender_pick = self.env['stock.picking'].search([('name', '=', rec.origin)])
                if sender_pick and rec.picking_type_id.sequence_code == "MTIV":
                    message_ids = self.env['mail.message'].search([('res_id', '=', sender_pick.id)]).ids

                    rec.from_wh_rep = sender_pick.from_wh
                    rec.from_user = self.env['mail.tracking.value'].search(
                        [('model', '=', 'stock.picking'), ('field_desc', '=', 'Status'),
                         ('new_value_char', '=', 'Done'), ('mail_message_id', 'in', message_ids)])[0].create_uid.name if \
                    self.env['mail.tracking.value'].search(
                        [('model', '=', 'stock.picking'), ('field_desc', '=', 'Status'),
                         ('new_value_char', '=', 'Done'), ('mail_message_id', 'in', message_ids)]) else '-'

                    rec_message_ids = self.env['mail.message'].search([('res_id', '=', rec.id)]).ids
                    rec.to_wh_rep = sender_pick.to_wh
                    rec.to_user = self.env['mail.tracking.value'].search(
                        [('model', '=', 'stock.picking'), ('field_desc', '=', 'Status'),
                         ('new_value_char', '=', 'Done'), ('mail_message_id', 'in', rec_message_ids)])[
                        0].create_uid.name if self.env['mail.tracking.value'].search(
                        [('model', '=', 'stock.picking'), ('field_desc', '=', 'Status'),
                         ('new_value_char', '=', 'Done'), ('mail_message_id', 'in', rec_message_ids)]) else '-'
                else:
                    rec.from_wh_rep = '-'
                    rec.from_user = '-'
                    rec.to_wh_rep = '-'
                    rec.to_user = '-'


class transfer_request_inherit(models.Model):
    _inherit = 'droga.inventory.transfer.custom'
    pharmacy_manager = fields.Many2one('res.users', compute='_get_pharma_approvers', store=True)

    def _get_pharma_approvers(self):
        for rec in self:
            rec.pharmacy_manager = self.env.ref("droga_pharma.pharma_supply_chain_manager").users.filtered(
                lambda m: self.env.company.id in m.company_ids.ids).ids[0] if len(
                self.env.ref("droga_pharma.pharma_supply_chain_manager").users.filtered(
                    lambda m: self.env.company.id in m.company_ids.ids).ids) > 0 else None

    def request_ph(self):
        self.set_activity_done()
        self.ensure_one()
        if self.location_dest_id.complete_name[0:3] != self.location_id.code[0:3]:
            self._get_pharma_approvers()
            self.state = 'phmg'
        else:
            if self.location_dest_id.complete_name[0:3] != self.location_id.code[0:3]:
                # Post on message board here
                channels = self.env['mail.channel'].search([('name', '=', 'Pharmacy inter-store')])

                message = "Inter-store transaction request has been initiated by " + str.upper(
                    self.location_dest_id.complete_name) + '. The requested store is ' + str.upper(
                    self.location_id.name) + "."
                message = message + '   Inter-store request number - ' + self.name
                for c in channels:
                    c.message_post(
                        subject="Inter-store pharmacy transfer.",
                        body=message,
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment',
                        author_id=2,
                    )
            self.confirm_im()
        # if self.location_dest_id.complete_name[0:3]==self.location_id.code[0:3]:
        #    self.confirm_ph()
        # self._get_pharma_approvers()
        # if not self.pharmacy_manager:
        #    raise UserError("Pharmacy operations manager not configured, please contact IT.")
        # self.state = 'phmg'

    def confirm_ph(self):
        self.set_activity_done()
        if self.location_id.wh_type != "PH":
            self.state = 'stmgp'
        else:
            self.confirm_im();

    def confirm_im(self):
        self.set_activity_done()
        for wh in self['location_id']:
            pick_type_id = self.env['stock.picking.type'].sudo().search(
                [('sequence_code', '=', 'MTOV'), ('warehouse_id', 'like', wh.id)]).id
            if not pick_type_id:
                raise UserError("Picking type 'MTOV' is not configured for source warehouse.")

            pick_type_id = self.env['stock.picking.type'].sudo().search(
                [('sequence_code', '=', 'MTOV'), ('warehouse_id', '=', wh.id)]).id
            locs = self.env['stock.location'].search(
                [('usage', '=', 'internal'), ('con_type', '=', False), ('wcode', '=', wh.code)])

            if len(locs) == 0:
                locs = self.env['stock.location'].search(
                    [('usage', '=', 'production'), ('con_type', '=', False), ('wcode', '=', wh.code)])
                if len(locs) == 0:
                    raise UserError("Issuing warehouse doesn't have internal location.")

            if self.consignment_item and len(self.detail_entries.filtered(lambda ent: ent.cons_price == 0)) > 0:
                raise UserError("Consignment price should be filled for all entries.")

            def_location_id = locs[0].id
            if not def_location_id:
                raise UserError("Default internal location is not configured for source warehouse.")
            picking_vals = {
                'partner_id': self.company_id.partner_id.id,
                'company_id': self.company_id.id,
                'picking_type_id': pick_type_id,
                'location_id': def_location_id,
                'location_dest_id': self.location_dest_id.id,
                'state': 'draft',
                'trans_issue_request': self.id,
                'scheduled_date': self.request_date,
                'requested_by': self.create_uid
            }
            picking_id = self.env['stock.picking'].sudo().create(picking_vals)

            if not self.transfer_reference:
                self.transfer_reference = picking_id.name + '\n'
            else:
                self.transfer_reference = self.transfer_reference + picking_id.name + '\n'

            for rec in self.detail_entries:
                move_vals = {
                    'picking_id': picking_id.id,
                    'picking_type_id': pick_type_id,
                    'name': picking_id.name,
                    'product_id': rec['product_id'].id,
                    'product_uom': rec["product_id"].uom_id.id,
                    'product_uom_qty': rec['product_uom_qty'] * (
                                rec["product_id"].uom_id.factor / rec["product_uom"].factor),
                    'location_id': def_location_id,
                    'location_dest_id': self.location_dest_id.id,
                    'cons_price': rec['cons_price'],
                    # 'state': 'waiting',
                    # 'state': 'confirmed',
                    'state': 'draft',
                    'company_id': self.company_id.id
                }

                self.env['stock.move'].sudo().create(move_vals)
            picking_id.action_assign()
            picking_id.state = 'assigned'
        self.state = 'waiting'
