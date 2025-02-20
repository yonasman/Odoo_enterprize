from odoo import models, fields, api
import datetime


class droga_tender_master_related(models.Model):
    _inherit = 'droga.tender.master'
    cus_type = fields.Many2one(related='customer.customer_type', string='Customer type',store=True)
    phone_add = fields.Char(related='customer.master_cust_id.phone', string='Phone number')
    bid_security_amount_char = fields.Char('Security amount', required=True)
    bid_security_pct = fields.Float('Security percent')
    awarded_amt_total=fields.Float('Awarded total amount',compute='_compute_awarded_amt_total',store=True)          #Total tender awarded
    tender_amt_participated = fields.Float('Total Quotation', compute='_compute_awarded_amt_total',store=True)     #Total tender participated
    performance_amt_award = fields.Float('Total award', compute='_compute_amt_performance',store=True)
    performance_amt_sent=fields.Float('Total Quotation',compute='_compute_amt_performance',store=True)              #Not active
    performance_pct=fields.Float('Award %',compute='_compute_awarded_amt_total',group_operator='avg',store=True)

    total_delivered_amount=fields.Float('Total delivered amt',compute='_compute_delivered_amt_total',store=True)
    performance_pct_delivery=fields.Float('Delivery %',compute='_compute_delivered_amt_total',group_operator='avg',store=True)

    award_folder=fields.Char(related='detail_submissions_fin.award_fold_num')
    item_types=fields.Text('Item / types',compute='_get_item_types')


    #Alert booleans
    submission_alert_sent=fields.Boolean('Submission alert sent status',default=False)
    opening_alert_sent = fields.Boolean('Opening alert sent status',default=False)
    extension_alert_sent = fields.Boolean('Extension alert sent status',default=False)

    @api.depends('detail_performance.delivered_qty','detail_performance.unit_price','detail_performance.award_cost')
    def _compute_delivered_amt_total(self):
        for rec in self:
            total_award = 0
            total_delivered = 0
            for perf_line in rec.detail_performance:
                total_delivered+=perf_line.delivered_qty*perf_line.unit_price
                total_award+=perf_line.award_cost
            rec.total_delivered_amount=total_delivered
            rec.performance_pct_delivery=(total_delivered/total_award)*100 if total_award!=0 else 0

    @api.depends('detail_submissions_fin.amount','detail_submissions_fin.status','detail_submissions_fin.amount','detail_submissions_fin')
    def _compute_awarded_amt_total(self):
        for rec in self:
            fin_details = rec.detail_submissions_fin
            amo_total = 0
            amt_participated=0
            for fin_line in fin_details:
                amt_participated+=fin_line['amount']
                if fin_line['status']=='awarded':
                    amo_total += fin_line['amount']
            rec.awarded_amt_total = amo_total
            rec.tender_amt_participated=amt_participated
            rec.performance_pct = (float(
                rec.awarded_amt_total / rec.tender_amt_participated)) * 100 if rec.tender_amt_participated != 0 else 0
    

    @api.depends('detail_performance.amount', 'detail_performance.award_cost')
    def _compute_amt_performance(self):
        for rec in self:
            awarded_cost = 0
            det_performance = rec.detail_performance
            for perf_line in det_performance:
                awarded_cost += perf_line['award_cost']
            rec.performance_amt_award = awarded_cost
            rec.performance_pct=(float(rec.performance_amt_award/rec.tender_amt_participated) )*100 if rec.tender_amt_participated!=0 else 0

    @api.depends('detail_tenders.lot_number','detail_tenders.type_item')
    def _get_item_types(self):
        for rec in self:
            type_item=''
            for det_tend in rec.detail_tenders:
                #type_item=type_item+'\nLot '+det_tend.lot_number+' - ' if type_item!='' else 'Lot '+det_tend.lot_number+' - '
                type_item = type_item.rstrip(type_item[-1]).rstrip(type_item[-2]) + '\nLot ' + det_tend.lot_number + ' - ' if type_item != '' else 'Lot ' + det_tend.lot_number + ' - '
                for item_de in det_tend.type_item:
                    type_item=type_item+item_de.type_or_item_name+', '
            rec.item_types=type_item.rstrip(type_item[-1]).rstrip(type_item[-2]) if type_item != '' else type_item

    @api.model
    def generate_activity(self):
        # recs = self.env['droga.tender.master'].search([('closing_date_gre','>=','datetime.datetime.combine(context_today(), datetime.time(0,0,0))')])

        tender_users = self.env['res.groups'].search([('name', '=', 'Tender Alert Receiver')])[0]['users']

        #region submission alerts
        compare_date_addis = datetime.date.today() + datetime.timedelta(days=3)
        compare_date_other = datetime.date.today() + datetime.timedelta(days=5)
        recs = self.env['droga.tender.master'].search([('submission_alert_sent', '=', False),
                                                       ('closing_date_gre', '<', compare_date_addis),
                                                       ('bid_submit_place', 'like', '%addis%')])
        for rec in recs:
            descr = 'Tender submission for ' + rec['customer'].name +' is on '+rec['closing_date_gre'].strftime("%B %d,%Y")
            rec['submission_alert_sent'] = True
            if rec['closing_date_gre'] == rec['open_date_gre']:
                rec['opening_alert_sent'] = True
            for ten_user in tender_users:
                self.env['mail.activity'].sudo().create({
                    'res_model_id': self.env.ref('droga_tender.model_droga_tender_master').id,
                    'res_name': descr,
                    'res_id': rec.id,
                    'automated': True,
                    'user_id': ten_user.id,
                    'date_deadline': rec['closing_date_gre'],
                    'activity_type_id': self.env['mail.activity.type'].search(
                        [('name', 'like', '%Tender submission%')]).id,
                    'summary': descr,
                    'note': rec['ten_name']
                })
        recs = self.env['droga.tender.master'].search([('submission_alert_sent', '=', False),
                                                       ('closing_date_gre', '<', compare_date_other), (
                                                           'bid_submit_place', 'not like',
                                                           '%addis%')])
        for rec in recs:
            descr = 'Tender submission for ' + rec['customer'].name +' is on '+rec['closing_date_gre'].strftime("%B %d,%Y")
            rec['submission_alert_sent'] = True
            if rec['closing_date_gre'] == rec['open_date_gre']:
                rec['opening_alert_sent'] = True
            for ten_user in tender_users:
                self.env['mail.activity'].sudo().create({
                    'res_model_id': self.env.ref('droga_tender.model_droga_tender_master').id,
                    'res_name': descr,
                    'res_id': rec.id,
                    'automated': True,
                    'user_id': ten_user.id,
                    'date_deadline': rec['closing_date_gre'],
                    'activity_type_id': self.env['mail.activity.type'].search(
                        [('name', 'like', '%Tender submission%')]).id,
                    'summary': descr,
                    'note': rec['ten_name']
                })
        #endregion

        # region open date alerts.
        compare_date = datetime.date.today() + datetime.timedelta(days=1)
        recs = self.env['droga.tender.master'].search([('opening_alert_sent', '=', False),
                                                       ('open_date_gre', '<', compare_date)])
        for rec in recs:
            descr = 'Tender open date for ' + rec['customer'].name + ' is on ' + rec['open_date_gre'].strftime("%B %d,%Y")
            rec['opening_alert_sent'] = True

            for ten_user in tender_users:
                self.env['mail.activity'].sudo().create({
                    'res_model_id': self.env.ref('droga_tender.model_droga_tender_master').id,
                    'res_name': descr,
                    'res_id': rec.id,
                    'automated': True,
                    'user_id': ten_user.id,
                    'date_deadline': rec['open_date_gre'],
                    'activity_type_id': self.env['mail.activity.type'].search(
                        [('name', 'like', '%Tender opening%')]).id,
                    'summary': descr,
                    'note': rec['ten_name']
                })
        #endregion

        # region extension date alerts
        compare_date_addis = datetime.date.today() + datetime.timedelta(days=3)
        compare_date_other = datetime.date.today() + datetime.timedelta(days=5)
        recs = self.env['droga.tender.master'].search([('extension_alert_sent', '=', False),
                                                       ('extension_date_gre', '<', compare_date_addis),
                                                       ('bid_submit_place', 'like',
                                                        '%addis%')])
        for rec in recs:
            descr = 'Tender extended submission for ' + rec['customer'].name + ' is on ' + rec['extension_date_gre'].strftime("%B %d,%Y")
            rec['extension_alert_sent'] = True
            if rec['extension_date_gre'] == rec['open_date_gre']:
                rec['opening_alert_sent'] = True
            for ten_user in tender_users:
                self.env['mail.activity'].sudo().create({
                    'res_model_id': self.env.ref('droga_tender.model_droga_tender_master').id,
                    'res_name': descr,
                    'res_id': rec.id,
                    'automated': True,
                    'user_id': ten_user.id,
                    'date_deadline': rec['extension_date_gre'],
                    'activity_type_id': self.env['mail.activity.type'].search(
                        [('name', 'like', '%Tender submission%')]).id,
                    'summary': descr,
                    'note': rec['ten_name']
                })
        recs = self.env['droga.tender.master'].search([('extension_alert_sent', '=', False),
                                                       ('extension_date_gre', '<', compare_date_other),
                                                       ('bid_submit_place', 'not like',
                                                        '%addis%')])
        for rec in recs:
            descr = 'Tender extended submission for ' + rec['customer'].name + ' is on ' + rec['extension_date_gre'].strftime("%B %d,%Y")
            rec['submission_alert_sent'] = True
            if rec['extension_date_gre'] == rec['open_date_gre']:
                rec['opening_alert_sent'] = True
            for ten_user in tender_users:
                self.env['mail.activity'].sudo().create({
                    'res_model_id': self.env.ref('droga_tender.model_droga_tender_master').id,
                    'res_name': descr,
                    'res_id': rec.id,
                    'automated': True,
                    'user_id': ten_user.id,
                    'date_deadline': rec['extension_date_gre'],
                    'activity_type_id': self.env['mail.activity.type'].search(
                        [('name', 'like', '%Tender submission%')]).id,
                    'summary': descr,
                    'note': rec['ten_name']
                })
        # endregion

        # region financial opening alert
        compare_date = datetime.date.today() + datetime.timedelta(days=1)
        recs = self.env['droga.tender.submission.detail'].search([('fin_alert_sent', '=', False),
                                                       ('fin_open', '<', compare_date)])
        for rec in recs:
            descr = 'Tender financial opening for ' + rec['parent_tender_submission'].customer.name + ' is on ' + rec['fin_open'].strftime("%B %d,%Y")
            rec['fin_alert_sent'] = True

            for ten_user in tender_users:
                self.env['mail.activity'].sudo().create({
                    'res_model_id': self.env.ref('droga_tender.model_droga_tender_master').id,
                    'res_name': descr,
                    'res_id': rec.parent_tender_submission.id,
                    'automated': True,
                    'user_id': ten_user.id,
                    'date_deadline': rec['fin_open'],
                    'activity_type_id': self.env['mail.activity.type'].search(
                        [('name', 'like', '%Tender financial opening%')]).id,
                    'summary': descr,
                    'note': rec['parent_tender_submission'].ten_name
                })
        # endregion

        # region contract agreement deadline
        compare_date = datetime.date.today() + datetime.timedelta(days=10)
        recs = self.env['droga.tender.contract'].search([('agree_alert_sent', '=', False),
                                                                  ('agree_deadline', '<', compare_date)])
        for rec in recs:
            descr = 'Tender contract deadline for ' + rec['parent_tender_contract'].customer.name + ' is on ' + rec['agree_deadline'].strftime("%B %d,%Y")
            rec['agree_alert_sent'] = True

            for ten_user in tender_users:
                self.env['mail.activity'].sudo().create({
                    'res_model_id': self.env.ref('droga_tender.model_droga_tender_master').id,
                    'res_name': descr,
                    'res_id': rec.parent_tender_contract.id,
                    'automated': True,
                    'user_id': ten_user.id,
                    'date_deadline': rec['agree_deadline'],
                    'activity_type_id': self.env['mail.activity.type'].search(
                        [('name', 'like', '%Contract agreement deadline%')]).id,
                    'summary': descr,
                    'note': rec['parent_tender_contract'].ten_name
                })

        recs = self.env['droga.tender.contract'].search([('ext_alert_sent', '=', False),
                                                         ('ext_deadline', '<', compare_date)])
        for rec in recs:
            descr = 'Tender contract extension for ' + rec['parent_tender_contract'].customer.name + ' is on ' + rec['ext_deadline'].strftime(
                "%B %d,%Y")
            rec['ext_alert_sent'] = True

            for ten_user in tender_users:
                self.env['mail.activity'].sudo().create({
                    'res_model_id': self.env.ref('droga_tender.model_droga_tender_master').id,
                    'res_name': descr,
                    'res_id': rec.parent_tender_contract.id,
                    'automated': True,
                    'user_id': ten_user.id,
                    'date_deadline': rec['ext_deadline'],
                    'activity_type_id': self.env['mail.activity.type'].search(
                        [('name', 'like', '%Contract agreement deadline%')]).id,
                    'summary': descr,
                    'note': rec['parent_tender_contract'].ten_name
                })
        # endregion
        self.env.cr.execute(
            """ delete from mail_activity where res_model = 'droga.tender.master' and date_deadline<current_date-INTERVAL '5 DAY'""",
            [])






        invoices = self.env['account.move'].search([('invoice_date_due', '<', compare_date),
                                                    ('invoice_date_due', '>', datetime.date.today()),
                                                    ('state', '=', 'posted'),('tender_alert_sent','=',False),
                                                    ('payment_state', 'in', ('not_paid', 'partial')),
                                                    ('sales_initiator','=like','TEN%')])
        channels = self.env['mail.channel'].search([('name', '=', 'Tender 10 days due date alert')])

        for inv in invoices:
            inv.write({'tender_alert_sent': True})
            message = "Please followup " + inv.partner_id.name + " on its outstanding payment of " + str(
                inv.amount_total_signed) + " due on "+str(inv.invoice_date_due)+"."
            for c in channels:
                c.message_post(
                    subject=inv.partner_id.name,
                    body=message,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                    author_id=self.env.user.id,
                )

    def write(self, vals):
        upd=super().write(vals)
        if 'closing_date_gre' in vals:
            self.submission_alert_sent = False
            self.generate_activity()
        if 'extension_date_gre' in vals:
            self.extension_alert_sent = False
            self.generate_activity()
        if 'open_date_gre' in vals:
            self.opening_alert_sent = False
            self.generate_activity()

        return upd



class droga_tender_late_invoice(models.Model):
    _inherit = 'account.move'
    tender_alert_sent=fields.Boolean('Tender alert sent',default=False)