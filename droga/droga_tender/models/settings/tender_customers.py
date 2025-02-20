from datetime import date

from odoo import models, fields, api

class droga_tender_settings_customers(models.Model):
    _name = 'droga.tender.settings.customers'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Customer Name",required=True)
    tin_no=fields.Char("Tin No")
    master_cust_id=fields.Many2one('res.partner')
    customer_type=fields.Many2one('droga.cust.type',string='Customer type')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    def request_reg(self):
        #notification_ids = []
        #notification_ids.append((0, 0, {
        #    'res_partner_id': self.env.user.id,
        #    'notification_type': 'inbox'}))
        #self.message_post(body='This receipt has been validated!', message_type='notification',
        #                   author_id=self.env.user.id,
        #                  notification_ids=notification_ids)

        channels = self.env['mail.channel'].search([('name', '=', 'Tender sales')])


        message = "Please register customer named '"+self.name+"'."
        message=message+' Tin No - '+self.tin_no if self.tin_no else message
        for c in channels:
            c.message_post(
                subject="Customer registration.",
                body=message,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                author_id=self.env.user.id,
            )


