import base64
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class Rfq_Local(models.Model):
    _name = 'droga.purchase.request.rfq.local'
    _description = 'Request for Quotation'
    _order = "name desc"

    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']

    @api.model
    def _default_user_team_committee(self):
        if 'default_purchase_request_id' in self._context:
            purchase_request_id = self._context['default_purchase_request_id']
            purchase_request = self.env['droga.purchase.request.local'].search([('id', '=', purchase_request_id)])

            if purchase_request:
                return purchase_request.department_manager.ids

    name = fields.Char('Request Reference', required=True,
                       index=True, copy=False, default='New')
    purchase_request_id = fields.Many2one(
        "droga.purchase.request.local", required=True)
    request_type = fields.Selection(
        related="purchase_request_id.request_type", store=True)

    supplier_id = fields.Many2one('res.partner', string='Supplier')

    date = fields.Datetime("Date", required=True, default=datetime.today())
    rfq_lines = fields.One2many(
        'droga.purchase.request.rfq.line.local', 'rfq_id', required=True)

    suppliers = fields.Many2many(
        'res.partner', string='Suppliers', domain="[('supplier_rank','!=', 0)]")

    remark = fields.Html("Remark")
    technical_remark = fields.Html("Technical remark")

    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 index=True, default=lambda self: self.env.company.id)
    currency_id = fields.Many2one("res.currency", related='company_id.currency_id', string="Currency", readonly=True,
                                  store=True)
    procurement_committee = fields.Many2many("hr.employee", default=_default_user_team_committee)
    state = fields.Selection(
        [("Draft", "Draft"), ("Winner Picked", "Winner Picked"), ("Checked", "Checked"),
         ("Committee Approval", "Committee Approved"),
         ("CEO Approval", "CEO"), ("Cancel", "Canceled")], default="Draft", tracking=True)

    wf_state = fields.Selection(
        [('On Progress', 'On Progress'), ('Approved', 'Approved')], default="On Progress")

    # total winner amount
    total_winner_amount = fields.Float(
        "Total Winner Amount", compute="_compute_total_winner_amount", store=True, default=0)

    approvals = fields.One2many(
        'studio.approval.entry', 'res_id', string='Approvals')

    for_pharmacy = fields.Boolean("For Pharmacy", default=False)

    @api.model
    def create(self, vals):

        company_id = vals.get('company_id', self.default_get(
            ['company_id'])['company_id'])

        # get sequence number for each company
        self_comp = self.with_company(company_id)

        res = super(Rfq_Local, self_comp).create(vals)

        request_type = res.request_type

        # generate transaction number
        if request_type == 'Local':
            sequence_no = self.env['droga.finance.utility'].get_transaction_no('RFQL', vals['date'],
                                                                               vals['company_id'])
            res.name = sequence_no or '/'
        elif request_type == 'Pharmacy':
            sequence_no = self.env['droga.finance.utility'].get_transaction_no('RFQP', vals['date'],
                                                                               vals['company_id'])
            res.name = sequence_no or '/'

        return res

    @api.depends('rfq_lines', 'purchase_request_id', 'state')
    def _compute_total_winner_amount(self):
        for record in self:
            for r in record.rfq_lines:
                if r.winner == "Yes":
                    record.total_winner_amount += r.price_total

    # draft request
    def draft_request(self):
        self.write({'state': 'Draft'})
        return True

    # checked
    def checked(self):
        self.write({'state': 'Checked'})
        if self.state == "Checked":
            self.set_activity_done()
            users = self.get_users_for_roles('Procurement Committee', self.company_id.id)
            for user in users:
                self.create_activity(user)

        return True

    # Committee Approval
    def committee_approval(self):
        self.write({'state': 'Committee Approval'})
        if self.total_winner_amount < 100000:
            self.write({'wf_state': 'Approved'})
        return True

    def operational_approval(self):
        self.write({'state': 'Operation Manager'})
        return True

    def finance_approval(self):
        self.write({'state': 'Finance'})
        return True

    # ceo approval
    def ceo_approval(self):
        self.write({'state': 'CEO Approval'})
        self.write({'wf_state': 'Approved'})
        # self.load_foregin_rfq_status()
        return True

    # reject request
    def reject_request(self):
        self.write({'state': 'Draft'})
        return True

    def cancel_request(self):
        self.write({'state': 'Cancel'})
        return True

    def generate_analysis_sheet(self):

        # validate current data
        if len(self.rfq_lines) != 0:
            raise ValidationError(
                "There are items in the RFQ please remove them if you to generate a new analysis sheet")

        # get invited suppliers list
        suppliers = self.suppliers
        products = self.purchase_request_id.purchase_request_lines

        if suppliers.ids:
            for supplier in suppliers:
                # search supplier in rfq line
                rfq_lines = self.rfq_lines.search(
                    [('rfq_id', '=', self.id), ('supplier_id', '=', supplier.id)])

                if not rfq_lines.ids:
                    # genertare record with each supplier and product
                    for product in products:
                        # create rfq line
                        unit_price = 0
                        if self.request_type == "Pharmacy":
                            unit_price = product.unit_price

                        rfq_line = {
                            'rfq_id': self.id,
                            'supplier_id': supplier.id,
                            'product_id': product.product_id.id,
                            'product_uom': product.product_uom.id,
                            'product_qty': product.product_qty,
                            'unit_price': unit_price
                        }
                        # create rfq line
                        self.env['droga.purchase.request.rfq.line.local'].create(
                            rfq_line)

    def pick_winner(self):

        # validate rfq lines
        self.validae_rfq_lines()

        # update all record to no
        partners = self.env['droga.purchase.request.rfq.line.local'].search(
            [('rfq_id', '=', self.id)])

        for partner in partners:
            partner.write({'winner': 'No'})

        # get product list
        products = self.purchase_request_id.purchase_request_lines.product_id

        # pick winner for each product
        for product in products:
            # get suppliers
            suppliers = self.env['droga.purchase.request.rfq.line.local'].search(
                [('rfq_id', '=', self.id), ('product_id', '=', product.id)])
            winner_supplier = {}
            # pick winner
            if suppliers.ids:
                winner_supplier = suppliers[0]

                for supplier in suppliers:
                    if supplier.unit_price < winner_supplier.unit_price:
                        winner_supplier = supplier

                if winner_supplier:
                    winner_supplier.write({'winner': 'Yes'})

            self.write({'state': 'Winner Picked'})

            self.set_activity_done()

            if self.request_type == "Pharmacy":
                self.write({'wf_state': 'Approved'})
                self.write({'state': 'Committee Approval'})
            else:
                users = self.get_users_for_roles('Procurement Committee', self.company_id.id)
                for user in users:
                    self.create_activity(user)

        return True

    def validae_rfq_lines(self):
        for record in self.rfq_lines:
            if record.unit_price == 0:
                raise ValidationError("Unit price can't be zero")
            elif record.unit_price < 0:
                raise ValidationError("Unit price can't be less than zero")
            elif record.product_qty == 0:
                raise ValidationError("Quantity can't be zero")
            elif record.product_qty < 0:
                raise ValidationError("Quantity can't be less than zero")

    def create_purchase_orders_automatically(self):

        suppliers = []
        # get unique suppliers from the rfq
        for line in self.rfq_lines:
            if line.winner == "Yes" and self.check_supplier(line.supplier_name, suppliers) == 0:
                suppliers.append(line)

        if suppliers:
            # close the status of purchase request commitment budget
            #self.close_purchase_request_commitment_budget()

            for supplier in suppliers:
                vals = {'name': 'New', 'state': 'draft', 'date_order': datetime.now(),
                        'rfq_local_id': supplier.rfq_id.id,
                        'company_id': self.company_id.id, 'from_rfq': True,
                        'partner_id': supplier.supplier_id.id, 'request_type': self.request_type, 'order_line': []}

                # get products the supplier won
                for line in self.rfq_lines:
                    if line.winner == "Yes" and line.supplier_id == supplier.supplier_id:
                        order_line_vals = (0, 0, {
                            'date_planned': fields.Date.today(),
                            'name': line.product_id.name,
                            'price_unit': line.unit_price,
                            'product_id': line.product_id.id,
                            'product_qty': line.product_qty,
                            'product_uom': line.product_uom.id,
                            'product_uom_pharma': line.product_uom.id,
                            'taxes_id': [(6, 0, line.tax_id.ids)]
                        })

                        vals['order_line'].append(order_line_vals)

                # create purchase orders
                purchase_order = self.env['purchase.order'].create(vals)

            # create purchase order commitment budget
            '''for line in self.rfq_lines:
                if line.winner == "Yes":
                    # get budgetary position and expense account from purchase request
                    purchase_request = self.env['droga.purchase.request.line.local'].search(
                        [('purchase_request_id', '=', self.purchase_request_id.id),
                         ('product_id', '=', line.product_id.id)])

                    commitment_budget = {
                        'document_type': 'PO',
                        'purchase_order_id': purchase_order.id,
                        'purchase_order_total_amount': purchase_order.amount_total,
                        'budget_date': purchase_order.date_order,
                        'budgetary_position': purchase_request.budgetary_position.id,
                        'expense_account': purchase_request.expense_account.id,
                        'analytic_account_id': self.purchase_request_id.branch.id,
                        'company_id': self.company_id.id,
                        'state': 'Active'
                    }

                    # persist to database
                    self.env['droga.budget.commitment.budget'].create(
                        commitment_budget)'''

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'Purchase Order Created Successfully',
                'type': 'success',
                'sticky': False
            }
        }

    def check_supplier(self, supplier_name, suppliers):
        count = 0
        for s in suppliers:
            if supplier_name == s.supplier_name:
                count += 1
        return count

    def close_purchase_request_commitment_budget(self):
        commitment_budget = self.env['droga.budget.commitment.budget'].search(
            [('purchase_request_id', '=', self.purchase_request_id.id)])

        for record in commitment_budget:
            record.write({'state': 'Closed'})

    def load_items_from_pr(self, res):

        records = self.env['droga.purchase.request.line.local'].search(
            [('purchase_request_id', '=', res.purchase_request_id.id)])

        for record in records:
            line = {'rfq_id': res.id, 'supplier_id': res.supplier_id.id, 'product_id': record.product_id.id,
                    'product_qty': record.product_qty, 'product_uom': record.product_uom.id, 'unit_price': 0,
                    'winner': 'Yes'}

            self.env['droga.purchase.request.rfq.line.local'].create(line)

    def open_rfq(self):
        return {
            'name': _('Customer Invoice'),
            'view_mode': 'grid',
            'view_id': self.env.ref('droga_procurement.timesheet_view_grid_by_project').id,
            'res_model': 'droga.purchase.request.rfq.line.local',
            'context': "{''}",
            'type': 'ir.actions.act_window',
            'res_id': self.id
        }

    def set_activity_done(self):
        activity = self.env["mail.activity"].search(
            [('res_name', '=', self.name)])
        if activity:
            activity.sudo().action_done()

    def create_activity(self, user_id):
        # create mail activity for the approval
        todos = dict(res_id=self.id,
                     res_model_id=self.env['ir.model'].search([('model', '=', 'droga.purchase.request.rfq.local')]).id,
                     user_id=user_id, summary='Grant Approval', note='You have a request to approve',
                     activity_type_id=4,
                     date_deadline=datetime.now())

        self.env['mail.activity'].sudo().create(todos)

    def get_users_for_roles(self, role, company_id):
        users = []
        roles = self.env['res.groups'].search([('name', '=', role)])

        for user in roles.users:
            if user.company_id.id == company_id:
                users.append(user.id)
        return users


class Rfq_Detail_local(models.Model):
    _name = 'droga.purchase.request.rfq.line.local'
    _description = 'Request for Quotation Detail'
    _order = "supplier_name asc"

    rfq_id = fields.Many2one("droga.purchase.request.rfq.local")
    company_id = fields.Many2one(
        'res.company', related='rfq_id.company_id', string='Company', store=True, readonly=True)
    # related fields
    purchase_request_id = fields.Many2one(related='rfq_id.purchase_request_id')

    purchase_request_lines = fields.One2many(
        related='purchase_request_id.purchase_request_lines')

    supplier_id = fields.Many2one(
        'res.partner', string='Supplier', domain="[('supplier_rank','!=', 0)]")
    supplier_name = fields.Char(related="supplier_id.name", store=True)
    product_id = fields.Many2one('product.product', string='Product', domain=[
        ('purchase_ok', '=', True)], change_default=True)
    product_qty = fields.Float(
        string='Quantity', digits='Product Unit of Measure', required=True, default=1)
    unit_price = fields.Float('Unit Price', required=True)
    total_price = fields.Float(
        'Total Price', compute="_compute_total", store=True)

    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  domain="[('category_id', '=', product_uom_category_id)]", required=True)
    product_uom_category_id = fields.Many2one(
        related='product_id.uom_id.category_id')

    price_subtotal = fields.Float(
        compute='_compute_total', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Float(compute='_compute_total',
                             string='Taxes', readonly=True, store=True)
    price_total = fields.Float(
        compute='_compute_total', string='Total', readonly=True, store=True)

    tax_id = fields.Many2many('account.tax', string='Taxes',
                              domain=['|', ('active', '=', False), ('active', '=', True)])

    winner = fields.Selection([('Yes', 'Yes'), ('No', 'No')], default="No")

    @api.depends('product_id', 'product_qty', 'unit_price', 'tax_id')
    def _compute_total(self):
        for record in self:
            record.total_price = record.unit_price * record.product_qty

            price = record.unit_price
            taxes = record.tax_id.compute_all(
                price, record.rfq_id.currency_id, record.product_qty)

            record.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'total_price': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.model
    def create(self, vals):

        return super(Rfq_Detail_local, self).create(vals)

    @api.depends('product_qty', 'unit_price')
    def _compute_total_price(self):
        for record in self:
            record.total_price = record.product_qty * record.unit_price

    @api.onchange('product_id')
    def onchange_product_id(self):
        x = self.purchase_request_lines.product_id.ids
        # set quantity
        products = self.purchase_request_lines

        for product in products:
            if product.product_id.id == self.product_id.id:
                self.product_qty = product.product_qty

        return {'domain': {'product_id': [('id', 'in', (x))]}}

    def check_double_product_supplier_entry(self, vals):
        if self:
            return self.env['droga.purchase.request.rfq.line.local'].search_count(
                [('rfq_id', '=', self.rfq_id.id), ('supplier_id', '=', self.supplier_id.id),
                 ('product_id', '=', self.product_id.id)])
        else:
            return self.env['droga.purchase.request.rfq.line.local'].search_count(
                [('rfq_id', '=', vals['rfq_id']), ('supplier_id', '=', vals['supplier_id']),
                 ('product_id', '=', vals['product_id'])])

    @api.onchange('product_id')
    def set_unit(self):
        for record in self:
            record.product_uom = record.product_id.uom_id

    def offer_detail(self):
        view = self.env.ref('droga_procurement.droga_purchase_request_rfq_line_local_view_tree')

        return {
            'name': 'Offer',
            'view_mode': 'tree',
            'res_model': 'droga.purchase.request.rfq.line.local',
            'view_id': view.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,

            'domain':
                ([('supplier_id', '=', self.supplier_id.id), ('rfq_id', '=', self.rfq_id.id)]),

            'context': {
                'default_supplier_id': self.supplier_id.id
            }

        }
