from datetime import timedelta

from odoo import models, fields

class FinalRegisteredRenewal(models.Model):
    _name = 'droga.reg.final.registered.renewal'
    _description = 'FINAL REGISTERED AND RENEWAL FOLLOW UP SHEET'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    details = fields.One2many('droga.reg.final.detaill', 'header', string='Company Details')

    company_name = fields.Char(string='Companies')
    applicant = fields.Char('Applicant')
    product_type = fields.Selection(
        [('medicine', 'Medicine'), ('device', 'Medical Device'), ('food', 'Food'), ('cosmetics', 'Cosmetics')],
        string='Product Type', required=True)

    product_name = fields.Text( string='Products')
    approval_date = fields.Date(string='Approval Date')
    validity_date = fields.Date(string='Validity Date')
    remark = fields.Text(string='Remark')

    registered_under = fields.Selection([('droga', 'Droga'), ('other', 'Other Agents')], string='Registered Under',required=True)
    pack_size = fields.Char('Pack Size')

    def get_users_for_roles(self, role, company_id):
        users = []
        roles = self.env['res.groups'].search([('name', '=', role)])

        for user in roles.users:
            if user.company_id.id == company_id:
                users.append(user.id)
        return users

    def notify(self, message):
        users = self.get_users_for_roles('Regulatory Manager', self.env.user.company_id.id)
        for user in users:
            self.env['bus.bus']._sendone(user.id, "simple_notification", {
                "title": "Reminder for due date",
                "message": message,
                "sticky": True,
                "warning": True
            })

    def activity(self, message, agreement):
        users = self.get_users_for_roles('Regulatory Manager', self.env.user.company_id.id)
        for user in users:
            self.env['mail.activity'].sudo().create({
                'res_model_id': self.env.ref('droga_regulatory.model_droga_reg_final_registered_renewal').id,
                'res_name': message,
                'res_id': agreement.id,
                'automated': True,
                'user_id': user.id,
                'activity_type_id': 4,
                'summary': message,
                'note': agreement['id']
            })

    def send_insurance_reminder(self):
        today = fields.Date.today()
        six_month_from_now = today + timedelta(days=180)

        agreement_due_date = self.search([('validity_date', '=', six_month_from_now)])
        for agreement in agreement_due_date:
            message = "There is a validity date to registered list in 6 months"
            self.notify(message)
            self.activity(message, agreement)


class FinalRegisteredRenewalDetail(models.Model):
    _name = 'droga.reg.final.detaill'


    header = fields.Many2one('droga.reg.final.registered.renewal', string='Company Details')

    follow_up = fields.Char('Status')
    reminding_email = fields.Date('Email Sent On')







