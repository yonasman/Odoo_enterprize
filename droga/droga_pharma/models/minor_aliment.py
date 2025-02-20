from datetime import datetime
from email.policy import default
from odoo import models, fields, api

class droga_pharma_minor_alignment(models.Model):
    _name = 'droga.pharma.minor.alignment'
    _description = 'Droga Minor Aliments'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    #Text fields
    minor_align=fields.Char("Minor ailment",required=True)
    decision = fields.Selection(
        [('Advice only', 'Advice only'), ('Advice and treatment', 'Advice and treatment')])
    referral=fields.Selection(
        [('Urgent', 'Urgent'), ('Appointment', 'Appointment')])

    treatment=fields.Many2many('product.template')
    detail_minor_alignment_followup = fields.One2many('droga.pharma.minor.alignment.follow_up', 'parent_minor_alignment')
    aliment_treatments=fields.One2many('droga.pharma.minor.alignment.products', 'parent_minor_alignment_prod')

    # Related fields
    client = fields.Many2one('res.partner')
    client2 = fields.Many2one('res.partner.pharma2',string='Client')
    customer = fields.Many2one('droga.pharma.cust.employees', related='sales_origin.customer_emp')
    client_descr = fields.Char(related='sales_origin.emp_descr')
    sales_origin = fields.Many2one('sale.order')
    mobile = fields.Char("Mobile", compute='get_mobile',reverse='_update_mob')
    def _update_mob(self):
        for rec in self:
            rec.client2.partner.mobile = rec.mobile

    @api.depends('client2')
    def get_mobile(self):
        for rec in self:
            rec.mobile=rec.client2.partner.mobile
    medical = fields.Html("Medical History", store=True, compute='get_cust_hist', inverse='update_medical',
                          tracking=True)
    medication_history = fields.Html("Medication History and adherence", store=True, compute='get_cust_hist',
                                     inverse='update_medication_history', tracking=True)
    immunization = fields.Html("Immunization", store=True, compute='get_cust_hist', inverse='update_immunization',
                               tracking=True)
    adr = fields.Html("ADRS and/or Allergies", store=True, compute='get_cust_hist', inverse='update_adr', tracking=True)
    dob = fields.Date("Date of Birth", compute='get_dob', store=True, inverse='inverse_dob', tracking=True)
    age = fields.Integer("Age", compute="_compute_age", readonly=True)

    def get_cust_hist(self):
        for rec in self:
            rec.medical = rec.client2.partner.medical_history
            rec.medication_history = rec.client2.partner.medication_history
            rec.immunization = rec.client2.partner.immunization
            rec.adr = rec.client2.partner.adr_allergy
            rec.dob = rec.client2.partner.dob
            rec.gender = rec.client2.partner.gender

    def update_adr(self):
        for rec in self:
            rec.client2.partner.adr_allergy = rec.adr

    def update_immunization(self):
        for rec in self:
            rec.client2.partner.immunization = rec.immunization

    def update_medication_history(self):
        for rec in self:
            rec.client2.partner.medication_history = rec.medication_history

    def update_medical(self):
        for rec in self:
            rec.client2.partner.medical_history = rec.medical

    def get_dob(self):
        for rec in self:
            rec.dob = rec.client2.partner.dob
    def inverse_dob(self):
        for rec in self:
            rec.client2.partner.dob = rec.dob

    def init_sales(self):
        order_lines = []
        sod=self.env['sale.order'].search([('minor_align_header','=',self.id)])
        if len(sod)>0:
            return {
                'name': 'Sales order',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'view_id': self.env.ref('droga_pharma.view_order_form_pharma').id,
                'type': 'ir.actions.act_window',

                'domain':
                    ([('id', '=', sod[0].id)]),
                'res_id': sod[0].id,
            }

        for line in self.aliment_treatments:
            order_lines.append({
                'name': line.product.product_tmpl_id.name,
                'product_template_id': line.product.product_tmpl_id.id,
                'product_uom': line.product.product_tmpl_id.uom_id.id,
                'product_id':line.product.id,
                'product_uom_pharma_qty': line.quantity,
                'price_unit': line.product.product_tmpl_id.list_price_phar,
            })

        return {
            'name': 'Sales order',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'view_id': self.env.ref('droga_pharma.view_order_form_pharma').id,
            'type': 'ir.actions.act_window',
            'context': {
                'default_partner_custom': self.client2.id,
                'default_order_line': order_lines,
                'default_state':'draft',
                'default_minor_align_header':self.id,
                'default_payment_term_id': 11,
                'default_pricelist_id': 2,
                'default_currency_id': 77,
                'default_order_from':'PH'
            },
            'domain':
                ([('minor_align_header', '=', self.id)])
        }

    @api.depends("dob")
    def _compute_age(self):
        for record in self:
            if record.dob:
                record.age = datetime.now().year - record.dob.year
            else:
                record.age = 0

    gender = fields.Selection(selection=[("Male", "Male"), ("Female", "Female")], string="Gender", store=True)
    profession = fields.Selection(selection=[("hp", "Health Professional"), ("other", "Other")], string="Profession", store=True)
    address = fields.Char("Address")
    diagnosis = fields.Text("Diagnosis")
    physician = fields.Char("Primary physician and contact information")
    next_date = fields.Date("Next appointment date")

    def create_an_activity(self,rec, user_id, message):
        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env.ref('droga_pharma.model_droga_pharma_minor_alignment').id,
            'res_name': message,
            'res_id': rec.id,
            'automated': True,
            'user_id': user_id,
            'activity_type_id': 4,
            'summary': message,
            'note': message
        })

    def set_activity_done(self):
        activity = self.env["mail.activity"].search(
            [('res_id', '=', self.id)])
        if activity:
            activity.sudo().action_done()

    def mtm_schedule(self):
        today = fields.Date.today()
        records = self.search([('next_date', '=', today)])
        for rec in records:
            message = "The customer "+rec.client_descr+" has an appointment for "+rec.minor_align
            self.create_an_activity(rec, rec.create_uid.id, message)

class droga_minor_alignment_products_detail(models.Model):
    _name = 'droga.pharma.minor.alignment.products'
    product=fields.Many2one('product.product')
    quantity=fields.Float('Quantity')
    parent_minor_alignment_prod = fields.Many2one('droga.pharma.minor.alignment')

class droga_minor_alignment_schedule(models.Model):
    _name = 'droga.pharma.minor.alignment.follow_up'

    parent_minor_alignment = fields.Many2one('droga.pharma.minor.alignment')

    date_follow_up=fields.Date('Date')
    current_status=fields.Many2one('droga.pharma.current_status',string='Current status')
    decision = fields.Selection(
        [('Advice only', 'Advice only'), ('Advice and treatment', 'Advice and treatment')])
    referral = fields.Selection(
        [('Urgent', 'Urgent'), ('Appointment', 'Appointment')])
    treatment = fields.Many2many('product.template')