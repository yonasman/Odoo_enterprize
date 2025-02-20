from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from datetime import datetime


class AccountMove(models.Model):
    _inherit = "account.move"

    purpose = fields.Char("Purpose")
    vendor_customer_name = fields.Char("Customer/Vendor Name")
    withholding_no = fields.Char("Withholding Ref", help="Withholding invoice number", store=True)
    withholding_invoice = fields.Boolean("Has Withholding",
                                         help="The transaction has withholding invoice",
                                         compute="is_withholding_transaction", store=True, default=False)
    withholding_invoice_provided = fields.Boolean("Withholding Invoice",
                                                  help="If the transaction has been withheld, the customer needs to provide a withholding invoice",
                                                  default=False)
    withholding_internal_ref = fields.Char("Withholding Internal Ref", help="Withholding Internal Reference")
    sales_initiator = fields.Char("Sales Person", store=True)

    transaction_type = fields.Many2one("account.transaction.type")
    transaction_no = fields.Char("Transaction Number", default='New')
    untaxed_amount_word = fields.Char(
        compute='_compute_amount_word')
    amount_total_word = fields.Char(
        compute='_compute_amount_word')
    tax_amount_word = fields.Char(
        compute='_compute_amount_word')

    withholding_two_percent = fields.Float(
        compute='_compute_withholding_amount')
    withholding_thirty_percent = fields.Float(
        compute='_compute_withholding_amount')
    vat_percent = fields.Float(
        compute='_compute_withholding_amount')

    cost_center = fields.Char(string="Division", store=True, compute='_get_sales_info')
    sales_channel = fields.Char("Sales Channel", store=True, compute='_get_sales_info')
    customer_category = fields.Char("Customer Category", store=True, compute='_get_sales_info')
    due_date_in_days = fields.Integer("Due Days", store=True, compute='update_due_days')

    sales_type = fields.Char("Sales Type", readonly=True)

    # picking list for vendor invoice
    picking_list = fields.One2many('stock.picking', compute='get_picking_list')

    # crv
    crvs = fields.One2many('account.move.crv', 'move_id_crv')
    withholdings = fields.One2many('account.move.withholding', 'move_id_wh')

    branch_address = fields.Many2one('droga.sales.branch.address', compute='get_branch_address')

    payment_request_id = fields.Integer(related='payment_id.payment_request_id.id')

    bank_payment_ref = fields.Char("Payment Ref", store=True)

    @api.model
    def create(self, vals):
        # Check withholding
        # vals.update({'withholding_invoice': self.is_withholding_transaction()})
        # generate transaction number
        res = super(AccountMove, self).create(vals)
        return res

    def write(self, vals):
        # Check withholding
        # vals.update({'withholding_invoice': self.is_withholding_transaction()})
        return super(AccountMove, self).write(vals)

    def _compute_amount_word(self):

        self.untaxed_amount_word = ''
        self.amount_total_word = ''
        self.tax_amount_word = ''
        self.tax_amount_word = ''

        for record in self:
            record.untaxed_amount_word = str(
                self.convert_to_word(record.amount_untaxed))
            record.amount_total_word = str(
                self.convert_to_word(record.amount_total))
            if record.withholding_two_percent != 0:
                record.tax_amount_word = str(
                    self.convert_to_word(record.withholding_two_percent))
            elif record.withholding_thirty_percent != 0:
                record.tax_amount_word = str(
                    self.convert_to_word(record.withholding_thirty_percent))

    def _compute_withholding_amount(self):
        tax_amount1 = 0
        tax_amount2 = 0
        vat_amount = 0

        self.withholding_two_percent = 0
        self.withholding_thirty_percent = 0
        self.vat_percent = 0

        for record in self.invoice_line_ids:
            for tax_id in record.tax_ids:
                if tax_id.amount == -2:
                    tax_amount1 += abs(record.balance * tax_id.amount / 100)
                elif tax_id.amount == -30:
                    tax_amount2 += abs(record.balance * tax_id.amount / 100)
                elif tax_id.amount == 15:
                    vat_amount += abs(record.balance * tax_id.amount / 100)

        self.withholding_two_percent = round(tax_amount1, 2)
        self.withholding_thirty_percent = round(tax_amount2, 2)
        self.vat_percent = round(vat_amount, 2)

    # get sales person
    @api.depends('invoice_line_ids.analytic_distribution')
    def _get_sales_info(self):
        self.sales_initiator = ''
        for record in self:
            if record.move_type == 'out_invoice':
                # get customer category
                record.customer_category = 'Others'
                record.cost_center = "Others"
                record.sales_channel = "Marketing"
                record.customer_category = record.partner_id.cust_type_ext.cust_org_type

                # calculate due days
                delta = datetime.now().date() - record.invoice_date_due
                record.due_date_in_days = delta.days

                # search sales order
                sale_order = self.env["sale.order"].sudo().search([('name', '=', record.invoice_origin)])
                for order in sale_order:
                    record.sales_initiator = order.sales_initiator

                for o in record.invoice_line_ids:
                    if o.analytic_distribution:
                        analytic_distributions = o.analytic_distribution
                        for analytic_distribution_id in analytic_distributions:
                            # search analytic definition table
                            analytic_plans = self.env['account.analytic.account'].search(
                                [('id', '=', analytic_distribution_id)])
                            for analytic_plan in analytic_plans:
                                if analytic_plan.plan_id.complete_name == 'Profit / Cost Center':
                                    record.cost_center = analytic_plan.display_name
                                elif analytic_plan.plan_id.complete_name == 'Sales Channel':
                                    record.sales_channel = analytic_plan.display_name
                        break

                if record.cost_center == "Others" and record.stock_move_id:
                    record.cost_center = record.stock_move_id.trans_warehouse.linked_analytic.display_name

    @api.depends('invoice_date', 'invoice_payment_term_id')
    def update_due_days(self):
        for record in self:
            # calculate due days
            delta = datetime.now().date() - record.invoice_date_due
            record.due_date_in_days = delta.days

    def update_due_days_all(self):
        records = self.env['account.move'].search(
            [('move_type', '=', 'out_invoice'), ('payment_state', 'in', ('not_paid', 'partial'))])
        for record in records:
            # calculate due days
            delta = datetime.now().date() - record.invoice_date_due
            due_date_in_days = delta.days

            self.env.cr.execute(
                """ update account_move set due_date_in_days=%s where id=%s""",
                (due_date_in_days, record.id))

    def _get_sales_info_obsolete(self):
        self.sales_initiator = ''
        recs = self.env['account.move'].search([('move_type', '=', 'out_invoice')])

        for record in recs:
            if record.move_type == 'out_invoice':

                customer_category = 'Others'
                cost_center = "Others"
                sales_channel = "Marketing"
                sales_initiator = ""

                if record.partner_id.cust_type_ext:
                    customer_category = record.partner_id.cust_type_ext.cust_org_type

                # calculate due days
                delta = datetime.now().date() - record.invoice_date_due
                due_date_in_days = delta.days

                # search sales order
                sale_order = self.env["sale.order"].sudo().search([('name', '=', record.invoice_origin)])
                for order in sale_order:
                    sales_initiator = order.sales_initiator

                    """# get cost center
                    if order.tender_origin_form_tender:
                        sales_channel = "Tender"
                    else:
                        sales_channel = "Marketing"

                    if order.order_type:
                        cost_center = order.order_type"""

                for o in record.invoice_line_ids:

                    if o.analytic_distribution:
                        analytic_distributions = o.analytic_distribution
                        for analytic_distribution_id in analytic_distributions:
                            # search analytic definition table
                            analytic_plans = self.env['account.analytic.account'].search(
                                [('id', '=', analytic_distribution_id)])
                            for analytic_plan in analytic_plans:
                                if analytic_plan.plan_id.complete_name == 'Profit / Cost Center':
                                    cost_center = analytic_plan.display_name
                                elif analytic_plan.plan_id.complete_name == 'Sales Channel':
                                    sales_channel = analytic_plan.display_name
                        break

                self.env.cr.execute(
                    """ update account_move set customer_category=%s,cost_center=%s,sales_channel=%s,due_date_in_days=%s,sales_initiator=%s where id=%s""",
                    (
                        customer_category, cost_center, sales_channel, due_date_in_days, sales_initiator, record.id))

    # check if the transaction has withholding transaction
    @api.depends("invoice_line_ids.tax_ids")
    def is_withholding_transaction(self):
        has_withholding_line = False
        for record in self.invoice_line_ids:
            for tax in record.tax_ids:
                if tax.tax_group_id.name == 'Withholding':
                    has_withholding_line = True
                    break
        self.withholding_invoice = has_withholding_line

    # get picking list from purchase order
    def get_picking_list(self):

        for record in self:
            record.picking_list = None
            if record.move_type in ('out_invoice', 'in_invoice'):
                # search picking list using purchase order name
                picking_lists = self.env['stock.picking'].search([('origin', '=', record.invoice_origin)])
                if picking_lists:
                    record.picking_list = picking_lists

    def get_branch_address(self):
        for record in self:
            record.branch_address = None
            branch_address = self.env['droga.sales.branch.address'].search(
                [('profit_center', '=', record.account_move_linked_analytic.id)])
            record.branch_address = branch_address

    # Generate withholding reference
    def generate_withholding_ref(self):
        # get sequence number for each company
        for record in self:
            if record.withholding_internal_ref:
                raise ValidationError("Internal withholding reference already generated")
            self_comp = self.with_company(record.company_id)

            sequence_no = self.env['droga.finance.utility'].get_transaction_no('WH', record.invoice_date,
                                                                               record.company_id.id)
            record.withholding_internal_ref = sequence_no or '/'

    @api.constrains('crvs')
    def validate_crv(self):
        # get total amount
        total_amount = abs(self.amount_untaxed_signed)
        total_amount_crv = 0
        for record in self.crvs:
            # sum crv amount
            total_amount_crv += record.amount

        if total_amount_crv > total_amount:
            raise ValidationError("You can't print CRV amount greater than the invoice amount")

    def convert_to_word(self, num):
        num_strings = str(abs(num))
        numbers = num_strings.split('.')

        word = self.int_to_word(int(numbers[0])) + ' birr'

        if len(numbers) == 2:
            if int(numbers[1]) != 0:
                if len(numbers[1]) == 1:
                    numbers[1] = int(numbers[1]) * 10.0

                word = self.int_to_word(int(numbers[0])) + ' birr and ' + self.int_to_word(int(numbers[1])) + ' cents'

        return word.capitalize()

    def int_to_word(self, num):
        d = {0: 'zero', 1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five',
             6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten',
             11: 'eleven', 12: 'twelve', 13: 'thirteen', 14: 'fourteen',
             15: 'fifteen', 16: 'sixteen', 17: 'seventeen', 18: 'eighteen',
             19: 'nineteen', 20: 'twenty',
             30: 'thirty', 40: 'forty', 50: 'fifty', 60: 'sixty',
             70: 'seventy', 80: 'eighty', 90: 'ninety'}
        k = 1000
        m = k * 1000
        b = m * 1000
        t = b * 1000

        assert (0 <= num)

        if (num < 20):
            return d[num]

        if (num < 100):
            if num % 10 == 0:
                return d[num]
            else:
                return d[num // 10 * 10] + '-' + d[num % 10]

        if (num < k):
            if num % 100 == 0:
                return d[num // 100] + ' hundred'
            else:
                return d[num // 100] + ' hundred ' + self.int_to_word(num % 100)

        if (num < m):
            if num % k == 0:
                return self.int_to_word(num // k) + ' thousand'
            else:
                return self.int_to_word(num // k) + ' thousand ' + self.int_to_word(num % k)

        if (num < b):
            if (num % m) == 0:
                return self.int_to_word(num // m) + ' million'
            else:
                return self.int_to_word(num // m) + ' million ' + self.int_to_word(num % m)

        if (num < t):
            if (num % b) == 0:
                return self.int_to_word(num // b) + ' billion'
            else:
                return self.int_to_word(num // b) + ' billion ' + self.int_to_word(num % b)

        if (num % t == 0):
            return self.int_to_word(num // t) + ' trillion'
        else:
            return self.int_to_word(num // t) + ' trillion ' + self.int_to_word(num % t)

        raise AssertionError('num is too large: %s' % str(num))

    def update_payment_ref_to_move_line(self):
        self.env.cr.execute("""
                        WITH limited_updates AS (
    SELECT am.id AS am_id, dap.bank_payment_ref
    FROM account_move am
    JOIN (
        SELECT move_id, string_agg(name, '-') AS bank_payment_ref
        FROM droga_account_payment_link_data
        GROUP BY move_id
    ) AS dap ON am.id = dap.move_id
    WHERE am.move_type IN ('out_invoice', 'in_invoice')
    LIMIT 300000
)
UPDATE account_move
SET bank_payment_ref = COALESCE(limited_updates.bank_payment_ref, '')
FROM limited_updates
WHERE account_move.id = limited_updates.am_id;
                    """)

        # Commit the transaction to ensure the data is saved
        self.env.cr.commit()

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    bank_payment_ref = fields.Char("Payment Ref", store=True)

    @api.depends("move_id", "payment_ids")
    def get_bank_payment_ref(self):
        lines = self.env["account.move.line"].search([])
        for record in lines:
            record.bank_payment_ref = ""

            # Assuming invoice_id is the ID of the invoice you want to check
            invoice = record.move_id

            # Initialize an empty recordset to store the linked payments
            linked_payments = self.env['account.payment']

            # Loop through each account.move.line in the invoice to find linked payments
            for line in invoice.line_ids:
                # Check for reconciled debit and credit move lines that match this invoice line
                partials = line.matched_debit_ids + line.matched_credit_ids

                # Extract the payments linked through reconciliation
                for partial in partials:
                    if partial.debit_move_id.move_id.payment_id:
                        linked_payments |= partial.debit_move_id.move_id.payment_id
                    if partial.credit_move_id.move_id.payment_id:
                        linked_payments |= partial.credit_move_id.move_id.payment_id

            # Display or process the linked payment information
            ref = "; ".join(payment.name for payment in linked_payments)

            record.write({'bank_payment_ref': ref})

    def update_payment_ref(self):
        # Execute the SQL insert statement
        self.env.cr.execute(""" delete from  droga_account_payment_link_data""")
        self.env.cr.commit()

        self.env.cr.execute("""
                INSERT INTO droga_account_payment_link_data (id, payment_id, move_id,payment_move_id,name)
                SELECT id, payment_id, move_id,payment_move_id,name FROM droga_account_payment_link
            """)

        # Commit the transaction to ensure the data is saved
        self.env.cr.commit()

# CRV document tracking
class AccountCrv(models.Model):
    _name = 'account.move.crv'

    _order = "move_id_crv asc"

    move_id_crv = fields.Many2one('account.move')
    name = fields.Char(related='move_id_crv.name')
    customer_name = fields.Char(related='move_id_crv.invoice_partner_display_name')
    crv_ref = fields.Char("CRV Reference", required=True)
    amount = fields.Float("Amount", required=True)
    is_crv_document_printed = fields.Boolean("Document Printed")
    payment_description = fields.Char("Payment Description")
    amount_word = fields.Char("Amount Word", compute='_compute_amount_word')

    def _compute_amount_word(self):
        for record in self:
            record.amount_word = self.env['account.move'].convert_to_word(record.amount)

    @api.constrains('crv_ref')
    def check_crv_ref(self):
        for record in self:
            # search crv ref in the database
            crv_count = self.env['account.move.crv'].search_count([('crv_ref', '=', record.crv_ref)])
            if crv_count > 1:
                raise ValidationError(
                    'CRV Reference already registered in the system, you can''t use one reference multiple times')

    def unlink(self):
        raise ValidationError(
            "You can't delete CRV Record")

class AccountWithholding(models.Model):
    _name = 'account.move.withholding'

    move_id_wh = fields.Many2one('account.move')
    withholding_tax_types = fields.Many2one("account.tax", required=True,
                                            domain="[('tax_group_id', '=', 'Withholding')]")
    ref = fields.Char("Reference", required=True)
    amount_before_vat = fields.Float("Before Vat", store=True)
    withholding_amount = fields.Float("Withholding", store=True, compute="compute_with_holding")
    withholding_date = fields.Date("Date", required=True)
    entry_id = fields.Many2one('account.move')
    withholding_amount_word = fields.Char("Amount Word", compute="_compute_amount_word")
    withholding_percent = fields.Float("Withholding Percent", store=True)

    def _compute_amount_word(self):
        for record in self:
            record.withholding_amount_word = self.env['account.move'].convert_to_word(record.withholding_amount)

    def create_with_holding_entry(self):
        pass

    @api.depends("withholding_tax_types", "amount_before_vat")
    def compute_with_holding(self):
        for record in self:
            # get untaxed amount
            record.withholding_percent = abs(record.withholding_tax_types.amount)

            if record.amount_before_vat == 0:
                record.amount_before_vat = record.move_id_wh.amount_untaxed
                record.withholding_amount = (
                        record.move_id_wh.amount_untaxed * (abs(record.withholding_tax_types.amount) / 100))
            else:
                record.withholding_amount = (
                        record.amount_before_vat * (abs(record.withholding_tax_types.amount) / 100))

    def create_with_holding_entry(self):

        if self.entry_id:
            raise ValidationError("You can't create multiple entries")

        for record in self:
            # get vendor id
            vendor_id = record.move_id_wh.partner_id.id
            invoice_date = datetime.now()
            invoice_lines = []

            if record.move_id_wh.move_type == 'in_invoice':
                invoice_lines.append({'debit': record.withholding_amount,
                                      'credit': 0,
                                      'partner_id': vendor_id,
                                      'account_id': self.get_account_id('211001')})
                invoice_lines.append({'debit': 0,
                                      'credit': record.withholding_amount,
                                      'partner_id': 0,
                                      'account_id': self.get_account_id('214003')})
            elif record.move_id_wh.move_type == 'out_invoice':
                invoice_lines.append({'debit': record.withholding_amount,
                                      'credit': 0,
                                      'partner_id': 0,
                                      'account_id': self.get_account_id('116002')})
                invoice_lines.append({'debit': 0,
                                      'credit': record.withholding_amount,
                                      'partner_id': vendor_id,
                                      'account_id': self.get_account_id('114001')})

            entry = {
                'move_type': 'entry',
                'journal_id': self.get_journal_id('JV'),
                'partner_id': vendor_id,
                'invoice_date': invoice_date,
                'line_ids': [(0, 0, {
                    'partner_id': line['partner_id'],
                    'debit': line['debit'],
                    'credit': line['credit'],
                    'account_id': line['account_id'],
                }) for line in invoice_lines],
            }

            vendor_invoice = self.env['account.move'].create(entry)

            record.entry_id = vendor_invoice

    def get_account_id(self, account):
        accounts = self.env["account.account"].search([('code', '=', account)])

        account_id = 0
        for account in accounts:
            account_id = account.id

        return account_id

    def get_journal_id(self, journal):
        journals = self.env["account.journal"].search([('code', '=', journal)])

        journal_id = 0
        for journal in journals:
            journal_id = journal.id

        return journal_id
