from datetime import datetime
from datetime import timedelta

from stdnum import cr
from stdnum.ch import uid

from odoo import models, fields, api
from odoo.addons.base.models.ir_model import IrModelData
from odoo.exceptions import ValidationError, UserError


class cust_credit_limit(models.Model):
    _inherit = 'res.partner'
    cust_credit_limit = fields.Float(string='Credit limit', tracking=True)
    unsettled_amount = fields.Monetary(compute='_compute_balance', string='Unsettled amount')
    available_amount = fields.Float(string='Credit balance', compute='_compute_balance')
    vat = fields.Char(string='Tin No', index=True,default='0000000000',
                      help="The Tax Identification Number. Complete it if the contact is subjected to government taxes. Used in some legal statements.")

    @api.depends('debit', 'credit')
    def _compute_balance(self):
        for record in self:
            if record.id in [15390, 15488]:
                matured_invoices = []
            elif record.vat != '0000000000':
                matured_invoices = self.env['account.move'].search(
                    [('state', '=', 'posted'), ('journal_id.type', '=', 'sale'),('cost_center','not like','Pharmacy%'),
                     ('payment_state', 'in', ['not_paid', 'partial']), ('partner_id.vat', '=', record.vat), '|',
                     ('partner_id.active', '=', True), ('partner_id.active', '=', False)])
            else:
                matured_invoices = self.env['account.move'].search(
                    [('state', '=', 'posted'), ('journal_id.type', '=', 'sale'),('cost_center','not like','Pharmacy%'),
                     ('payment_state', 'in', ['not_paid', 'partial']), ('partner_id', '=', record.id), '|',
                     ('partner_id.active', '=', True), ('partner_id.active', '=', False)])
            tot_amount = 0
            for mi in matured_invoices:
                tot_amount = tot_amount + (
                    mi['amount_total_signed'] if mi['amount_residual'] == 0 else mi['amount_residual'])
            record.unsettled_amount = tot_amount
            # record.unsettled_amount = record.credit - record.debit

            record.available_amount = record.cust_credit_limit - record.unsettled_amount


class cust_sales_credit_limit(models.Model):
    _inherit = 'sale.order'

    available_amount = fields.Float(string='Credit balance', related='partner_id.available_amount')
    tender_origin_form = fields.Many2one('droga.tender.master', readonly=True)
    cash_upfront = fields.Float(string='Down payment')
    pay_type = fields.Boolean(related='payment_term_id.apply_credit_limit')
    mature_amount = fields.Monetary('Matured amount', compute='_get_mature_amount')
    show_invoice_button = fields.Boolean(compute='_get_mature_amount')
    manual_price = fields.Boolean('Manual price', default=False, required=True, tracking=True)
    Vat_no = fields.Char(related='partner_id.vat', readonly='True')
    cust_type_ext = fields.Many2one('droga.cust.type', related='partner_id.cust_type_ext', inverse='_cust_type_inv',
                                    string='Customer type')
    cust_id = fields.Integer(related='partner_id.id', readonly='True')
    sales_type = fields.Char('Sales order type', compute='_get_so_type', store=True)
    supporters = fields.Many2many('droga.pro.sales.master', string='Supporters')
    cust_name = fields.Char('Customer Name')
    cust_id = fields.Char('Customer ID')
    sales_order_type = fields.Selection([
        ('Local', 'Local'),
        ('Foreign', 'Foreign')], string='Order type',default='Local')
    contract_num = fields.Char('Contract number')
    invoice_printed = fields.Char(default="No", string="Invoice printed", store=True)

    INVOICE_STATUS = [
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice')
    ]
    
    invoice_status = fields.Selection(
        selection=INVOICE_STATUS,tracking=True,
        string="Invoice Status",
        compute='_compute_invoice_status',
        store=True)

    def _cust_type_inv(self):
        pass

    order_type = fields.Selection([
        ('IM', 'Import'),('EX','Export'),
        ('WS', 'Wholesale')], string='Order from')
    order_from = fields.Char('Order from')

    @api.depends('payment_term_id')
    def _get_so_type(self):
        for rec in self:
            if rec.payment_term_id.apply_credit_limit:
                rec.sales_type = 'Credit sales'
            elif rec.payment_term_id.name == 'Sales return':
                rec.sales_type = 'Sales return'
            else:
                rec.sales_type = 'Cash sales'

    @api.depends('partner_id')
    def _get_mature_amount(self):
        for rec in self:
            if rec.partner_id.id in [15390, 15488] or rec.partner_id.x_exclude_maturity_for_reconciliation:
                matured_invoices = []
            elif rec.partner_id.vat != '0000000000' and not rec.partner_id.mature_individually:
                matured_invoices = self.env['account.move'].search(
                    [('state', '=', 'posted'), ('journal_id.type', '=', 'sale'),
                     ('company_id', '=', self.env.company.id),
                     ('invoice_date_due', '<', datetime.now().date()),
                     ('payment_state', 'in', ['not_paid', 'partial']), ('partner_id.vat', '=', rec.partner_id.vat), '|',
                     ('partner_id.active', '=', True), ('partner_id.active', '=', False)])
            else:
                matured_invoices = self.env['account.move'].search(
                    [('state', '=', 'posted'), ('journal_id.type', '=', 'sale'),
                     ('company_id', '=', self.env.company.id),
                     ('invoice_date_due', '<', datetime.now().date()),
                     ('payment_state', 'in', ['not_paid', 'partial']), ('partner_id', '=', rec.partner_id.id), '|',
                     ('partner_id.active', '=', True), ('partner_id.active', '=', False)])
            tot_amount = 0
            for mi in matured_invoices:
                tot_amount = tot_amount + (
                    mi['amount_total_signed'] if mi['amount_residual'] == 0 else mi['amount_residual'])
            rec.mature_amount = tot_amount
            rec.show_invoice_button = False if rec.mature_amount == 0 else True

    def action_cancel(self):
        for rec in self:
            if rec.invoice_status not in ('no', 'to invoice'):
                raise ValidationError("The sales order is already invoiced, hence can not be cancelled.")

            if len(rec.order_line.filtered(lambda x: x.qty_delivered > 0)) > 0:
                raise ValidationError("There are dispatched items under the sales order, hence can not be cancelled.")
            pass
        return super(cust_sales_credit_limit, self).action_cancel()

    def write(self,vals):
        if self.order_from and self.state not in ('sale', 'cancel', 'done', 'fia'):
            if self.order_from=='PH' and 'state' in vals:
                for l in self.order_line:
                       l._compute_price_unit()
        return super(cust_sales_credit_limit, self).write(vals)

    @api.model
    def create(self, vals):
        message = ''
        result = super(cust_sales_credit_limit, self).create(vals)

        if result.order_from:
            if result.order_from=='PH':
                for l in result.order_line:
                       l._compute_price_unit()

        for so in result:

            if not so.partner_id.vat and so.company_id.id==1:
                message = message + "Tin No must be registered for customer!"
                # raise ValidationError("Tin No must be registered for customer!")
            if not so.pr_sales and (self.env.user.name.startswith('CRM') or self.env.user.name.startswith('Tender')):
                message = message + ('\n' if message else '') + "Please login before registering a sales order!"
                # raise ValidationError("Please login before registering a sales order!")
            if so.order_from:
                if so.order_from.startswith('PH'):
                    if so.partner_id.available_amount_pharma < so.amount_total and so.payment_term_id.apply_credit_limit and so.company_id.id in (1,2):
                        message = message + ('\n' if message else '') + "You cannot exceed credit limit!"
                        # raise ValidationError("You cannot exceed credit limit!")
                    if so.customer_emp:
                        if so.customer_emp.employee_credit_limit!=0 and so.customer_emp.employee_credit_limit <so.amount_total and so.payment_term_id.apply_credit_limit:
                            message = message + ('\n' if message else '') + "Maximum credit limit for employee is "+str(so.customer_emp.employee_credit_limit)
                    if so.mature_amount_pharma > 0:
                        message = message + (
                            '\n' if message else '') + "Please settle matured amounts before initiating another sales!"
            else:
                if so.payment_term_id.apply_credit_limit and so.payment_term_id.id not in so.partner_id.property_supplier_payment_term_id.allowed_terms.ids and so.company_id.id in (1,2):
                    message = message + (
                        '\n' if message else '') + "Payment term is not allowed for customer"
                #if so.partner_id.available_amount < so.amount_total and so.payment_term_id.apply_credit_limit and not so.partner_id.id in [
                #    15390] and so.company_id.id in (1,2):
                #    message = message + ('\n' if message else '') + "You cannot exceed credit limit!"
                    # raise ValidationError("You cannot exceed credit limit!")
                if so.mature_amount > 0:
                    message = message + (
                        '\n' if message else '') + "Please settle matured amounts before initiating another sales!"

            if so.amount_total < so.payment_term_id.min_amount and not so.tender_origin_form_tender and (not so.order_from.startswith('PT') if type(so.order_from) is str else True) and so.company_id.id in (1,2):
                message = message + (
                    '\n' if message else '') + "Minimum order amount for " + so.payment_term_id.name + " is " + str(
                    so.payment_term_id.min_amount)
                # raise ValidationError("Minimum order amount for "+so.payment_term_id.name+" is "+str(so.payment_term_id.min_amount))
            if message:
                raise ValidationError(message)

            if 'cust_type_ext' in vals:
                if result.partner_id.cust_type_ext.id != vals['cust_type_ext']:
                    result.partner_id.cust_type_ext = vals['cust_type_ext']

            if len(so.order_line) == 0:
                raise ValidationError('Please register at least one product to initiate sales order.')

            # if so.order_type:
            #    if so.order_type=='WS' and self.env.company.id == 1:
            #        raise ValidationError("WHOLESALE IS NOT ACTIVE CURRENTLY AS INVENTORY IS UNDER STOCK TAKE.")

            # Pharmacy and physiotheraphy sales (so.order_type is false for pharmacy and physio as this field is used for import and wholesale)
            if not so.order_type and self.env.company.id == 1:
                # Pharmacy
                if so.order_from.startswith('PH'):
                    if not so.wareh:
                        raise ValidationError("Employee is not linked to a pharmacy chain branch.")
                    for res in so.order_line:
                        res.wareh = so.wareh
                        res.product_id.product_tmpl_id.invoice_policy = 'order'
                # Physiotheray
                else:
                    for res in so.order_line:
                        res.wareh = 32 if so.order_from == 'PT-Bole' else 31
                        res.product_id.product_tmpl_id.invoice_policy = 'order'
            # This is for import or wholesale sales under Droga
            elif so.order_type and self.env.company.id == 1:
                so.order_from = 'IM-' + so.order_type
            elif self.env.company.id == 2:
                so.order_from = 'EM-EM'

            if result.user_id.name.startswith('CRM'):
                result.sales_initiator = 'SR-' + result.pr_sales.p_name if result.pr_sales else result.user_id.name
            elif result.user_id.name.startswith('Tender'):
                result.sales_initiator = 'TEN-' + result.pr_sales.p_name if result.pr_sales else result.user_id.name
            else:
                result.sales_initiator = result.user_id.name

            if self.env.company.id == 2:
                if so.sales_order_type == 'Local':
                    _name = self.env['ir.sequence'].next_by_code('sale.order.emma.local')
                else:
                    _name = self.env['ir.sequence'].next_by_code('sale.order.emma.foreign')

                if not _name:
                    raise UserError("Order sequence not found.")
                vals['name'] = _name
                so.name = _name
        return result

    def action_create(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError((
                "It is not allowed to confirm an order in the following states: %s",
                ", ".join(self._get_forbidden_state_confirm()),
            ))

        self.order_line._validate_analytic_distribution()

        for order in self:
            if order.partner_id in order.message_partner_ids:
                continue
            order.message_subscribe([order.partner_id.id])

        self.write(self._prepare_confirmation_values())

        # Context key 'default_name' is sometimes propagated up to here.
        # We don't need it and it creates issues in the creation of linked records.
        context = self._context.copy()
        context.pop('default_name', None)

        self.with_context(context)._action_confirm()
        if self.env.user.has_group('sale.group_auto_done_setting'):
            self.action_done()

        return True

    def _get_invoice_print_status(self):
        for record in self:
            invoice = self.env["account.move"].search([('invoice_origin', '=', record.name)])
            for rec in invoice:
                if rec.is_invoice_printed_pos:
                    rec.invoice_printed = "Yes"
                else:
                    rec.invoice_printed = "No"


class cust_sales_no_create_after_invoice(models.Model):
    _inherit = 'sale.order.line'
    manual_price = fields.Boolean(related='order_id.manual_price')
    expiry_date_html = fields.Html('Expiration date', compute='_get_expiry', default='')
    batch_html = fields.Html('Batch No', compute='_get_expiry', default='')

    order_type = fields.Selection([
        ('IM', 'Import'),('EX','Export'),
        ('WS', 'Wholesale')], string='Order type', related='order_id.order_type')
    import_quant_invoiced=fields.Float('Invoiced quantity', compute='_get_on_hand', store=True)

    @api.depends('qty_invoiced')
    def _get_on_hand(self):
        for rec in self:
            if rec.company_id.id == 1 and rec.product_id.import_uom_new.factor != 0:
                rec.import_quant_invoiced = rec.qty_invoiced / (
                            rec.product_id.uom_id.factor / rec.product_id.import_uom_new.factor)
            else:
                rec.import_quant_invoiced = rec.qty_invoiced


    def _get_expiry(self):
        for rec in self:
            rec.expiry_date_html = ''
            rec.batch_html
            try:
                for move in rec.move_ids:
                    count = len(move.move_line_ids) - 1
                    for id, move_line in enumerate(move.move_line_ids):
                        rec.expiry_date_html = (
                                                   rec.expiry_date_html if rec.expiry_date_html else '') + move_line.lot_id.expiration_date.strftime(
                            "%B %d,%Y") + ('\n' if id < count else '')
                        rec.batch_html = (
                                             rec.batch_html if rec.batch_html else '') + move_line.lot_id.name + ' (' + str(
                            move_line.qty_done) + ')' + ('\n' if id < count else '')
            except:
                rec.expiry_date_html = ''
                rec.batch_html = ''

    def _prepare_procurement_values(self, group_id=False):

        values = super(cust_sales_no_create_after_invoice, self)._prepare_procurement_values(group_id)
        self.ensure_one()
        # Use the delivery date if there is else use date_order and lead time
        date_deadline = self.order_id.commitment_date or (
                self.order_id.date_order + timedelta(days=self.customer_lead or 0.0))
        date_planned = date_deadline - timedelta(days=self.order_id.company_id.security_lead)
        values.update({
            'group_id': group_id,
            'sale_line_id': self.id,
            'date_planned': date_planned,
            'date_deadline': date_deadline,
            'route_ids': self.route_id,
            'warehouse_id': self.wareh or False,
            'partner_id': self.order_id.partner_shipping_id.id,
            'product_description_variants': self.with_context(
                lang=self.order_id.partner_id.lang)._get_sale_order_line_multiline_description_variants(),
            'company_id': self.order_id.company_id,
            'product_packaging_id': self.product_packaging_id,
            'sequence': self.sequence,
        })
        return values

    # Restrict multiple sales order invoicing
    @api.model
    def create(self, vals):
        res = super(cust_sales_no_create_after_invoice, self).create(vals)
        if self.order_id.state != 'draft' and self.order_id.state:
            raise ValidationError("Sales order is already invoiced!")
        else:
            return res


class payment_term_no_credit(models.Model):
    _inherit = 'account.payment.term'
    apply_credit_limit = fields.Boolean(string='Apply credit limit', default=True, tracking=True)
    deliv_after_payment = fields.Boolean(string='Delivery after payment', default=False, tracking=True)
    min_amount = fields.Float(string='Minimum order amount', default=0, tracking=True)
    used_under = fields.Selection([
        ('BT', 'Both'),
        ('DR', 'Droga'), ('PC', 'Pharmacy chain')], string='Term used under')
    allowed_terms=fields.Many2many('account.payment.term',
        relation='account_payment_term_rel',
        column1='payment_term_id',
        column2='related_payment_term_id',
        string='Related Payment Terms')

    def write(self, vals_list):
        if not self.env.user.has_group('droga_sales.payment_term_update'):
            raise UserError("You can not update payment term.")
        return super(payment_term_no_credit, self).write(vals_list)

    @api.model
    def create(self, vals):
        if not self.env.user.has_group('droga_sales.payment_term_update'):
            raise UserError("You can not create payment term.")
        return super(payment_term_no_credit, self).create(vals)


class payment_term_no_credit_line(models.Model):
    _inherit = "account.payment.term.line"

    def write(self, vals_list):
        if not self.env.user.has_group('droga_sales.payment_term_update'):
            raise UserError("You can not update payment term.")
        return super(payment_term_no_credit_line, self).write(vals_list)


class payment_term_no_credit_messages(models.Model):
    _name = 'account.payment.term'
    _inherit = ['account.payment.term', 'mail.thread', 'mail.activity.mixin', 'image.mixin']
