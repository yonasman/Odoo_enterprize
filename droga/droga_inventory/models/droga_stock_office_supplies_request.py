import json
from operator import mod
from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools.view_validation import READONLY
from datetime import datetime


class droga_stock_office_supplies(models.Model):
    _name = 'droga.inventory.office.supplies.request'
    _description = "Store Requisition"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name desc"

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
    @api.depends('detail_entries.total_price')
    def compute_total_purchase_amount(self):
        total = 0
        for record in self.detail_entries:
            total += record.total_price

        self.total_amount = total

    # set default warehouse
    def _default_warehouse(self):
        # get office supplies tore
        return self.env['stock.warehouse'].search([('code', '=', 'OF')], limit=1).id

    def identify_requester(self):
        context = self._context

        if context.get('uid') == self.create_uid.id:
            self.requester = True
        else:
            self.requester = False

    def get_current_user_id(self):
        context = self._context
        return context.get('uid')

    name = fields.Char('Name', default='New')

    # for approvers
    requester = fields.Boolean('Requester', default=False, compute='identify_requester')

    requested_by = fields.Many2one(
        "hr.employee", string="Requested By", required=True, default=_get_employee_id)
    request_date = fields.Datetime('Request Date', default=fields.Datetime.now,
                                   state={'draft': [('readonly', False)]})
    department = fields.Many2one(
        "hr.department", string="Department", required=True, default=_get_department_id)

    warehouse = fields.Many2one('stock.warehouse', default=_default_warehouse)

    product_type = fields.Selection([('Technical', 'Technical'), ('Non Technical', 'Non Technical')],
                                    default='Non Technical')

    request_type = fields.Selection(
        [("Local", "Local"), ("Pharmacy", "Pharmacy")], default="Local", readonly=True)

    purpose = fields.Char("Purpose")

    detail_entries = fields.One2many(
        'droga.inventory.office.supplies.request.detail', 'request_header')

    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company, required=True)

    currency_id = fields.Many2one(
        "res.currency", string="Currency",
        default=lambda self: self.env.company.currency_id)

    # request_reference = fields.Text(string='Request reference', readonly=True)
    request_picking = fields.One2many('stock.picking', 'office_request')

    approvals = fields.One2many(
        'studio.approval.entry', 'res_id', string='Approvals')

    department_manager = fields.Many2one(
        "hr.employee", compute="_get_manager_id", store=True)
    department_manager_user_id = fields.Many2one(
        related="department_manager.user_id", store=True)

    branch = fields.Many2one("account.analytic.account", string="Cost Center", domain=[
        ('plan_id', '=', 'Cost Center')])

    total_amount = fields.Float(
        "Total Amount", compute="compute_total_purchase_amount", store=True)

    state = fields.Selection([
        ('draft', 'Draft'),

        # when the user the submitted the draft request
        ("submit", "Submitted"),
        ("verify", "Verified"),  # when the department manger approved it
        # when the budget department approved the budget
        ("Budget Approval", "Budget Approved"),
        ('waiting', 'Waiting'),  # When request is processed
        ('processed', 'Processed'),  # When request is processed
        ('done', 'Received'),  # When request is received
        ('cancel', 'Cancelled'),  # When requester cancels it from draft
    ], string='Status', default="draft", readonly=True, tracking=True,
        help=" * Requested: The transfer is requested to the sending warehouse.\n"
             " * Done: The transfer is approved and processed.\n")

    # if the request is approved by department manager check this option
    approve_dept_manger = fields.Boolean("By Department", default=False,
                                         help="The request will be approved by the department manager")

    @api.model
    def create(self, vals_list):
        if vals_list.get('name', 'New') == 'New':
            if len(vals_list['detail_entries']) == 0:
                raise UserError(
                    "At least one product must be requested to save record.")

        res = super(droga_stock_office_supplies, self).create(vals_list)

        request_type = res.request_type

        # generate transaction number
        if request_type == 'Local':
            sequence_no = self.env['droga.finance.utility'].get_transaction_no('STR', vals_list['request_date'],
                                                                               vals_list['company_id'])
        elif request_type == 'Pharmacy':
            sequence_no = self.env['droga.finance.utility'].get_transaction_no('STRP', vals_list['request_date'],
                                                                               vals_list['company_id'])

        if not sequence_no:
            raise UserError("Request sequence not found.")

        res.name = sequence_no or '/'

        return res

    # submit action
    def action_submit(self):
        self.state = "submit"

        self.set_activity_done()
        self._get_manager_id()
        if not self.department_manager:
            raise ValidationError(
                "A manager is not set for the requester, please contact HR to set manager for your employee record")
        # create activity for the approver
        # self.create_activity(self.department_manager_user_id.id)
        self.create_activity(self.department_manager_user_id.id)

    # verify request
    def action_verify(self):
        if self.create_uid.id == self.get_current_user_id():
            raise ValidationError(
                "You can't approve your request!")

        self.state = "verify"

    # cancel request
    def action_cancel(self):  # If there is reserved items, cancel them
        self.state = 'cancel'

    # rejet request
    def action_reject(self):
        self.state = 'draft'

    # budget checked
    def action_budget_check(self):
        # check for budgetary position and expense account
        for record in self.detail_entries:
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

        self.state = 'Budget Approval'
        return True

    def action_request(self):

        # validate issue quantity
        self.validate_issue_qty()

        picking_id = None

        wh = self.env['stock.warehouse'].search([('code', '=', 'OF')])

        pick_type_id = self.env['stock.picking.type'].sudo().search(
            [('sequence_code', '=', 'MTOV'), ('warehouse_id', 'like', wh.id)]).id
        if not pick_type_id:
            raise UserError(
                "Picking type 'MTOV' is not configured for office supplies.")

        pick_type_id = self.env['stock.picking.type'].sudo().search(
            [('sequence_code', '=', 'MTOV'), ('warehouse_id', '=', wh.id)]).id
        def_location_id = self.env['stock.location'].search(
            [('complete_name', 'like', wh.code + '/Stock%'), ('usage', '=', 'internal')])[0].id
        def_dest_id = self.env['stock.location'].search(
            [('name', 'like', 'Office%'), ('con_type', '=', 'INC')])

        if not def_location_id:
            raise UserError(
                "Default internal location is not configured for source warehouse.")
        if not def_dest_id:
            raise UserError(
                "Default expense location 'Office supplies expense' is not configured for office supplies.")

        item_lines_available = 0
        for rec in self.detail_entries:
            if rec.avaliable_qty != 0:
                item_lines_available += 1

        if item_lines_available != 0:
            picking_vals = {
                'partner_id': self.company_id.partner_id.id,
                'company_id': self.env.company.id,
                'picking_type_id': pick_type_id,
                'location_id': def_location_id,
                'location_dest_id': def_dest_id[0].id,
                # 'auto_generated': True,
                'origin': self.name,
                # 'state': 'draft',
                'state': 'waiting',
                'office_request': self.id,
                'scheduled_date': self.request_date
            }
            picking_id = self.env['stock.picking'].sudo().create(picking_vals)

        # if not self.request_reference:
        #    self.request_reference = picking_id.name + '\n'
        # else:
        #    self.request_reference = self.request_reference + picking_id.name + '\n'

        for rec in self.detail_entries:
            if rec['avaliable_qty'] != 0:
                move_vals = {
                    'picking_id': picking_id.id,
                    'picking_type_id': pick_type_id,
                    'name': picking_id.name,
                    'product_id': rec['product_id'].id,
                    'product_uom': rec['product_uom'].id,
                    'product_uom_qty': rec['avaliable_qty'],
                    'location_id': def_location_id,
                    'location_dest_id': def_dest_id[0].id,
                    # 'state': 'draft',          Confirmed is waiting status
                    'state': 'waiting',
                    'company_id': self.env.company.id
                }

                self.env['stock.move'].sudo().create(move_vals)

        if picking_id.ids:
            self.state = 'waiting'
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': "You can't create stoke if there is no available quantity in the stock",
                    'type': 'danger',
                    'sticky': False
                }
            }

    def validate_issue_qty(self):
        for record in self.detail_entries:
            if record.avaliable_qty > record.stock_balance or record.avaliable_qty > record.product_uom_qty:
                raise UserError(
                    "Issue quantity can’t be greater than the requested quantity or stock balance available")
            elif record.avaliable_qty <= 0:
                raise UserError(
                    "Issue can't be zero or less than zero")

    def action_receive(self):
        self.state = 'done'

    def action_create_purchase_request(self):
        states = ['Budget Approval', 'waiting', 'processed']
        if self.state not in states:

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': "You can't create purchase request before the request approved",
                    'type': 'danger',
                    'sticky': False
                }
            }
        else:
            # check if there is no purchase related with the rfq
            purchase_requests = self.env['droga.purchase.request.local'].search(
                [('store_request_id', '=', self.id), ('state', '!=', 'Cancel')])

            if purchase_requests.ids:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': 'Purchase request for the current Store Requisition is already created',
                        'type': 'danger',
                        'sticky': False
                    }
                }

        items_for_purchase_request = 0
        for record in self.detail_entries:
            if record.unavilable_qty != 0:
                items_for_purchase_request += 1

        if items_for_purchase_request == 0:

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'All items are issued, you can’t create purchase requests for issued items',
                    'type': 'danger',
                    'sticky': False
                }
            }
        else:
            # create purchase request
            vals = {
                'name': 'New',
                'state': 'Budget Approved',
                'request_type': 'Local',
                'purpose': self.purpose,
                'branch': self.branch.id,
                'request_by': self.requested_by.id,
                'department': self.department.id,
                'request_date': self.env.cr.now(),
                'store_request_id': self.id,
                'request_type': self.request_type,
                'company_id': self.env.company.id,

            }
            vals['purchase_request_lines'] = []

            for line in self.detail_entries:
                if line.unavilable_qty != 0:
                    order_line_vals = (0, 0, {
                        'product_id': line.product_id.product_variant_id.id,
                        'product_qty': line.unavilable_qty,
                        'product_uom': line.product_uom.id,
                        'unit_price': line.unit_price,
                        'budgetary_position': line.budgetary_position.id,
                        'expense_account': line.expense_account.id

                    })

                    vals['purchase_request_lines'].append(order_line_vals)

            # create purchase request
            purchase_request = self.env['droga.purchase.request.local'].create(vals)
            if purchase_request.ids:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': 'Purchase Request created successfully!',
                        'type': 'success',
                        'sticky': False
                    }
                }

    def set_activity_done(self):
        activity = self.env["mail.activity"].search(
            [('res_name', '=', self.name)])
        if activity:
            activity.sudo().action_done()

    def create_activity(self, user_id):
        # create mail activity for the approval
        todos = dict(res_id=self.id,
                     res_model_id=self.env['ir.model'].search(
                         [('model', '=', 'droga.inventory.office.supplies.request')]).id,
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

    @api.depends("department")
    def _get_manager_id(self):
        for record in self:
            if record.approve_dept_manger:
                record.department_manager = record.department.manager_id
            else:
                record.department_manager = record.requested_by.parent_id


class droga_stock_transfer_office_supplies_request_detail(models.Model):
    _name = 'droga.inventory.office.supplies.request.detail'
    request_header = fields.Many2one(
        'droga.inventory.office.supplies.request', required=True)

    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company, required=True)
    product_id = fields.Many2one(
        'product.template', 'Product',
        check_company=True,
        index=True, required=True,
        state={'done': [('readonly', True)]})
    product_uom_qty = fields.Float(
        'Request',
        digits='Product Unit of Measure', store=True,
        default=1.0, required=True, state={'done': [('readonly', True)]})
    # available_qty = fields.Float('Available', readonly=True, compute="get_count")

    product_uom = fields.Many2one('uom.uom', "UoM", store=True, compute='get_uom', inverse='set_uom', required=True,
                                  domain="[('category_id', '=', product_uom_category_id)]")
    # product_uom = fields.Many2one('uom.uom', "UoM", required=True, domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(
        related='product_id.uom_id.category_id', store=True)

    unit_price = fields.Float('Unit Price')
    total_price = fields.Float(
        'Total Price', compute="_compute_total", store=True)

    budgetary_position = fields.Many2one("account.budget.post")
    expense_account = fields.Many2one("account.account")

    remaining_budget = fields.Float(
        "Remaining Budget", compute="_get_remaining_budget", store=True)

    avaliable_qty = fields.Float("Available Qty")
    unavilable_qty = fields.Float(
        "Unavilable Qty", compute="compute_unavilable_qty")

    stock_balance = fields.Float(
        "Stock Balance", compute='_compute_current_stock_balance')

    @api.depends('product_uom_qty', 'unit_price')
    def _compute_total(self):
        for record in self:
            record.total_price = record.unit_price * record.product_uom_qty
            record.avaliable_qty = record.product_uom_qty

    # @api.depends( 'product_uom_qty', 'product_id', 'product_uom')
    def get_count(self):
        loc_id = self.env['stock.location'].search(
            [('name', 'like', 'Office supplies expense')])[0].id
        for rec in self:
            try:
                rec.available_qty = self.env['stock.quant']._get_available_quantity(rec.product_id,
                                                                                    loc_id) * rec.product_uom.factor

            except Exception as e:
                rec.available_qty = 0

    @api.onchange('product_id')
    def get_uom(self):
        for rec in self:
            rec.product_uom = rec.product_id.uom_id

            # display only non-technical items
            if rec.request_header.product_type == 'Technical':
                product_categories = self.env['product.category'].search([('off_supplies', '=', False)]).ids
            else:
                product_categories = self.env['product.category'].search([('off_supplies', '=', True)]).ids

            return {'domain': {'product_id': [('categ_id', 'in', (product_categories))]}}

    def set_uom(self):
        pass

    @api.onchange('budgetary_position', 'expense_account')
    def _load_budgetary_position_accounts(self):
        accounts = self.budgetary_position.account_ids.ids
        return {'domain': {'expense_account': [('id', 'in', (accounts))]}}

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
            if record.budgetary_position.id and record.request_header.branch.id and record.expense_account.id:
                self.env.cr.execute("""select distinct b.account,a.general_budget_id,a.analytic_account_id,sum(b.remaining_balance) as remaining_balance from crossovered_budget_lines a 
    inner join crossovered_budget_lines_detail b on a.id=b.budgetary_position_id 
    where a.general_budget_id=%s and a.analytic_account_id=%s and b.account=%s and (a.date_from>=%s and a.date_to<=%s)
    group by b.account,a.general_budget_id,a.analytic_account_id """, (
                    record.budgetary_position.id, record.request_header.branch.id, record.expense_account.id, date_from,
                    date_to))
                res = self.env.cr.dictfetchone()

                # update remaining balance
                if res != None:
                    record.remaining_budget = res['remaining_balance']

    @api.depends('avaliable_qty')
    def compute_unavilable_qty(self):
        for record in self:
            record.unavilable_qty = record.product_uom_qty - record.avaliable_qty

    # @api.depends('product_id', 'request_header.warehouse')
    def _compute_current_stock_balance(self):
        for record in self:
            # search available quantity
            available_quantity = self.env['stock.quant'].search(
                [('location_id', '=', record.request_header.warehouse.lot_stock_id.id),
                 ('product_tmpl_id', '=', record.product_id.id)],
                limit=1).available_quantity
            record.stock_balance = available_quantity

    @api.onchange("product_id")
    def get_standard_price(self):
        for record in self:
            record.unit_price = record.product_id.standard_price
