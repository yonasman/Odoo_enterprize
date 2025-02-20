from datetime import datetime
from odoo import models, fields,api

class PreImportPermit(models.Model):
    _name = 'droga.reg.pre.import.permit.header'
    _description = 'Pre Import Permit'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def set_activity_done(self):
        activity = self.env["mail.activity"].search(
            [('res_name', '=', self.name)])
        if activity:
            activity.sudo().action_done()

    def get_users_for_roles(self, role, company_id):
        users = []
        roles = self.env['res.groups'].search([('name', '=', role)])

        for user in roles.users:
            if user.company_id.id == company_id:
                users.append(user.id)
        return users


    def create_activity(self, user_id, message):
        # create mail activity for the approval
        todos = dict(res_id=self.id,
                     res_model_id = self.env['ir.model'].search([('model', '=', 'droga.reg.pre.import.permit.header')]).id,
                     user_id=user_id, summary= message, note= message,
                     activity_type_id=4,
                     date_deadline=fields.datetime.now())
        self.env['mail.activity'].sudo().create(todos)

    manufacturer = fields.Char(string='Vendor')
    proforma_invoice_no = fields.Char(string='Proforma Invoice No.')
    invoice_amount = fields.Float(string='Invoice Amount (USD)')
    date_received = fields.Date(string='Date Received')
    date_generated = fields.Date(string='Date Generated')
    app_no = fields.Char(string='App No.')
    discrepancy = fields.Char(string='Discrepancy')
    ra_status = fields.Selection([('procurement', 'Procurement'), ('ra', 'RA') ],
                                 string="Status",default='ra')


    no_days = fields.Char("Number of days taken", compute='compute_days_between_dates', readonly=True)

    @api.depends('date_received', 'date_generated')
    def compute_days_between_dates(self):
        for record in self:
            if record.date_received and record.date_generated:
                date_format = "%Y-%m-%d"
                datetime1 = datetime.strptime(str(record.date_received), date_format)
                datetime2 = datetime.strptime(str(record.date_generated), date_format)

                delta = datetime2 - datetime1
                num_days = delta.days
                num_of_days = str(num_days) + ' days'
                record.no_days = num_of_days
            else:
                record.no_days = 'Not Set'

    preimport_permit_no = fields.Char(string='Preimport permit No')

    def activty_for_ra(self):
        if self.preimport_permit_no:
            users = self.get_users_for_roles('Regulatory Manager', self.company_id.id)
            for user in users:
                self.create_activity(user,'New Entry Added to pre-import List')

