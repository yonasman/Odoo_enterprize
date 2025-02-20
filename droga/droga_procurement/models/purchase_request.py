from math import fabs
from odoo import _, api, fields, models
from datetime import datetime
from odoo.exceptions import ValidationError


class purhcase_request(models.Model):
    _name = 'droga.purhcase.request'
    _description = 'Purchase Request'
    _order = "name desc"

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

    # compute total purchase amount
    @api.depends('purhcase_request_lines.total_price')
    def compute_total_purchase_amount(self):
        total = 0
        for record in self.purhcase_request_lines:
            total += record.total_price

        self.total_amount = total

    def get_current_uid(self):
        for record in self:
            if self.env.context.get('uid', False):
                record.current_uid = self.env.context.get('uid', False)
            else:
                record.current_uid = False

            if record.department_manager_user_id == record.current_uid:
                record.is_department_manager = True
            else:
                record.is_department_manager = False

    def identify_requester(self):
        context = self._context

        if context.get('uid') == self.create_uid.id:
            self.requester = True
        else:
            self.requester = False

    # for approvers
    requester = fields.Boolean('Requester', default=False, compute='identify_requester')

    current_uid = fields.Integer(compute='get_current_uid')
    is_department_manager = fields.Boolean(compute='get_current_uid')

    name = fields.Char('Request Reference', required=True,
                       index=True, copy=False, default='New')
    request_type = fields.Selection(
        [("Local", "Local"), ("Foregin", "Foregin")], default="Local")
    request_by = fields.Many2one(
        "hr.employee", string="Requested By", required=True, default=_get_employee_id)
    request_date = fields.Datetime(
        "Request Date", required=True, default=datetime.today())
    department = fields.Many2one(
        "hr.department", string="Department", required=True, default=_get_department_id)
    purpose = fields.Char("Purpose")

    request_purpose = fields.Selection([('Refill', 'Refill'), ('Tender', 'Tender'), ('Emergency', 'Emergency')])

    purhcase_request_lines = fields.One2many(
        "droga.purhcase.request.line", "purhcase_request_id", required=True)

    purhcase_request_lines_expectetd = fields.One2many(
        "droga.purhcase.request.line", "purhcase_request_id", required=True)

    purhcase_request_lines_market_analysis = fields.One2many(
        "droga.purhcase.request.line", "purhcase_request_id", required=True)

    purhcase_request_lines_foregin_supp_list = fields.One2many(
        "droga.purhcase.request.line", "purhcase_request_id", required=True)

    purhcase_request_lines_foregin_competitors = fields.One2many(
        "droga.purhcase.request.line", "purhcase_request_id", required=True)

    purchase_analysis_report = fields.One2many(
        "droga.purhcase.request.line", "purhcase_request_id")

    state = fields.Selection(
        [("Draft", "Draft"), ("Submitted", "Submitted"), ("Verified", "Verified"),
         ("Budget Approved", "Budget Approved"), ("Procurement Manager", "PR Manager Approved"),
         ("Approved", "Ceo Approved"), ("Cancel", "Canceled")], default="Draft", tracking=True)

    wf_state = fields.Selection(
        [('On Progress', 'On Progress'), ('Approved', 'Approved')], default="On Progress")

    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 index=True, default=lambda self: self.env.company.id)

    currency_id = fields.Many2one(
        "res.currency", string="Currency", required=True,
        default=lambda self: self.env.company.currency_id)

    exchange_rate = fields.Float(
        "Exchange Rate", required=True, default=1.00, digits=(12, 4))

    approvals = fields.One2many(
        'studio.approval.entry', 'res_id', string='Approvals')

    buying_method = fields.Selection([("RFQ", "RFQ"), ("Bid", "Bid")])
    rfqs = fields.One2many('droga.purhcase.request.rfq',
                           'purhcase_request_id', string='RFQ')

    foregin_phase_rfqs = fields.One2many(
        "droga.purchase.foregin.status", "purchase_request_id_rfq_phase")

    # approvers
    department_manager = fields.Many2one(
        "hr.employee", compute="_get_manager_id", store=True)
    department_manager_user_id = fields.Many2one(
        related="department_manager.user_id", store=True)

    branch = fields.Many2one("account.analytic.account", string="Cost Center", domain=[
        ('plan_id', '=', 'Cost Center')])

    total_amount = fields.Float(
        "Total Amount", compute="compute_total_purchase_amount", store=True)

    is_user_import_operation = fields.Boolean(string="check field", compute='get_import_operation_group')

    reject_message = fields.Char('Reason')

    rfq_count = fields.Integer("RFQ Count", compute='compute_rfq_count', default=0)
    rfq_status = fields.Char("RFQ Status", compute="compute_rfq_status")

    dummy_count = fields.Integer(compute="count_linked_documents", string="Dummy Count")
    pr_count1 = fields.Integer(store=True, string="PR Count")
    rfq_count1 = fields.Integer(store=True, string="RFQ Count")
    po_count1 = fields.Integer(store=True, string="PO Count")
    grn_count1 = fields.Integer(store=True, string="GRN Count")

    pr_grn_receive_status = fields.Selection([('Received', 'Received'), ('Not Received', 'Not Received')], store=True,
                                             default='Not Received')

    def compute_rfq_status(self):
        # set rfq status to not created
        for record in self:
            record.rfq_status = "Not Created"
            for rfq in record.rfqs:
                if rfq.state != 'Cancel':
                    record.rfq_status = rfq.state
                    break

    def compute_rfq_count(self):
        for record in self:
            count = 0
            for rec in record.rfqs:
                count += 1
            record.rfq_count = count

    @api.depends('is_user_import_operation', 'request_by')
    def get_import_operation_group(self):
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        if res_user.has_group('droga_procurement.group_purchase_import_operation_group'):
            self.is_user_import_operation = True
        else:
            self.is_user_import_operation = False

    @api.depends("department")
    def _get_manager_id(self):
        # for record in self:
        # record.department_manager = record.request_by.parent_id

        # get groups
        group = self.env["res.groups"].search([('full_name', '=', 'Purchase Foreign Request Verify')])

        for user in group.users:
            for employee in user.employee_ids:
                self.department_manager = employee

    @api.model
    def create(self, vals):
        # get sequence number for each company
        company_id = vals.get('company_id', self.default_get(
            ['company_id'])['company_id'])

        self_comp = self.with_company(company_id)

        # generate transaction number
        sequence_no = self.env['droga.finance.utility'].get_transaction_no('PRF', vals['request_date'],
                                                                           vals['company_id'])
        vals['name'] = sequence_no or '/'

        res = super(purhcase_request, self_comp).create(vals)

        return res

    def write(self, vals):

        res = super(purhcase_request, self).write(vals)
        # calculate total purchase price

        return res

    # submit request
    def submit_request(self):
        if len(self.purhcase_request_lines) == 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'At least one product must be requested to submit the request.',
                    'type': 'danger',
                    'sticky': False
                }
            }

        self.write({'state': 'Submitted', 'reject_message': ''})
        self.set_activity_done()
        self._get_manager_id()
        if not self.department_manager:
            raise ValidationError(
                "A manager is not set for the requester, please contact HR to set manager for your employee record")
        # create activity for the approver
        self.create_activity(self.department_manager_user_id.id)
        return True

    # draft request
    def draft_request(self):
        self.write({'state': 'Draft'})
        return True

    # verify request
    def verify_request(self):
        self.write({'state': 'Verified'})
        # mark activity as done
        self.set_activity_done()

        # create new activity
        # get budget accountant
        users = self.get_users_for_roles('Business Control Specialist')
        for user in users:
            self.create_activity(user)

        return True

    # rejet request
    def reject_request(self):
        self.write({'state': 'Draft'})
        self.set_activity_done()
        self.create_reject_activity()
        return True

    def cancel_request(self):
        self.write({'state': 'Cancel'})
        self.cancel_commitment_budget()
        return True

    # budget checked
    def budget_checked_request(self):
        # check for budgetary position and expense account
        for record in self.purhcase_request_lines:
            if not record.budgetary_position.ids or not record.expense_account.ids:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': 'Budget category or expense account can''t be empty',
                        'type': 'danger',
                        'sticky': False
                    }
                }

        self.write({'state': 'Budget Approved'})
        self.record_commitment_budget()

        # activity done
        self.set_activity_done()
        # create new activity
        # get budget accountant
        users = self.get_users_for_roles('CEO')
        for user in users:
            self.create_activity(user)

        return True

    def approve_request_pr_manager(self):
        self.write({'state': 'Procurement Manager'})
        if self.total_amount <= 100000:
            self.write({'wf_state': 'Approved'})
            self.send_notification_on_approval()
        return True

    # approve request
    def approve_request(self):
        self.write({'state': 'Approved'})
        self.write({'wf_state': 'Approved'})
        # record commitment budget

        self.set_activity_done()
        self.send_notification_on_approval()
        return True

    def open_rfq(self):
        view = self.env.ref(
            'droga_procurement.droga_purhcase_request_view_tree')

        return {
            'name': 'RFQ',
            'view_mode': 'tree,form',
            'res_model': 'droga.purhcase.request.rfq',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'res_id': self.id
        }

    def load_foregin_purchase_status(self):
        # get phase 1 or request for quotation steps
        rfq_steps = self.env["droga.foregin.purchase.phases"].search([])

        for rfq_step in rfq_steps:
            # create record in rfq step status one2manyobject
            status = {'purchase_request_id_rfq_phase': self.id,
                      'phase': rfq_step.id,
                      'status': 'Not Started'}
            # create the record in database
            sta = self.env['droga.purchase.foregin.status'].create(status)

    def record_commitment_budget(self):
        # record commitement budget when the budget approves
        for record in self:
            if record.state == "Budget Approved":
                # total purchase amount
                lines_include_in_total = []
                for line in record.purhcase_request_lines:
                    # create commitment record
                    commitment_budget = {
                        'document_type': 'PR',
                        'purchase_request_id': record.id,
                        'purchase_request_total_amount': line.total_price,
                        'budget_date': record.request_date,
                        'budgetary_position': line.budgetary_position.id,
                        'expense_account': line.expense_account.id,
                        'analytic_account_id': self.branch.id,
                        'company_id': record.company_id.id,
                        'state': 'Active'
                    }

                    # persist to database
                    self.env['droga.budget.commitment.budget'].create(
                        commitment_budget)

    def cancel_commitment_budget(self):
        records = self.env['droga.budget.commitment.budget'].search(
            [('purchase_request_id', '=', self.id), ('state', '=', 'Active')])
        for record in records:
            record.write({'state': 'Closed'})

    def set_activity_done(self):
        activity = self.env["mail.activity"].search(
            [('res_name', '=', self.name)])
        if activity:
            activity.sudo().action_done()

    def create_activity(self, user_id):
        # create mail activity for the approval
        todos = dict(res_id=self.id,
                     res_model_id=self.env['ir.model'].search([('model', '=', 'droga.purhcase.request')]).id,
                     user_id=user_id, summary='Grant Approval', note='You have a request to approve',
                     activity_type_id=4,
                     date_deadline=datetime.now())

        self.env['mail.activity'].sudo().create(todos)

    def create_reject_activity(self):
        # create mail activity for the approval

        todos = dict(res_id=self.id,
                     res_model_id=self.env['ir.model'].search([('model', '=', 'droga.purhcase.request')]).id,
                     user_id=self.create_uid.id, summary='Request Rejected', note=self.reject_message,
                     activity_type_id=4,
                     date_deadline=datetime.now())

        self.env['mail.activity'].sudo().create(todos)

    def get_users_for_roles(self, role):
        users = []
        roles = self.env['res.groups'].search([('name', '=', role)])

        for user in roles.users:
            users.append(user.id)
        return users

    def reject_box(self):
        view = self.env.ref(
            'droga_procurement.droga_account_purchase_request_foreign_reject_view_form')

        return {
            'name': 'Reject',
            'view_mode': 'form',
            'res_model': 'droga.purhcase.request',
            'view_id': view.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id
        }

    def send_notification_on_approval(self):
        purchase_group = self.env.ref('droga_procurement.group_purchase_procurement_manager_group')
        purchase_user = self.env['res.users'].search(
            [('groups_id', '=', purchase_group.ids)])

        notification_ids = []

        message = "Purchase request #" + self.name + " is approved, please create RFQ"

        for purchase in purchase_user:
            notification_ids.append((0, 0, {
                'res_partner_id': purchase.partner_id.id,
                'notification_type': 'inbox'}))

        subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')

        self.message_post(body=message, message_type="notification",
                          author_id=self.env.user.partner_id.id, subtype_id=subtype_id,
                          notification_ids=notification_ids)

    def change_product_from_droga_to_ema(self):
        records = self.env['droga.purhcase.request.line'].search([('company_id', '=', 2)])

        for rec in records:
            # search product id from ema
            products = self.env['product.product'].search([('name', '=', rec.product_id.name)])
            for product in products:
                if product.company_id.id == 2:
                    rec.product_id = product

        records1 = self.env['droga.purhcase.request.rfq.line'].search([('company_id', '=', 2)])

        for rec in records1:
            # search product id from ema
            products = self.env['product.product'].search([('name', '=', rec.product_id.name)])
            for product in products:
                if product.company_id.id == 2:
                    rec.product_id = product

    @api.depends('name')
    def count_linked_documents(self):

        pr_count = 1
        rfq_count = 0
        po_count = 0
        grn_count = 0

        for record in self:
            record.dummy_count = 1
            # get current object
            current_object = self.env['droga.purhcase.request'].search(
                [('id', '=', record.id), ('state', '!=', 'canceled')])

            # search rfq count
            rfq_count = self.env['droga.purhcase.request.rfq'].search_count(
                [('purhcase_request_id', '=', record.id)])
            # search rfq's
            rfqs = self.env['droga.purhcase.request.rfq'].search([('purhcase_request_id', '=', record.id)])

            for rfq in rfqs:
                # search po's
                po_count = self.env['purchase.order'].search_count(
                    [('rfq_id', '=', rfq.id)])

                # search po's then recived grn
                pos = self.env['purchase.order'].search([('rfq_id', '=', rfq.id)])

                for po in pos:
                    # count grns
                    grn_count = self.env['stock.picking'].search_count(
                        [('origin', '=', po.name), ('state', '=', 'done')])

                    if record.grn_count1 > 0:
                        record.pr_grn_receive_status = 'Received'

            # update counts
            for xx in current_object:
                xx.pr_count1 = pr_count
                xx.rfq_count1 = rfq_count
                xx.po_count1 = po_count
                xx.grn_count1 = grn_count


class purhcase_request_line(models.Model):
    _name = "droga.purhcase.request.line"
    _description = "Purchase Request Line"
    _rec_name = 'product_id'

    seq_no = fields.Integer("No", compute='compute_sequence_no')
    purhcase_request_id = fields.Many2one("droga.purhcase.request")
    current_market_status = fields.One2many('droga.purchase.request.line.current.market.analysis',
                                            'purchase_request_line_id')
    future_market_status = fields.One2many('droga.purchase.request.line.future.market.status',
                                           'purchase_request_line_id')
    vendor_list = fields.One2many('droga.purchase.request.line.vendors',
                                  'purchase_request_line_id')

    exchange_rate = fields.Float(
        related="purhcase_request_id.exchange_rate", store=True)
    company_id = fields.Many2one(
        'res.company', related='purhcase_request_id.company_id', string='Company', store=True, readonly=True)
    status = fields.Selection(
        [("Draft", "Draft"), ("Submitted", "Submitted"), ("Verified", "Verified"), ("Budget Checked", "Budget Checked"),
         ("Approved", "Approved"), ("Cancel", "Canceled")], default="Draft", tracking=True,
        related='purhcase_request_id.state')
    product_id = fields.Many2one('product.product', string='Product', domain=[
        ('purchase_ok', '=', True)], change_default=True)
    product_category = fields.Many2one(related='product_id.categ_id', store=True)
    product_qty = fields.Float(
        string='Quantity', digits='Product Unit of Measure', required=True, default=1)

    product_tmpl_id = fields.Many2one(related='product_id.product_tmpl_id', store=True)

    is_core_product = fields.Boolean("Core product", compute="_compute_product_values",
                                     inverse='_inverse_product_values', store=True)

    unit_price = fields.Float('Unit Price', digits=(12, 4))
    total_price = fields.Float(
        'Total Price', compute="_compute_total", store=True, digits=(12, 4))

    unit_price_foregin = fields.Float('Unit Price', digits=(12, 4))
    total_price_foregin = fields.Float(
        'Total Price', compute="_compute_total", store=True, digits=(12, 4))

    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  domain="[('category_id', '=', product_uom_category_id)]", required=True)
    product_uom_category_id = fields.Many2one(
        related='product_id.uom_id.category_id')

    budget_product = fields.Boolean('Budget product?')
    expected_average_mon_cons = fields.Float(
        'Expected average monthly consumption')  # Fix me, compute using product master
    current_stock_balance = fields.Float(
        'Current balance', compute='_compute_product_values', inverse='_inverse_product_values',
        store=True)  # Fix me, fetch from inventory
    selling_price_after_arrival = fields.Float('Arrival selling price')
    # Fix me, compute using sales price
    expected_margin = fields.Float('Expected margin')
    arrival_time = fields.Date('Arrival time')

    budgetary_position = fields.Many2one("account.budget.post")
    expense_account = fields.Many2one("account.account")

    remaining_budget = fields.Float(
        "Remaining Budget", compute="_get_remaining_budget", store=True)

    remark = fields.Char("Remark")

    # field for anlysis report
    four_month_order_qty = fields.Float(
        "Four Month Qty", compute="_consumption_total", help="Order Quantity times Average Monthly Consumption",
        store=True)
    six_month_order_qty = fields.Float(
        "Six Month Qty", compute="_consumption_total", help="Order Quantity times Average Monthly Consumption",
        store=True)

    order_qty_and_current_stcok = fields.Float(
        "Order Qty & Current Stock", compute="_consumption_total", help="Order Quantity Plus Current Stock", store=True)

    @api.depends("unit_price", "selling_price_after_arrival")
    def calculate_margin(self):
        for record in self:
            record.expected_margin = ((record.unit_price - record.selling_price_after_arrival) / record.selling_price_after_arrival) * 100

    def compute_sequence_no(self):
        seq_no = 1
        for record in self:
            record.seq_no = seq_no
            seq_no += 1

    @api.depends('product_qty', 'unit_price', 'unit_price_foregin', 'exchange_rate')
    def _compute_total(self):
        for record in self:
            if record.purhcase_request_id.request_type == 'Local':
                record.total_price = record.unit_price * record.product_qty
            else:
                record.total_price = record.unit_price * record.product_qty
                # record.unit_price = record.unit_price_foregin * record.exchange_rate
                # record.total_price = record.unit_price * record.product_qty
                # record.total_price_foregin = record.unit_price_foregin * record.product_qty

    # set unit of measure
    @api.onchange('product_id')
    def set_unit(self):
        for record in self:
            record.product_uom = record.product_id.import_uom_new
            record.is_core_product = record.product_id.is_core_product
            record.current_stock_balance = record.product_id.free_qty

    @api.depends('product_id')
    def _compute_product_values(self):
        for record in self:
            record.is_core_product = record.product_id.is_core_product
            record.current_stock_balance = record.product_id.free_qty

    def _inverse_product_values(self):
        for rec in self:
            for record in self:
                record.product_id.is_core_product = record.is_core_product
                record.product_id.free_qty = record.current_stock_balance

    @api.onchange('budgetary_position', 'expense_account')
    def _load_budgetary_position_accounts(self):
        for record in self:
            accounts = record.budgetary_position.account_ids.ids
            return {'domain': {'expense_account': [('id', 'in', (accounts))]}}

    @api.depends('product_qty', 'expected_average_mon_cons', 'current_stock_balance')
    def _consumption_total(self):
        for record in self:
            record.four_month_order_qty = record.expected_average_mon_cons * 4
            # record.six_month_order_qty = record.expected_average_mon_cons * 6
            if record.expected_average_mon_cons!=0:
                record.six_month_order_qty = (
                                             record.product_qty + record.current_stock_balance) / record.expected_average_mon_cons
            record.order_qty_and_current_stcok = record.product_qty + \
                                                 record.current_stock_balance
        return True

    @api.depends('budgetary_position', 'expense_account')
    def _get_remaining_budget(self):

        now = datetime.today().date()

        if now.month >= 7 and now.day >= 7:
            date_from = datetime(now.year, 7, 8)
            date_to = datetime(now.year + 1, 7, 7)
        else:
            date_from = datetime(now.year - 1, 7, 8)
            date_to = datetime(now.year, 7, 7)

        for record in self:
            # get budget from remaining budget
            if record.budgetary_position.id and record.purhcase_request_id.branch.id and record.expense_account.id:
                self.env.cr.execute("""select distinct b.account,a.general_budget_id,a.analytic_account_id,sum(b.remaining_balance) as remaining_balance from crossovered_budget_lines a 
    inner join crossovered_budget_lines_detail b on a.id=b.budgetary_position_id 
    where a.general_budget_id=%s and a.analytic_account_id=%s and b.account=%s and (a.date_from>=%s and a.date_to<=%s)
    group by b.account,a.general_budget_id,a.analytic_account_id """, (
                    record.budgetary_position.id, record.purhcase_request_id.branch.id, record.expense_account.id,
                    date_from, date_to))
                res = self.env.cr.dictfetchone()

                # update remaining balance
                if res != None:
                    record.remaining_budget = res['remaining_balance']

    def open_detail_market_analysis(self):
        view = self.env.ref(
            'droga_procurement.droga_purchase_request_market_analysis_form')

        return {
            'name': 'Current Market Status',
            'view_mode': 'form',
            'res_model': 'droga.purhcase.request.line',
            'view_id': view.id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
        }

    def open_detail_future_market_status(self):
        view = self.env.ref(
            'droga_procurement.droga_purchase_request_future_market_status_form')

        return {
            'name': 'Future Market Status',
            'view_mode': 'form',
            'res_model': 'droga.purhcase.request.line',
            'view_id': view.id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
        }

    def open_detail_vendors(self):
        view = self.env.ref(
            'droga_procurement.droga_purchase_request_vendor_list_form')

        return {
            'name': 'Vendors',
            'view_mode': 'form',
            'res_model': 'droga.purhcase.request.line',
            'view_id': view.id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
        }


class purchase_request_line_current_market_analysis(models.Model):
    _name = 'droga.purchase.request.line.current.market.analysis'

    purchase_request_line_id = fields.Many2one('droga.purhcase.request.line')

    importer = fields.Many2one("droga.purchase.competitors", string='Importer')
    manufacturer = fields.Many2one('res.partner', domain="[('supplier_rank','!=', 0)]", string="Manufacturer")
    unit = fields.Many2one('uom.uom', string='UoM')
    avail_stock = fields.Float('Available Stock')
    sell_up = fields.Float('Selling Unit Price', digits=(12, 4))
    epss_volume = fields.Float('EPSS Stock Volume')
    local_man_status = fields.Char('Local Manufacturers Stock and RM Status')
    market_analysis_remark = fields.Char('Remark')


class purchase_request_line_future_market_analysis(models.Model):
    _name = 'droga.purchase.request.line.future.market.status'

    purchase_request_line_id = fields.Many2one('droga.purhcase.request.line')
    importer = fields.Many2one("droga.purchase.competitors", string='Importer')
    manufacturer = fields.Char(string='Manufacturer')
    unit = fields.Many2one('uom.uom', string="UoM")
    private_unit_price = fields.Float('Private Unit Price', digits=(12, 4))
    private_unit_quantity = fields.Float('Private Quantity')
    private_order_date = fields.Date('Private Ordered Date')
    epss_unit_ = fields.Float('EPSS Unit Price', digits=(12, 4))
    epss_winner = fields.Char('EPSS Winner Manufacturer')


class purchase_request_line_vendors(models.Model):
    _name = 'droga.purchase.request.line.vendors'

    purchase_request_line_id = fields.Many2one('droga.purhcase.request.line')

    foregin_manufacturer = fields.Many2one('res.partner', domain="[('supplier_rank','!=', 0)]", string="Manufacturer")
    foregin_unit_price = fields.Float('Unit Price')
    foregin_shelf_life = fields.Float('Shelf Life')
    foregin_is_sup_regsitered = fields.Boolean('Registered?', default=True)


class purchase_foregin_status(models.Model):
    _name = "droga.purchase.foregin.status"
    _description = "Status Tracking for Foregin Purchases"

    purchase_request_id_rfq_phase = fields.Many2one(
        "droga.purhcase.request", string="Purchase Request")

    rfq_id = fields.Many2one("droga.purhcase.request.rfq")

    phase = fields.Many2one("droga.foregin.purchase.phases")
    phase_name = fields.Selection(related="phase.phase_name", store=True)
    step = fields.Char(related="phase.step")
    status = fields.Selection(
        [("Not Started", "Not Started"), ("On Progress", "On Progress"), ("Done", "Done")])
    done_date = fields.Date("Done Date")
    remark = fields.Char("Remark")
