from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime


class purchase_order(models.Model):
    _inherit = "purchase.order"

    @api.depends('order_line.unit_price_foregin', 'order_line.price_unit', 'order_line.product_qty')
    def compute_usd_total_amount(self):
        total = 0
        for record in self.order_line:
            total += record.total_price_foregin

        self.amount_total_usd = total

    def generate_release_permit(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Release Permits',
            'res_model': 'droga.reg.pre.import.permit.generated',
            'view_mode': 'form',
            'context': {
                'default_ra_status': 'procurement',
                'default_date_received': fields.Datetime.now(),

            },

        }

    def add_to_pre_import(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pre-Import Permits',
            'res_model': 'droga.reg.pre.import.permit.header',
            'view_mode': 'form',
            'context': {
                'default_date_received': fields.Datetime.now(),
                'default_ra_status': 'procurement',
            },
        }

    preimport_permit_no = fields.Char(string='Preimport permit No')
    rfq_id = fields.Many2one("droga.purhcase.request.rfq")
    rfq_local_id = fields.Many2one("droga.purchase.request.rfq.local")
    purchase_request_id = fields.Many2one("droga.purhcase.request")
    purchase_order_partial_shipments = fields.One2many("purchase.order.partial.shipment", "purchase_order_id")

    supplier_country = fields.Many2one(related='partner_id.country_id', store=True)

    from_rfq = fields.Boolean(default=False)

    shipping_reconcilations = fields.One2many(
        'droga.purchase.shipping.reconcilation', 'purchase_order_id')
    lcs = fields.One2many('droga.purchase.lc', 'purchase_order_id')

    exchange_rate = fields.Float("Exchange Rate", digits=(12, 4), default=1)

    amount_total_usd = fields.Float(
        "Total Amount USD", compute="compute_usd_total_amount", store=True)
    # copy foregin currency request

    # phases
    order_phase_status = fields.One2many(
        'droga.purchase.po.foregin.status', 'purchase_order_id')
    shipment_phase_status = fields.One2many(
        'droga.purchase.po.shipment.foregin.status', 'purchase_order_id')
    clearance_phase_status = fields.One2many(
        'droga.purchase.po.clearance.foregin.status', 'purchase_order_id')
    post_clearance_phase_status = fields.One2many(
        'droga.purchase.po.post.clerance.foregin.status', 'purchase_order_id')

    # docuemnts
    order_phase_documents = fields.One2many(
        'droga.purchase.po.docuemnts.foregin.status', 'purchase_order_id')
    shipment_phase_documents = fields.One2many(
        'droga.purchase.po.shipment.docuemnts.foregin.status', 'purchase_order_id')
    clearance_phase_documents = fields.One2many(
        'droga.purchase.po.clearance.docuemnts.foregin.status', 'purchase_order_id')
    post_clearance_phase_documents = fields.One2many(
        'droga.purchase.po.post.clerance.docuemnts.foregin.status', 'purchase_order_id')

    # ordering
    import_permit_no = fields.Char("Import Permit Number")
    import_permit_date = fields.Date("Import Permit Date")
    import_permit_approved = fields.Boolean("Import Permit Approved")
    lpco_number = fields.Char("LPCO number")
    margin = fields.Float("Margin")
    deposit_amount = fields.Float("Deposit Amount")
    deposit_date = fields.Date("Deposit Date")
    bank_service_charge = fields.Float("Bank Service Charge")

    # pre import
    pre_import_no = fields.Char("Pre Import No")
    pre_import_approved_date = fields.Date("Pre Import Approved Date")

    # import permit and insurance
    insurance_policy_no = fields.Char('Insurance Policy No')
    insurance_name = fields.Char("Insurance Name")
    insurance_date = fields.Date("Insurance Date")
    insurance_premium_cost = fields.Float("Insurance Premium Cost")

    # shipment
    shipment_percent = fields.Float("1st Shipment Amount", required=True, default=0)
    is_shipment_partial = fields.Boolean("Is Shipment Partial", default=False)
    shipment_date = fields.Date("Estimated Shipment Date")
    production_completion_date = fields.Date("Estimaed Production Completion Date")

    # shipment document
    shipment_scan_copy_doc_recived_date = fields.Date("Shipment Document Scan Copy Recived Date")
    shipment_original_copy_doc_recived_date = fields.Date(
        "Shipment Document Original Recived Date")

    shipment_doc_original_sent_from_supplier = fields.Date(
        "Date Original Document Sent from Supplier to Applicant Bank")
    shipment_doc_original_sent_from_supplier_courier = fields.Date(
        "Date Original Document Sent from Supplier to Applicant Bank By Courier")
    document_tracking_number = fields.Char("Courier Tracking No")
    shipment_doc_original_recived_by_applicant_bank = fields.Date(
        "Date Original Document Recived by Applicant Bank")

    # shipment lc amount
    exchange_rate_lc_settlement = fields.Float("Exchange Rate", digits=(12, 4))
    shipment_lc_amount = fields.Float("Deposit Amount for LC Settlement")

    lc_settlement_deposited = fields.Date("LC Settlement Deposited Date")
    shipment_doc_collected_from_applicant_bank = fields.Date(
        "Date Original Document Collected from Applicant Bank")
    shipment_doc_handed_to_finance = fields.Date(
        "Date Original Document Handed to Finance")
    supplier_payment_date = fields.Date("Supplier Payment Date")

    document_tracking_date = fields.Date("Document Tracking Date")

    discrepancy = fields.Selection(
        [('Yes', 'Yes'), ('No', 'No')], string="Discrepancy?")
    accept_discrepancy = fields.Boolean("Accept Discrepancy")
    discrepancy_comment = fields.Html("Discrepancy Comment")
    discrepancy_amount = fields.Float("Discrepancy Amount")

    is_it_do = fields.Boolean("IS it DO")
    do_amount = fields.Float("DO Amount", compute="calculate_do_amount", store=True)

    # good clearance
    goods_arrival_date = fields.Date(
        "Good Arrival Date", help="Good arrival to Port of discharge")
    goods_arrival_date_final_destination = fields.Date(
        "Good Arrival Date to Final Destination", help="Good Arrival Date to Final Destination")

    mode_of_transport = fields.Selection(related='rfq_id.mod_of_shipment')
    ports = fields.One2many(
        'droga.purchase.arrival.ports', 'purchase_order_id')

    freight_payment_by_air = fields.Float("Freight Amout ETB")
    freight_payment_by_sea = fields.Float("Freight Amount USD")
    freight_payment_by_sea_dg = fields.Float(
        "Freight Amount from Djibouti to Galafi USD", help="From Djibouti to Galafi")
    freight_payment_by_sea_gp = fields.Float(
        "Freight Amount from Galafi to Dry Port ETB", help="From Galafi to Dry Port")

    freight_paid_date = fields.Date("Freight Paid Date")
    container_deposit_amount = fields.Float("Container Deposit Amount")
    container_deposit_status = fields.Selection([('Returned', 'Returned'), ('Not Returned', 'Not Returned')],
                                                default='Not Returned')

    freight_settlement_advice_to_finance = fields.Date(
        "Freight Settlement Debit Advice Handed Over to Finance")
    shipping_doc_to_transitor = fields.Date(
        "Shipping Document & Settlement Advice is Handed Over to Transistor")

    declaration_number = fields.Char("Declaration Number")
    release_permit_applied_to_fda = fields.Date(
        "Release Permit Applied Date to FDA")
    custom_duty_tax_amount = fields.Float("Custom Duty Tax Amount")
    custom_duty_tax_paid_date = fields.Date("Custom Duty Tax Paid Date")
    custom_tax_acceptance = fields.Boolean(
        "Acceptance of the Duty Tax by Custom ")
    custom_duty_tax_additional_amount = fields.Float(
        "Additional Custom Duty Tax Amount")

    custom_duty_withholding_tax = fields.Float("Custom Withholding Tax")

    storage_cost = fields.Float("Storage Cost")
    demurrage_cost = fields.Float("Demurrage Cost")
    local_transport_cost = fields.Float("Local Transport Cost")
    loading_unloading_cost = fields.Float("Loading & Unloading Cost")

    release_permit_received_from_fda = fields.Date(
        "Release Permit Received from FDA")
    release_date_from_customs_delivery = fields.Date(
        "Release Date from Customs to Delivery Warehouse")

    goods_release_date = fields.Date("Release Date", help="Good Release Date")

    # post good clearance
    packing_list_shared_with_inventory = fields.Date(
        "Packing List Shared Date to Inventory")
    goods_arrival_date = fields.Date("Goods Arrival Date to Warehouse")
    grn_reconcilation_form_recived_date = fields.Date(
        "GRN and Reconciliation Form Received Date")
    reconcilation_discrepancy = fields.Boolean("Reconciliation Discrepancy")
    discrepancy_comment = fields.Html("Discrepancy Comment")
    discrepancy_action = fields.Html("Discrepancy Action")
    grn_submitted_to_finance = fields.Date("GRN Submission Date to Finance")
    stamped_declaration_recived_date = fields.Date(
        "Final Custom Stamped Invoice & Declaration Recived Date")
    delinquent_settlement_date = fields.Date("NBE Delinquent Settlement Date")
    transistor_service_payment_Amount = fields.Float(
        "Transitor Service Payment Amount")
    container_deposit_reimbursed_date = fields.Date(
        "Container Deposit Reimbursed Date")
    transistor_service_payment_done_date = fields.Date(
        "Transitor Service Payment Done Date")

    # bank
    bank = fields.Many2one("res.bank")
    branch = fields.Char("Branch")
    currency_approved_date = fields.Date("Currency Approved DateF")

    request_type = fields.Selection(
        [("Local", "Local"), ("Foregin", "Foregin"), ("Pharmacy", "Pharmacy")], readonly=True)
    is_delivery_partial = fields.Boolean("Partial Delivery")
    lc_margins = fields.One2many("droga.purchase.lc.margin", "purchase_order_id")

    payment_status = fields.Selection([('Paid', 'Paid'), ('Not Paid', 'Not Paid')], default='Not Paid',
                                      compute="compute_payment_status")

    payment_lead_time = fields.Float("Payment Lead Time", compute="compute_payment_status")
    delinquent_status = fields.Selection([('Delinquent', 'Delinquent'), ('Non Delinquent', 'Non Delinquent')],
                                         compute="compute_payment_status")

    @api.depends("supplier_payment_date")
    def compute_payment_status(self):
        for record in self:
            record.payment_status = 'Not Paid'
            record.payment_lead_time = 0
            record.delinquent_status = 'Non Delinquent'

            if record.supplier_payment_date and record.request_type == 'Foregin':
                record.payment_status = 'Paid'

                # calclualte payment lead time
                if record.shipment_doc_collected_from_applicant_bank and record.supplier_payment_date:
                    # Convert strings to datetime objects
                    date_format = '%Y-%m-%d'
                    date1 = record.shipment_doc_collected_from_applicant_bank
                    date2 = record.supplier_payment_date

                    # Calculate the difference between the two dates
                    time_difference = date2 - date1

                    # Extract the number of days
                    days_difference = time_difference.days
                    record.payment_lead_time = days_difference

            if record.delinquent_settlement_date:
                record.delinquent_status = 'Delinquent'

    def open_lc_detail(self):
        view = self.env.ref('droga_procurement.droga_purchase_lc_view_form')

        return {
            'name': 'LC Reconciliation',
            'view_mode': 'form',
            'res_model': 'droga.purchase.lc',
            'view_id': view.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id
        }

    def button_confirm(self):
        message = ''
        for res in self:
            for line in res.order_line:
                new_items = self.env['product.template'].search([('old_ref', '=', line.product_id.default_code)])
                if len(new_items) > 0:
                    message = message + 'Product ' + line.product_id.default_code + ' has been updated with ' + \
                              new_items[0].default_code + ', '

            sup_id=4

            if res.company_id.id==1 and (res.request_type=='Local' or res.request_type=='Pharmacy'):
                #Droga local
                sup_id=4
            elif res.company_id.id==1 and res.request_type=='Foregin':
                # Droga Foregin
                sup_id = 263
            elif res.company_id.id == 2 and res.request_type == 'Local':
                # EMA local
                sup_id = 842
            elif res.company_id.id == 2 and res.request_type == 'Foregin':
                # EMA Foregin
                sup_id = 843
            elif res.company_id.id == 10 and res.request_type == 'Local':
                # Somaliland local
                sup_id = 871
            elif res.company_id.id == 10 and res.request_type == 'Foregin':
                # Somaliland Foregin
                sup_id = 872
            elif res.company_id.id == 22 and res.request_type == 'Local':
                # Rwanda local
                sup_id = 873
            elif res.company_id.id == 22 and res.request_type == 'Foregin':
                # Rwanda Foregin
                sup_id = 874

            recs=self.env['ir.property'].sudo().search([('name','=','property_stock_supplier'),('res_id', '=', 'res.partner,%s' % res.partner_id.id)])
            if not recs:
                self.env['ir.property'].sudo().create({
                    'res_id': 'res.partner,'+str(res.partner_id.id),
                    'name':'property_stock_supplier',
                    'value':'stock.location,'+str(sup_id),
                    'fields_id':6384,
                    'type':'many2one'
                })
            else:
                recs[0].sudo().write({'value': 'stock.location,'+str(sup_id)})

        if len(message) > 5:
            raise UserError(message)

        return super(purchase_order, self).button_confirm()

    @api.model
    def create(self, vals):
        # get sequence number for each company

        if 'Purchase' not in self.env['stock.picking.type'].browse(vals['picking_type_id']).name:
            raise UserError('Please select either local or foreign purchase under \'Deliver To\' field.')

        company_id = vals.get('company_id', self.default_get(
            ['company_id'])['company_id'])

        self_comp = self.with_company(company_id)

        res = super(purchase_order, self_comp).create(vals)

        request_type = res.request_type

        # Check if there are old items in PO
        message = ''
        for line in res.order_line:
            new_items = self.env['product.template'].search([('old_ref', '=', line.product_id.default_code)])
            if len(new_items) > 0 and not res.from_rfq:
                message = message + 'Product ' + line.product_id.default_code + ' has been updated with ' + new_items[
                    0].default_code + ', '

        if len(message) > 5:
            raise UserError(message)

        if request_type == 'Foregin':
            # generate transaction number
            sequence_no = self.env['droga.finance.utility'].get_transaction_no('POF', vals['date_order'],
                                                                               vals['company_id'])
            res.name = sequence_no or '/'

        elif request_type == 'Local':
            # generate transaction number
            sequence_no = self.env['droga.finance.utility'].get_transaction_no('POL', vals['date_order'],
                                                                               vals['company_id'])
            res.name = sequence_no or '/'

        elif request_type == 'Pharmacy':
            # generate transaction number
            sequence_no = self.env['droga.finance.utility'].get_transaction_no('POP', vals['date_order'],
                                                                               vals['company_id'])
            res.name = sequence_no or '/'

        self.load_po_status(res.id)
        self.load_shipping_reconcilation(res.id)
        return res

    def load_po_status(self, purchase_order_id):
        # get phase 1 or request for quotation steps
        po_steps = self.env["droga.foregin.purchase.phases"].search([])

        for po_step in po_steps:
            # create record in rfq step status one2manyobject
            status = {'purchase_order_id': purchase_order_id,
                      'phase': po_step.id,
                      'status': 'Not Started'}
            # create the record in database
            if po_step.phase_name == "2":  # ordering phase
                self.env['droga.purchase.po.foregin.status'].create(status)
            elif po_step.phase_name == "3":  # shipment phase
                self.env['droga.purchase.po.shipment.foregin.status'].create(
                    status)
            elif po_step.phase_name == "4":  # good clearance
                self.env['droga.purchase.po.clearance.foregin.status'].create(
                    status)
            elif po_step.phase_name == "5":  # post clearance
                self.env['droga.purchase.po.post.clerance.foregin.status'].create(
                    status)

        # get proforma invoice documents
        documents = self.env["droga.purchase.reconciliation.docs"].search([])

        for document in documents:
            pi_status = {
                'purchase_order_id': purchase_order_id,
                'document': document.id,
            }

            if document.doc_type == "Ordering":  # ordering
                self.env['droga.purchase.po.docuemnts.foregin.status'].create(
                    pi_status)
            elif document.doc_type == "Shipment":  # Shipment
                self.env['droga.purchase.po.shipment.docuemnts.foregin.status'].create(
                    pi_status)
            elif document.doc_type == "Good Clearance":  # Good Clearance
                self.env['droga.purchase.po.clearance.docuemnts.foregin.status'].create(
                    pi_status)
            elif document.doc_type == "Post Clearance":  # Post Clearance
                self.env['droga.purchase.po.post.clerance.docuemnts.foregin.status'].create(
                    pi_status)

    def load_shipping_reconcilation(self, purchase_order_id):
        Shipping_reconciliation_docs = self.env['droga.purchase.reconciliation.docs'].search([
            ('doc_type', '=', 'Shipping')])

        for line in Shipping_reconciliation_docs:
            shipping_line = {
                'purchase_order_id': purchase_order_id,
                'name': line.name,
                'order': line.order,
            }
            self.env['droga.purchase.shipping.reconcilation'].create(
                shipping_line)

    @api.onchange('margin', 'exchange_rate_lc_settlement', 'shipment_percent')
    def lc_margin_amount(self):
        for record in self:
            record.deposit_amount = (record.margin * record.amount_total * record.shipment_percent / 100) / 100
            # remaining margin percent
            rem_margin_percent = (100 - record.margin) / 100
            record.shipment_lc_amount = (
                                                record.amount_total_usd * record.exchange_rate_lc_settlement * record.shipment_percent / 100) * rem_margin_percent

    @api.depends("is_it_do")
    def calculate_do_amount(self):
        for record in self:
            if record.is_it_do:
                record.do_amount = record.shipment_percent * 1.1
            else:
                record.do_amount = 0


class purchase_order_line(models.Model):
    _inherit = "purchase.order.line"

    seq_no = fields.Integer("No", compute='compute_sequence_no')
    unit_price_foregin = fields.Float('Unit Price', digits=(12, 4))
    total_price_foregin = fields.Float(
        'Total Price', compute="_compute_total", store=True, inverse="_inverse_compute_total")

    product_category = fields.Many2one(related='product_id.categ_id', store=True)

    rfq_price_total_etb = fields.Float("RFQ Price", compute="compute_rfq_price")
    price_variance_with_rfq = fields.Float("RFQ Price Variance", compute="compute_rfq_price")

    def compute_rfq_price(self):
        for record in self:
            record.rfq_price_total_etb = 0
            record.price_variance_with_rfq = 0

            # get rfq price by product id and rfq id
            rfq_id = record.order_id.rfq_id.id
            product_id = record.product_id.id

            rfq_product_line = self.env['droga.purhcase.request.rfq.line'].search([('rfq_id', '=', rfq_id), ('product_id', '=', product_id)])

            for rfq in rfq_product_line:
                record.rfq_price_total_etb = rfq.total_price
                record.price_variance_with_rfq = record.price_total - rfq.total_price

    def _inverse_compute_total(self):
        pass

    def compute_sequence_no(self):
        seq_no = 1
        for record in self:
            record.seq_no = seq_no
            seq_no += 1

    @api.depends('unit_price_foregin', 'product_qty', 'order_id.exchange_rate')
    def _compute_total(self):
        for record in self:
            if record.order_id.request_type == 'Foregin':
                record.total_price_foregin = record.unit_price_foregin * record.product_qty
                record.price_unit = record.unit_price_foregin * record.order_id.exchange_rate


# partial shipment
class partial_shipment(models.Model):
    _name = 'purchase.order.partial.shipment'

    purchase_order_id = fields.Many2one("purchase.order")
    mode_of_transport = fields.Selection(related='purchase_order_id.mode_of_transport')
    request_type = fields.Selection(related='purchase_order_id.request_type')
    # amount_total = fields.Monetary(related="purchase_order_id.amount_total")
    amount_total_usd = fields.Float(related="purchase_order_id.amount_total_usd")

    # shipment
    shipment_percent = fields.Float("Shipment Amount", required=True)
    shipment_description = fields.Char("Shipment Description", required=True)
    shipment_date = fields.Date("Estimated Shipment Date")
    production_completion_date = fields.Date("Estimaed Production Completion Date")

    # shipment document
    shipment_scan_copy_doc_recived_date = fields.Date("Shipment Document Scan Copy Recived Date")
    shipment_original_copy_doc_recived_date = fields.Date(
        "Shipment Document Original Recived Date")

    shipment_doc_original_sent_from_supplier = fields.Date(
        "Date Original Document Sent from Supplier to Applicant Bank")
    shipment_doc_original_sent_from_supplier_courier = fields.Date(
        "Date Original Document Sent from Supplier to Applicant Bank By Courier")
    document_tracking_number = fields.Char("Courier Tracking No")
    shipment_doc_original_recived_by_applicant_bank = fields.Date(
        "Date Original Document Recived by Applicant Bank")

    # shipment lc amount
    exchange_rate_lc_settlement = fields.Float("Exchange Rate", digits=(12, 4))
    shipment_lc_amount = fields.Float("Deposit Amount for LC Settlement")

    lc_settlement_deposited = fields.Date("LC Settlement Deposited Date")
    shipment_doc_collected_from_applicant_bank = fields.Date(
        "Date Original Document Collected from Applicant Bank")
    shipment_doc_handed_to_finance = fields.Date(
        "Date Original Document Handed to Finance")
    supplier_payment_date = fields.Date("Supplier Payment Date")

    document_tracking_date = fields.Date("Document Tracking Date")

    discrepancy = fields.Selection(
        [('Yes', 'Yes'), ('No', 'No')], string="Discrepancy?")
    accept_discrepancy = fields.Boolean("Accept Discrepancy")
    discrepancy_comment = fields.Html("Discrepancy Comment")
    discrepancy_amount = fields.Float("Discrepancy Amount")

    is_it_do = fields.Boolean("IS it DO")
    do_amount = fields.Float("DO Amount", compute='calculate_do_amount', store=True)

    # good clearance
    goods_arrival_date = fields.Date(
        "Good Arrival Date", help="Good arrival to Port of discharge")
    goods_arrival_date_final_destination = fields.Date(
        "Good Arrival Date to Final Destination", help="Good Arrival Date to Final Destination")

    # mode_of_transport = fields.Selection(related='rfq_id.mod_of_shipment')
    ports = fields.One2many(
        'droga.purchase.arrival.ports', 'purchase_order_id')

    freight_payment_by_air = fields.Float("Freight Amout ETB")
    freight_payment_by_sea = fields.Float("Freight Amount USD")
    freight_payment_by_sea_dg = fields.Float(
        "Freight Amount from Djibouti to Galafi USD", help="From Djibouti to Galafi")
    freight_payment_by_sea_gp = fields.Float(
        "Freight Amount from Galafi to Dry Port ETB", help="From Galafi to Dry Port")

    freight_paid_date = fields.Date("Freight Paid Date")
    container_deposit_amount = fields.Float("Container Deposit Amount")
    container_deposit_status = fields.Selection([('Returned', 'Returned'), ('Not Returned', 'Not Returned')],
                                                default='Not Returned')

    freight_settlement_advice_to_finance = fields.Date(
        "Freight Settlement Debit Advice Handed Over to Finance")
    shipping_doc_to_transitor = fields.Date(
        "Shipping Document & Settlement Advice is Handed Over to Transistor")

    declaration_number = fields.Char("Declaration Number")
    release_permit_applied_to_fda = fields.Date(
        "Release Permit Applied Date to FDA")
    custom_duty_tax_amount = fields.Float("Custom Duty Tax Amount")
    custom_duty_tax_paid_date = fields.Date("Custom Duty Tax Paid Date")
    custom_tax_acceptance = fields.Boolean(
        "Acceptance of the Duty Tax by Custom ")
    custom_duty_tax_additional_amount = fields.Float(
        "Additional Custom Duty Tax Amount")

    custom_duty_tax_additional_actual_paid = fields.Float(
        "Additional Custom Duty Tax Actual Paid Amount")

    custom_duty_withholding_tax = fields.Float("Custom Withholding Tax")

    storage_cost = fields.Float("Storage Cost")
    demurrage_cost = fields.Float("Demurrage Cost")
    local_transport_cost = fields.Float("Local Transport Cost")
    loading_unloading_cost = fields.Float("Loading & Unloading Cost")

    release_permit_received_from_fda = fields.Date(
        "Release Permit Received from FDA")
    release_date_from_customs_delivery = fields.Date(
        "Release Date from Customs to Delivery Warehouse")

    goods_release_date = fields.Date("Release Date", help="Good Release Date")

    # post good clearance
    packing_list_shared_with_inventory = fields.Date(
        "Packing List Shared Date to Inventory")
    goods_arrival_date = fields.Date("Goods Arrival Date to Warehouse")
    grn_reconcilation_form_recived_date = fields.Date(
        "GRN and Reconciliation Form Received Date")
    reconcilation_discrepancy = fields.Boolean("Reconciliation Discrepancy")
    discrepancy_comment = fields.Html("Discrepancy Comment")
    discrepancy_action = fields.Html("Discrepancy Action")
    grn_submitted_to_finance = fields.Date("GRN Submission Date to Finance")
    stamped_declaration_recived_date = fields.Date(
        "Final Custom Stamped Invoice & Declaration Recived Date")
    delinquent_settlement_date = fields.Date("NBE Delinquent Settlement Date")
    transistor_service_payment_Amount = fields.Float(
        "Transitor Service Payment Amount")
    container_deposit_reimbursed_date = fields.Date(
        "Container Deposit Reimbursed Date")
    transistor_service_payment_done_date = fields.Date(
        "Transitor Service Payment Done Date")

    # @api.onchange('exchange_rate_lc_settlement', 'shipment_percent')
    def lc_margin_amount(self):
        for record in self:
            rem_margin_percent = record.shipment_percent / 100
            record.shipment_lc_amount = (
                    record.amount_total_usd * record.exchange_rate_lc_settlement * record.shipment_percent / 100)

    @api.depends("is_it_do")
    def calculate_do_amount(self):
        for record in self:
            if record.is_it_do:
                record.do_amount = record.shipment_percent * 1.1
            else:
                record.do_amount = 0


# arrival ports
class po_ports(models.Model):
    _name = 'droga.purchase.arrival.ports'

    purchase_order_id = fields.Many2one("purchase.order")
    name = fields.Selection(
        [('Bole Airport', 'Bole Airport'), ('Djibouti', 'Djibouti'), ('Mojo', 'Mojo'), ('Kaliti', 'Kaliti')])
    arrival_date = fields.Date('Arrival Date')


# steps
class po_foregin_status(models.Model):
    _name = "droga.purchase.po.foregin.status"
    _description = "Status Tracking for Foreign Purchases"

    purchase_order_id = fields.Many2one("purchase.order")

    phase = fields.Many2one("droga.foregin.purchase.phases")
    phase_name = fields.Selection(related="phase.phase_name", store=True)
    step = fields.Char(related="phase.step")
    order = fields.Integer(related="phase.order")
    status = fields.Selection(
        [("Not Started", "Not Started"), ("On Progress", "On Progress"), ("Done", "Done")])
    done_date = fields.Date("Done Date")
    remark = fields.Char("Remark")


class po_shipment_foregin_status(models.Model):
    _name = "droga.purchase.po.shipment.foregin.status"
    _description = "Status Tracking for Foreign Purchases"

    purchase_order_id = fields.Many2one("purchase.order")

    phase = fields.Many2one("droga.foregin.purchase.phases")
    phase_name = fields.Selection(related="phase.phase_name", store=True)
    step = fields.Char(related="phase.step")
    order = fields.Integer(related="phase.order")
    status = fields.Selection(
        [("Not Started", "Not Started"), ("On Progress", "On Progress"), ("Done", "Done")])
    done_date = fields.Date("Done Date")
    remark = fields.Char("Remark")


class po_clearance_foregin_status(models.Model):
    _name = "droga.purchase.po.clearance.foregin.status"
    _description = "Status Tracking for Foreign Purchases"

    purchase_order_id = fields.Many2one("purchase.order")

    phase = fields.Many2one("droga.foregin.purchase.phases")
    phase_name = fields.Selection(related="phase.phase_name", store=True)
    step = fields.Char(related="phase.step")
    order = fields.Integer(related="phase.order")
    status = fields.Selection(
        [("Not Started", "Not Started"), ("On Progress", "On Progress"), ("Done", "Done")])
    done_date = fields.Date("Done Date")
    remark = fields.Char("Remark")


class po_post_clerance_foregin_status(models.Model):
    _name = "droga.purchase.po.post.clerance.foregin.status"
    _description = "Status Tracking for Foreign Purchases"

    purchase_order_id = fields.Many2one("purchase.order")

    phase = fields.Many2one("droga.foregin.purchase.phases")
    phase_name = fields.Selection(related="phase.phase_name", store=True)
    step = fields.Char(related="phase.step")
    order = fields.Integer(related="phase.order")
    status = fields.Selection(
        [("Not Started", "Not Started"), ("On Progress", "On Progress"), ("Done", "Done")])
    done_date = fields.Date("Done Date")
    remark = fields.Char("Remark")


# documents


class po_ordering_document_status(models.Model):
    _name = "droga.purchase.po.docuemnts.foregin.status"

    _description = "Status Tracking for Ordering Phase Document Tracking"

    purchase_order_id = fields.Many2one("purchase.order")
    document = fields.Many2one("droga.purchase.reconciliation.docs")
    order = fields.Integer(related="document.order")
    done = fields.Boolean("Done", default=False)
    done_date = fields.Date("Done Date")
    remark = fields.Char("Remark")


class po_shipment_document_status(models.Model):
    _name = "droga.purchase.po.shipment.docuemnts.foregin.status"

    _description = "Status Tracking for Ordering Phase Document Tracking"

    purchase_order_id = fields.Many2one("purchase.order")
    document = fields.Many2one("droga.purchase.reconciliation.docs")
    order = fields.Integer(related="document.order")
    done = fields.Boolean("Done", default=False)
    done_date = fields.Date("Done Date")
    remark = fields.Char("Remark")


class po_clearance_document_status(models.Model):
    _name = "droga.purchase.po.clearance.docuemnts.foregin.status"

    _description = "Status Tracking for Ordering Phase Document Tracking"

    purchase_order_id = fields.Many2one("purchase.order")
    document = fields.Many2one("droga.purchase.reconciliation.docs")
    order = fields.Integer(related="document.order")
    done = fields.Boolean("Done", default=False)
    done_date = fields.Date("Done Date")
    remark = fields.Char("Remark")


class po_post_clerance_document_status(models.Model):
    _name = "droga.purchase.po.post.clerance.docuemnts.foregin.status"

    _description = "Status Tracking for Ordering Phase Document Tracking"

    purchase_order_id = fields.Many2one("purchase.order")
    document = fields.Many2one("droga.purchase.reconciliation.docs")
    order = fields.Integer(related="document.order")
    done = fields.Boolean("Done", default=False)
    done_date = fields.Date("Done Date")
    remark = fields.Char("Remark")


class shipping_reconcilation(models.Model):
    _name = 'droga.purchase.shipping.reconcilation'
    _description = 'Shipping Reconciliation'

    purchase_order_id = fields.Many2one('purchase.order')
    name = fields.Char("Name", required=True)
    order = fields.Integer("Step Order", required=True)
    state = fields.Selection([('Right', 'Right'), ('Wrong', 'Wrong')])
    remark = fields.Char("Remark")
