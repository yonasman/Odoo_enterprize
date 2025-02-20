from odoo import _, api, fields, models
from datetime import datetime


class ForeignCurrencyRequest(models.Model):
    _name = 'droga.account.foreign.currency.request'
    _description = 'Foreign Currency Request'

    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']

    def _get_employee_id(self):
        # assigning the related employee of the logged in user
        employee_rec = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    def _get_department_id(self):
        # assigning the related employee of the logged in user
        employee_rec = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.department_id

    name = fields.Char("Request Number")
    rfq_id = fields.Many2one("droga.purhcase.request.rfq")
    proforma_invoice_no = fields.Char(
        related="rfq_id.proforma_invoice_no", store=True)
    nbe_number = fields.Char("NBE")
    request_type = fields.Selection(
        [('Normal', 'Normal'), ('Urgent', 'Urgent')], default="Normal")
    request_by = fields.Many2one(
        "hr.employee", string="Requested By", required=True, default=_get_employee_id)
    request_date = fields.Datetime(
        "Request Date", required=True, default=datetime.today())
    payment_due_date = fields.Datetime("Payment Due Date", required=True)
    department = fields.Many2one(
        "hr.department", string="Department", required=True, default=_get_department_id)

    purpose = fields.Char("Purpose")

    supplier_id = fields.Many2one("res.partner")

    approvals = fields.One2many(
        'studio.approval.entry', 'res_id', string='Approvals')

    company_id = fields.Many2one(
        'res.company', 'Company', required=True, default=lambda self: self.env.company.id)

    currency_id = fields.Many2one(
        "res.currency", string="Currency", required=True)

    bank = fields.Many2one("res.bank")
    bank_branch = fields.Char("Branch")

    total_amount = fields.Float("Total Amount USD")
    exchange_rate = fields.Float("Exchange Rate", default=1, digits=(12, 4))
    total_amount_etb = fields.Float(
        "Total Amount ETB", compute="_compute_total", store=True)
    amount_in_word = fields.Char(
        "Amount in Word", compute="_compute_amount_to_word", store=True)

    request_approved_date = fields.Date("Approved Date")

    state = fields.Selection([('Draft', 'Draft'), ("Queued", "Queued"),
                              ('On Progress', 'On Progress'), ('Approved', 'Approved'), ('Cancelled', 'Cancelled')],
                             default="Draft", tracking=True)

    @api.model
    def create(self, vals):
        # get sequence number for each company
        company_id = vals.get('company_id', self.default_get(
            ['company_id'])['company_id'])

        self_comp = self.with_company(company_id)

        # generate transaction number
        sequence_no = self.env['droga.finance.utility'].get_transaction_no('FCR', vals['request_date'],
                                                                           company_id)
        vals['name'] = sequence_no or '/'

        res = super(ForeignCurrencyRequest, self_comp).create(vals)
        return res

    # compute total ETB amount

    @api.depends('total_amount', 'exchange_rate')
    def _compute_total(self):
        for record in self:
            record.total_amount_etb = record.total_amount * record.exchange_rate

    @api.depends('total_amount', 'exchange_rate')
    def _compute_amount_to_word(self):
        for record in self:
            record.amount_in_word = str(record.currency_id.amount_to_text(
                record.total_amount))

    def queued_request(self):
        self.write({'state': 'Queued'})
        return True

    def on_progress_request(self):
        self.write({'state': 'On Progress'})
        self.send_notfication_on_approval('On Progress')
        return True

    def approve_request(self):
        self.write({'state': 'Approved'})
        self.send_notfication_on_approval('Approved')
        return True

    def cancel_request(self):
        self.write({'state': 'Cancelled'})
        return True

    def reject_request(self):
        self.write({'state': 'Draft'})
        return True

    def send_notfication_on_approval(self, approval_type):
        purchase_group = self.env.ref('droga_procurement.group_purchase_procurement_manager_group')
        purchase_user = self.env['res.users'].search(
            [('groups_id', '=', purchase_group.ids)])

        notification_ids = []

        if approval_type == "On Progress":
            message = 'Your request for foreign currency with Request #' + self.name + " for RFQ #" + self.rfq_id.name + " is on progress"
        else:
            message = 'Your request for foreign currency with Request #' + self.name + " for RFQ #" + self.rfq_id.name + " is approved by the bank of " + self.bank.name

        for purchase in purchase_user:
            notification_ids.append((0, 0, {
                'res_partner_id': purchase.partner_id.id,
                'notification_type': 'inbox'}))

        self.message_post(body=message, message_type="notification",
                          author_id=self.env.user.partner_id.id,
                          notification_ids=notification_ids)
