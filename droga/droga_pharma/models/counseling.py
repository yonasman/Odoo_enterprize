from datetime import datetime
from email.policy import default
from odoo import models, fields, api
from odoo.exceptions import UserError


class droga_pharma_counselling(models.Model):
    _name = 'droga.pharma.counselling'

    #Text fields
    # area_counsel=fields.Many2one('droga.pharma.area_counsel',string='Area of counselling')
    coun_code = fields.Char("Counselling session ID", default='New',readonly=True)
    counselling_cat = fields.Selection(selection=[('life_style', 'Life style'), ('medication_use', 'Medication Use')], string='Area of counselling',required=True)
    description = fields.Char("Area of counselling description")
    status=fields.Char("Status")
    ses_acceptance= fields.Selection([('Accepted', 'Accepted'), ('Rejected', 'Rejected')],string="Acceptance")
    pharmacist_lev_understanding=fields.Selection([('High', 'High'), ('Optimal', 'Optimal'),('Low', 'Low')],string='Pharmacist level of understanding')
    assessment = fields.Html("Assessment")
    date=fields.Date('Date',default=datetime.today())
    sales_origin = fields.Many2one('sale.order',required=True)
    counselling_given = fields.Html("Counselling given")
    patient_lev_understanding=fields.Selection([('High', 'High'), ('Optimal', 'Optimal'),('Low', 'Low')],string='Patient Level of understanding')
    # Related fields
    client = fields.Many2one('res.partner')
    client_descr = fields.Char(related='client.name')
    customer = fields.Many2one('droga.pharma.cust.employees', related='sales_origin.customer_emp')
    mobile = fields.Char("Mobile", compute='get_cust_hist', store=True, inverse='inverse_mobile', tracking=True)
    dob = fields.Date("Date of Birth", store=True, compute='get_cust_hist', inverse='inverse_dob')
    age = fields.Integer("Age", compute="_compute_age", readonly=True)
    gender = fields.Selection(selection=[("Male", "Male"), ("Female", "Female")], string="Gender", store=True,
                              compute='get_cust_hist', inverse='update_gender')

    medical = fields.Html("Medical History", store=True, compute='get_cust_hist', inverse='update_medical',
                          tracking=True)
    medication_history = fields.Html("Medication History and adherence", store=True, compute='get_cust_hist',
                                     inverse='update_medication_history', tracking=True)
    immunization = fields.Html("Immunization", store=True, compute='get_cust_hist', inverse='update_immunization',
                               tracking=True)
    adr = fields.Html("ADRS and/or Allergies", store=True, compute='get_cust_hist', inverse='update_adr', tracking=True)

    @api.depends('client.medical_history', 'client.medication_history', 'client.immunization', 'client.adr_allergy',
                 'client.dob', 'client.gender', 'client.mobile','client.weight', 'client.height')
    def get_cust_hist(self):
        for rec in self:
            rec.medical = rec.client.medical_history
            rec.medication_history = rec.client.medication_history
            rec.immunization = rec.client.immunization
            rec.adr = rec.client.adr_allergy
            rec.dob = rec.client.dob
            rec.gender = rec.client.gender
            rec.mobile = rec.client.mobile
            rec.weight=rec.client.weight
            rec.height = rec.client.height

    def update_adr(self):
        for rec in self:
            rec.client.adr_allergy = rec.adr

    @api.model
    def create(self, vals_list):
        if vals_list.get('coun_code', 'New') == 'New':
            _name = self.env['ir.sequence'].next_by_code('droga.pharma.counselling.session.sequence')
            if not _name:
                raise UserError("Order sequence not found.")
            vals_list['coun_code'] = _name

        return super(droga_pharma_counselling, self).create(vals_list)

    def update_immunization(self):
        for rec in self:
            rec.client.immunization = rec.immunization
    def update_gender(self):
        for rec in self:
            rec.client.gender=rec.gender
    def update_medication_history(self):
        for rec in self:
            rec.client.medication_history = rec.medication_history

    def update_medical(self):
        for rec in self:
            rec.client.medical_history = rec.medical

    _sql_constraints = [
        ('sales_consulting', 'unique (sales_origin)',
         'Only a single counselling session can be conducted per sales order.')
    ]

    def inverse_dob(self):
        for rec in self:
            rec.client.dob = rec.dob

    def inverse_mobile(self):
        for rec in self:
            rec.client.mobile = rec.mobile

    def inverse_weight(self):
        for rec in self:
            rec.client.weight = rec.weight

    def inverse_height(self):
        for rec in self:
            rec.client.height = rec.height
    @api.depends("dob")
    def _compute_age(self):
        for record in self:
            if record.dob:
                record.age = datetime.now().year - record.dob.year
            else:
                record.age = 0


    profession = fields.Selection(selection=[("hp", "Health Professional"), ("other", "Other")], string="Profession", store=True)
    weight = fields.Float("Weight",compute='get_cust_hist',store=True,inverse='inverse_weight')
    height = fields.Float("Height (in meters)",compute='get_cust_hist',store=True,inverse='inverse_height')
    bsa = fields.Float("BSA")
    bmi=fields.Float(compute='_get_bmi',string='BMI')
    @api.depends('weight','height','client.weight','client.height')
    def _get_bmi(self):
        for rec in self:
            rec.bmi=rec.weight/(rec.height*rec.height) if rec.height!=0 else 0
    address = fields.Char("Address")
    pregnancy = fields.Boolean("Pregnancy status")
    diagnosis = fields.Text("Diagnosis")
    physician = fields.Char("Primary physician and contact information")
