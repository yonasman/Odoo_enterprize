from odoo import models, fields, api
from odoo.exceptions import UserError


class droga_bussiness_dev_requests(models.Model):
    _name = "droga.bdr.requests.header"
    _rec_name='request_no'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    status = fields.Selection( [("draft", "Draft"), ("submitted", "submitted"), ("reviewed", "Reviewed")],
                               default='draft',tracking=True,required=True)
    bd_status = fields.Selection( [("registered", "Registered"), ("developed", "Developed"), ("agreement", "Agreement")], default='registered', required=True)
    tracking_number = fields.Char('Tracking Number')

    request_no = fields.Char('Request ID', readonly=True)
    requested_by = fields.Many2one("res.users", string="Requested by", index=True, default=lambda self: self.env.user.name)
    date = fields.Datetime("Requested Date", default= fields.Datetime.now(), readonly=True)
    department = fields.Many2one('hr.department', string='Department',default=lambda self: self.env.user.department_id)
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 index=True, default=lambda self: self.env.company.id, readonly=True)

    details = fields.One2many('droga.bdr.requests.detail','header',string='Product Details', tracking=True)

    description = fields.Text(string='Product/Project Description')
    private_tender = fields.Selection([
        ('private', 'Private'),
        ('tender', 'Tender'),
        ('both', 'Both')
    ], string='Is it for Private, Tender or Both?')
    competitors = fields.Many2many('market.competitors', string='Name of Competitors')
    price = fields.Float(string='Ethiopian Average Current Price in ETB')
    sales_forecast = fields.Float(string='Annual Sales Forecast')
    remark = fields.Text(string='Remark')
    state = fields.Selection([("accepted", "Accepted"), ("rejected", "Rejected")])

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('droga.reg.master.custom.sequence')

        vals['request_no'] = sequence
        return super(droga_bussiness_dev_requests, self).create(vals)

    def update_request_status(self, request_number):
        request = self.search([('request_no', '=', request_number)], limit=1)
        if request:
            request.status = 'reviewed'

    def submit_req(self):
        for record in self:
            record.status = 'submitted'


class droga_bussiness_dev_detail(models.Model):
    _name = "droga.bdr.requests.detail"

    header = fields.Many2one('droga.bdr.requests.header', string="Header")

    description = fields.Text(string='Product/Project Description')
    private_tender = fields.Selection([
        ('private', 'Private'),
        ('tender', 'Tender'),
        ('both', 'Both')
    ], string='Is it for Private, Tender or Both?')
    competitors = fields.Many2many('market.competitors', string='Name of Competitors')
    price = fields.Float(string='Ethiopian Average Current Price in ETB')
    sales_forecast = fields.Float(string='Annual Sales Forecast')
    remark = fields.Text(string='Remark')
    state = fields.Selection( [("accepted", "Accepted"), ("rejected", "Rejected")])

