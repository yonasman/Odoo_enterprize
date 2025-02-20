from odoo import models, fields,api
from odoo.exceptions import UserError


class droga_tender_submission_detail(models.Model):
    _name = 'droga.tender.submission.detail'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    #Selection fields
    tech_result = fields.Selection([('Pass', 'Pass'), ('Fail', 'Fail')])
    status = fields.Selection([('awarded', 'Awarded'), ('cancelled', 'Cancelled'),('undeva', 'Under evaluation'),('faiten', 'Failed tender'),('lost', 'Lost')],tracking=True)

    #Text fields
    lot_number=fields.Char("Lot Number",required=True)
    item_des = fields.Char("Item requested old")
    item_des_list = fields.Many2one('droga.tender.products',string="Item requested")
    item_pro = fields.Char("Item proposed")
    product=fields.Many2one('product.product','Product')
    brand_model = fields.Char("Brand/Model")
    remark = fields.Char("Description and remark")
    award_fold_num = fields.Char("Award folder number")
    supplier_new=fields.Char('Supplier')
    uom_free_field=fields.Char('UOM unregistered')
    uom_reg_field = fields.Many2one('droga.tender.uom',string='UOM')
    item_num=fields.Integer('Item Number')
    deliv_period_text = fields.Char("Delivery period")

    def open_tender(self):
        return {
            'name': 'Tender',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'droga.tender.master',
            'type': 'ir.actions.act_window',
            'res_id': self.parent_tender_submission.id,
        }

    procurement_title = fields.Char(related='parent_tender_submission.procurement_title')
    closing_date_gre = fields.Datetime(related='parent_tender_submission.closing_date_gre')
    cus_type = fields.Many2one(related='parent_tender_submission.customer_type', string='Customer type', store=True)
    latest_invoice_date = fields.Date('Invoice date')

    _sql_constraints = [
            ('lot_number_item_num_unique', 'unique (lot_number,item_num,month)', 'The combination lot number and item number already exists!')
        ]

    # decimal fields
    quantity=fields.Float("Quantity",default=1)
    unit_price = fields.Float("Unit Price",tracking=True)
    amount = fields.Float("Amount",compute="compute_amount")
    @api.depends("unit_price","quantity")
    def compute_amount(self):
        for rec in self:
            rec.amount=rec.unit_price*rec.quantity
    deliv_period = fields.Float("Delivery days")

    # relational fields
    type_item = fields.Many2one('droga.tender.settings.type.item', string='Type or items',required=True)
    parent_tender_submission=fields.Many2one('droga.tender.master',required=True)
    unit_of_measure=fields.Many2one('uom.uom', string='UOM')
    currency=fields.Many2one('res.currency',string='Currency')
    supplier=fields.Many2one('res.partner',string='Existing supplier')
    country = fields.Many2one('res.country', string='Country')
    incoterm=fields.Many2one('droga.tender.settings.incoterm','Incoterm')
    tender_specs=fields.One2many('droga.tender.specs.detail','submission_detail')
    competi_id = fields.One2many('droga.tender.competitors', 'submission_id')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    detail_performance = fields.One2many('droga.tender.performance.evaluation', 'parent_tender_performance_detail')

    # Date fields
    fin_open = fields.Datetime("Financial opening GRE")
    st_date = fields.Date("Status date GRE")
    expiry_date = fields.Date("Expiry date")
    expiry_date_char = fields.Char("Expiry date")

    def competitors_open(self):
        return {
            'name': 'Competitors',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'droga.tender.submission.detail',
            'view_id': self.env.ref('droga_tender.droga_tender_competitors_view_tree').id,
            'type': 'ir.actions.act_window',

            # This will pass the detail ID if a record is present
            'res_id': self.id,

            # When target is new, it will popup else it will use it's own form, wow ferenj
            'target': 'new',

        }

    def tech_specs_open(self):
        return {
            'name': 'Technical specification',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'droga.tender.submission.detail',
            'view_id': self.env.ref('droga_tender.droga_tender_specs_view_tree').id,
            'type': 'ir.actions.act_window',

            # This will pass the detail ID if a record is present
            'res_id': self.id,

            # When target is new, it will popup else it will use it's own form, wow ferenj
            #'target': 'new',

        }
    @api.model
    def create(self, vals_list):
        res = super().create(vals_list)
        if vals_list["quantity"]==0:
            raise UserError("Quantity can not be zero.")
        if "status" in vals_list:
            if vals_list["status"]=="awarded":
                to_create_perf_eval = {
                    "award_cost":vals_list["unit_price"]*vals_list["quantity"],"award_quantity":vals_list["quantity"],
                    "parent_tender_performance": vals_list["parent_tender_submission"],
                    "parent_tender_performance_detail": res.id,
                }
                self.env["droga.tender.performance.evaluation"].create(to_create_perf_eval)
                cont_created=self.env['droga.tender.contract'].search([('lot_number','=',vals_list["lot_number"])])
                if len(cont_created)==0:
                    to_create_cont_agreement = {
                    "lot_number": vals_list["lot_number"],
                    "type_item": vals_list["type_item"],
                    "parent_tender_contract": vals_list["parent_tender_submission"],
                    'company_id':vals_list["company_id"]
                    }
                    self.env["droga.tender.contract"].create(to_create_cont_agreement)

                    if not self.parent_tender_submission.customer.master_cust_id and not self.parent_tender_submission.alert_sent:
                        channels = self.env['mail.channel'].search([('name', '=', 'Tender sales')])

                        message = "Please register customer named '" + self.parent_tender_submission.customer.name + "'."
                        message = message + ' Tin No - ' + self.parent_tender_submission.customer.tin_no if self.parent_tender_submission.customer.tin_no else message
                        for c in channels:
                            c.message_post(
                                subject="Customer registration.",
                                body=message,
                                message_type='comment',
                                subtype_xmlid='mail.mt_comment',
                                author_id=self.env.user.id,
                            )

        return res

    def write(self, vals):
        if 'quantity' in vals:
            if vals["quantity"]==0:
                raise UserError("Quantity can not be zero.")

        if 'incoterm' in vals:
            # Select and update values here
            pass

        if 'award_fold_num' in vals:
            # Select and update values here
            pass

        if 'currency' in vals:
            # Select and update values here
            pass



        if 'status' not in vals:
            return super().write(vals)
        if vals["status"]=="awarded":
            to_create_perf_eval = {
                "parent_tender_performance_detail": self.id,"award_quantity":(vals['quantity'] if 'quantity' in vals else self.quantity),
                "award_cost": (vals['unit_price'] if 'unit_price' in vals else self.unit_price) * (vals['quantity'] if 'quantity' in vals else self.quantity),
                "parent_tender_performance": self.parent_tender_submission.id,
            }
            self.env["droga.tender.performance.evaluation"].create(to_create_perf_eval)

            cont_created = self.env['droga.tender.contract'].search([('lot_number', '=', self.lot_number)])
            if len(cont_created) == 0:
                to_create_cont_agreement = {
                    "lot_number": self.lot_number,
                    "type_item": self.type_item.id,
                    "item_des": self.item_des,
                    "parent_tender_contract": self.parent_tender_submission.id,
                }
                self.env["droga.tender.contract"].create(to_create_cont_agreement)

            if not self.parent_tender_submission.customer.master_cust_id and not self.parent_tender_submission.alert_sent:
                channels = self.env['mail.channel'].search([('name', '=', 'Tender sales')])

                message = "Please register customer named '" + self.parent_tender_submission.customer.name + "'."
                message = message + ' Tin No - ' + self.parent_tender_submission.customer.tin_no if self.parent_tender_submission.customer.tin_no else message
                for c in channels:
                    c.message_post(
                        subject="Customer registration.",
                        body=message,
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment',
                        author_id=self.env.user.id,
                    )
                self.parent_tender_submission.alert_sent=True

        return super().write(vals)


class droga_tender_products(models.Model):
    _name='droga.tender.products'
    _rec_name = 'product'
    product=fields.Char('Product')
