from datetime import timedelta

from odoo import models, fields

class GmpInspection(models.Model):
    _name = 'droga.reg.gmp.inspection'
    _description = 'GMP Inspection Follow Up Sheet'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    company_name = fields.Char(string='Company Name')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    product_line_description = fields.Char(string='Product Line Description')
    gmp_application_date = fields.Date(string='GMP Application Date')
    fee_letter_receival_date = fields.Date(string='GMP Fee Letter Receival Date')
    fee_paid_submit_date = fields.Date(string='Fee Paid and Submitted to Inspection On')
    scheduled_inspection_date = fields.Date(string='Scheduled for Inspection Date')
    inspection_report_receival_date = fields.Date(string='Inspection Report Received Date')
    gmp_certificate_receival_date = fields.Date(string='GMP Certificate Received Date')
    renewal = fields.Boolean(string='Renewal')
    contract_renewal = fields.Date(string='Renewal')
    remark = fields.Text(string='Remark')
    document_sent = fields.Boolean(string='Document Attached', default=False)
    document_desc = fields.Text('Description about attached document')

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
                'res_model_id': self.env.ref('droga_regulatory.model_droga_reg_gmp_inspection').id,
                'res_name': message,
                'res_id': agreement.id,
                'automated': True,
                'user_id': user.id,
                'activity_type_id': 4,
                'summary': message,
                'note': agreement['company_name']
            })

    def send_insurance_reminder(self):
        today = fields.Date.today()
        three_month_from_now = today + timedelta(days=90)

        agreement_due_date = self.search([('contract_renewal', '=', three_month_from_now)])
        for agreement in agreement_due_date:
            message = "The due date for the agreement " + agreement.company_name + " is only 3 months away!"
            self.notify(message)
            self.activity(message, agreement)

    def create_an_activity(self, user_id, message):
        # create mail activity for the approval
        todos = dict(res_id=self.id,
                     res_model_id = self.env['ir.model'].search([('model', '=', 'droga.reg.gmp.inspection')]).id,
                     user_id=user_id, summary= message, note= message,
                     activity_type_id=4,
                     date_deadline=fields.datetime.now())
        self.env['mail.activity'].sudo().create(todos)

    def send_doc_notification(self):
        users = self.get_users_for_roles('Regulatory Manager', self.company_id.id)
        for record in self:
            message_doc_sent = 'Document has been sent for GMP follow up with company name: ' + record.company_name
            for user in users:
                self.create_an_activity(user, message_doc_sent)

    def set_activity_done(self):
        activity = self.env["mail.activity"].search(
            [('res_name', '=', self.reg_num)])
        if activity:
            activity.sudo().action_done()