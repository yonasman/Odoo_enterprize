import datetime

from odoo import models, fields, api


class droga_tender_activity_generate(models.Model):
    _name = 'droga_tender_activity'


    def generate_activity(self):
        # recs = self.env['droga.tender.master'].search([('closing_date_gre','>=','datetime.datetime.combine(context_today(), datetime.time(0,0,0))')])

        tender_users = self.env['res.groups'].search([('name', '=', 'Tender Alert Receiver')])[0]['users']

        #region submission alerts
        compare_date_addis = datetime.date.today() + datetime.timedelta(days=3)
        compare_date_other = datetime.date.today() + datetime.timedelta(days=5)
        recs = self.env['droga.tender.master'].search([('submission_alert_sent', '=', False),
                                                       ('closing_date_gre', '<', compare_date_addis),
                                                       ('bid_submit_place.submission_place_name', '=ilike', 'addis')])
        for rec in recs:
            descr = 'Tender submission, 3 days left for ' + rec['ten_name']
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
                                                           'bid_submit_place.submission_place_name', 'not ilike',
                                                           'Addis')])
        for rec in recs:
            descr = 'Tender submission, 5 days left for ' + rec['ten_name']
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

        # region open date alerts
        compare_date = datetime.date.today() + datetime.timedelta(days=1)
        recs = self.env['droga.tender.master'].search([('opening_alert_sent', '=', False),
                                                       ('open_date_gre', '<', compare_date)])
        for rec in recs:
            descr = 'Tender open date, 1 day left for ' + rec['ten_name']
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
                                                       ('bid_submit_place.submission_place_name', '=ilike',
                                                        'addis')])
        for rec in recs:
            descr = 'Tender extended submission, 3 days left for ' + rec['ten_name']
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
                                                       ('bid_submit_place.submission_place_name', 'not ilike',
                                                        'addis')])
        for rec in recs:
            descr = 'Tender extended submission, 5 days left for ' + rec['ten_name']
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
            descr = 'Tender finance opening date, 1 day left for ' + rec['parent_tender_submission'].ten_name
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
            descr = 'Tender contract deadline, 10 days left for ' + rec['parent_tender_contract'].ten_name
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
            descr = 'Tender contract extended deadline, 10 days left for ' + rec['parent_tender_contract'].ten_name
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
            """ delete from mail_activity where res_model = 'droga.tender.master' and date_deadline<current_date-INTERVAL '5 DAY'""",[])

















