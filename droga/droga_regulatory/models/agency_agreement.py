from datetime import timedelta

from odoo import models, fields

class AgencyAgreement(models.Model):
    _name = 'droga.reg.agency.agreement.header'
    _description = 'Agency Agreement Follow Up Sheet'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    unique_id = fields.Char('U_id')

    name = fields.Char(string='Name')
    phone = fields.Char(string='Phone')
    applicant_type = fields.Selection([("first", "First Agent"), ("second", "Second Agent"), ("third", "Third Agent")],
                                      string='Application Type')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    status = fields.Selection([("active", "Active"), ("inactive", "Inactive"), ("pending", "Pending")], string='Status')
    extension_date = fields.Date(string='Extension Date')

    follow_up = fields.One2many('droga.reg.agency.agreement.detail','company_info',string='Follow Up')

    tracking_number = fields.Char('Tracking Number')




class AgencyAgreementDet(models.Model):
    _name = 'droga.reg.agency.agreement.detail'

    follow_up_date = fields.Date(string='Date')
    follow_up_status = fields.Char(string='Follow up status')

    company_info = fields.Many2one('droga.reg.agency.agreement.header', string='Follow Up')


