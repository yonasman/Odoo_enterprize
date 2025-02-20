from datetime import datetime, timedelta
from email.policy import default
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class droga_pharma_mtm_history(models.Model):
    _name='droga.pharma.mtm.history'
    #mtm_duration_in_months = fields.Integer("MTM duration in months")
    active_status = fields.Char('Status',compute='_compute_active_state')
    cons_start_date = fields.Date('MTM start date')
    cons_end_date = fields.Date('MTM end date')
    mtm_header=fields.Many2one('droga.pharma.mtm.header')
    origin_sales=fields.Many2one('sale.order')
    client=fields.Many2one('res.partner',related='origin_sales.partner_id')
    no_of_sessions=fields.Integer('Total sessions')
    no_of_sessions_left=fields.Integer(compute='_get_no_of_sessions_left',string='Remaining sessions')

    def _get_no_of_sessions_left(self):
        for rec in self:
            rec.no_of_sessions_left=rec.no_of_sessions-len(self.env['droga.pharma.mtm.follow_up'].search([('origin_sales','=',rec.origin_sales.id)]))
    def _compute_active_state(self):
        for rec in self:
            today = fields.Date.today()
            if today >= rec.cons_start_date and today <= rec.cons_end_date:
                rec.active_status = 'Active'
            else:
                rec.active_status = 'Closed'

class droga_pharma_mtm_header(models.Model):
    _name = 'droga.pharma.mtm.header'
    mtm_history=fields.One2many('droga.pharma.mtm.history','mtm_header')
    _rec_name = "client_descr"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Droga MTM"
    plan_generate_frequency=fields.Integer('Plan generation frequency in days')

    detail_mtm=fields.One2many('droga.pharma.mtm.detail','parent_mtm')
    detail_mtm_followup = fields.One2many('droga.pharma.mtm.follow_up', 'parent_mtm_follow')
    # Related fields
    client = fields.Many2one('res.partner')
    customer = fields.Many2one('droga.pharma.cust.employees',related='sales_origin.customer_emp')
    client_descr= fields.Char(related='client.name')
    sales_origin=fields.Many2one('sale.order')
    mobile = fields.Char("Mobile", related='client.mobile', store=True)
    medical = fields.Html("Medical History",store=True,compute='get_cust_hist',inverse='update_medical',tracking=True)
    medication_history = fields.Html("Medication History and adherence", store=True,compute='get_cust_hist',inverse='update_medication_history',tracking=True)
    immunization = fields.Html("Immunization", store=True,compute='get_cust_hist',inverse='update_immunization',tracking=True)
    adr = fields.Html("ADRS and/or Allergies", store=True,compute='get_cust_hist',inverse='update_adr',tracking=True)

    @api.depends('client.medical_history','client.medication_history','client.immunization','client.adr_allergy','client.dob','client.gender','client.weight','client.height')
    def get_cust_hist(self):
        for rec in self:
            rec.medical=rec.client.medical_history
            rec.medication_history = rec.client.medication_history
            rec.immunization = rec.client.immunization
            rec.adr = rec.client.adr_allergy
            rec.dob = rec.client.dob
            rec.gender=rec.client.gender
            rec.weight=rec.client.weight
            rec.height = rec.client.height

    def update_adr(self):
        for rec in self:
            rec.client.adr_allergy=rec.adr
    def update_immunization(self):
        for rec in self:
            rec.client.immunization=rec.immunization
    def update_medication_history(self):
        for rec in self:
            rec.client.medication_history=rec.medication_history
    def update_medical(self):
        for rec in self:
            rec.client.medical_history=rec.medical
    def update_dob(self):
        for rec in self:
            rec.client.dob=rec.dob
    def update_gender(self):
        for rec in self:
            rec.client.gender=rec.gender
    def inverse_weight(self):
        for rec in self:
            rec.client.weight = rec.weight

    def inverse_height(self):
        for rec in self:
            rec.client.height = rec.height

    dob = fields.Date("Date of Birth", store=True,compute='get_cust_hist',inverse='update_dob')
    age = fields.Integer("Age", compute="_compute_age", readonly=True)
    gender = fields.Selection(selection=[("Male", "Male"), ("Female", "Female")], string="Gender", store=True,compute='get_cust_hist',inverse='update_gender')
    profession = fields.Selection(selection=[("hp", "Health Professional"), ("other", "Other")], string="Profession", store=True)
    weight = fields.Float("Weight", compute='get_cust_hist', store=True, inverse='inverse_weight')
    height = fields.Float("Height (in meters)", compute='get_cust_hist', store=True, inverse='inverse_height')
    bmi = fields.Float(compute='_get_bmi', string='BMI')

    @api.depends('weight','height','client.weight','client.height')
    def _get_bmi(self):
        for rec in self:
            rec.bmi = rec.weight / (rec.height * rec.height) if rec.height != 0 else 0
    bsa = fields.Float("BSA")
    address = fields.Char("Address")
    pregnancy = fields.Char("Pregnancy status")
    diagnosis = fields.Text("Diagnosis")
    physician = fields.Char("Primary physician and contact information")

    check_compute = fields.Boolean(default=False, store=True)

    @api.depends("dob")
    def _compute_age(self):
        for record in self:
            if record.dob:
                record.age = datetime.now().year - record.dob.year
            else:
                record.age = 0

    def create_an_activity(self,rec, user_id, message):
        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env.ref('droga_pharma.model_droga_pharma_mtm_header').id,
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
        records = self.search([('cons_end_date', '>=', today), ('next_schedule', '=', today)])
        for rec in records:
            message = "The mtm customer "+rec.client_descr+" has a follow up today."
            self.create_an_activity(rec, rec.create_uid.id, message)
            rec.prev_schedule = today
            rec.next_schedule = today + timedelta(days=rec.plan_generate_frequency)

    @api.model
    def create(self, vals):
        res=super(droga_pharma_mtm_header, self).create(vals)
        if not res.client:
            raise ValidationError(
                "Customer must be registered to initiate an MTM order.")
        return res


class droga_pharma_mtm_detail(models.Model):
    _name = 'droga.pharma.mtm.detail'

    parent_mtm=fields.Many2one('droga.pharma.mtm.header')

    # Text fields
    indication = fields.Char("Indication", required=True)
    drug = fields.Many2one('product.template', string='Drug')
    frequency = fields.Char("Frequency")
    frequency_type = fields.Selection([("Hourly", "Hourly"),("Daily", "Daily"), ("Weekly", "Weekly"), ('Monthly', 'Monthly')], default='Daily',string='Rate')
    start_date = fields.Date('Start date')
    stop_date = fields.Date('Stop date')
    date = fields.Date("Date")
    remark = fields.Char("Remark")

class droga_pharma_mtm_schedule(models.Model):
    _name = 'droga.pharma.mtm.follow_up'

    parent_mtm_follow = fields.Many2one('droga.pharma.mtm.header')

    date_follow_up=fields.Date('Follow up date')
    time=fields.Char('Follow up time')
    current_status=fields.Many2one('droga.pharma.current_status',string='Current status')

    follow_up_detail=fields.One2many('droga.pharma.mtm.follow_up.detail','parent_follow_up')

    eff_saf_med = fields.Html('Effectiveness and safety of medication')
    int_imple = fields.Html('Intervention implemented')
    plan = fields.Html("Plans and goals for next followup")
    referral = fields.Boolean("Sent referral for further diagnosis")
    asses_care_plan = fields.Html('Assessment and care plan')
    recs_inter = fields.Html('Recommendations / Interventions')
    from_sales_order = fields.Boolean("From Sales order?", default=False)
    origin_sales=fields.Many2one('sale.order')
    def open_follow_up_form(self):
        return {
            'name': 'Follow up',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'droga.pharma.mtm.follow_up',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.id
        }

    @api.model
    def create(self, vals):
        res=super(droga_pharma_mtm_schedule, self).create(vals)
        sod=self.env['droga.pharma.mtm.history'].search([('cons_start_date','<=',res.date_follow_up),('cons_end_date','>=',res.date_follow_up),('client','=',res.parent_mtm_follow.client.id)])
        for sd in sod:
            if sd.no_of_sessions-len(self.search([('origin_sales','=',sd.origin_sales.id)]))>0:
                vals['origin_sales']=sd.origin_sales.id
                res.origin_sales = sd.origin_sales.id
                return res

        raise UserError("There're no active MTM orders to create a follow up.")


class droga_pharma_mtm_schedule_detail(models.Model):
    _name = 'droga.pharma.mtm.follow_up.detail'
    parent_follow_up=fields.Many2one('droga.pharma.mtm.follow_up')

    drug_therapy_problem = fields.Many2one('droga.pharma.drug.therapy.problem', string='Drug therapy problem')
    drug_therapy_cause = fields.Many2one('droga.pharma.drug.therapy.problem.cause', string='Drug therapy cause',
                                         domain="[('problem_id','=',drug_therapy_problem)]")
    intervention = fields.Char('Intervention', compute='_get_default_intervention', store=True,
                               inverse='_inverse_function')
    def _inverse_function(self):
        pass
    @api.depends('drug_therapy_cause')
    def _get_default_intervention(self):
        for rec in self:
            rec.intervention=rec.drug_therapy_cause.recommended_intervention.descr

    intervention_implemented = fields.Selection(selection=[('fully', 'Fully Implemented'), ('partial', 'Partially Implemented'), ('rejected', 'Rejected')],string='Intervention implemented?')
    outcome = fields.Selection(selection=[('resolved', 'Resolved'), ('stable', 'Stable'),
                                          ('partial_improvement', 'Partial Improvement'),
                                          ('unimproved', 'Unimproved'), ('worsened', 'Worsened'),
                                          ('failure', 'Failure'), ('expiry', 'Expiry')])
    # asses_care_plan = fields.Html('Assessment and care plan',
    #                               related='parent_follow_up.parent_mtm_follow.asses_care_plan')
    #
    # recs_inter = fields.Html('Recommendations / Interventions',
    #                          related='parent_follow_up.parent_mtm_follow.recs_inter')
    client = fields.Many2one('res.partner', related='parent_follow_up.parent_mtm_follow.client')
    customer = fields.Many2one('droga.pharma.cust.employees', related='parent_follow_up.parent_mtm_follow.customer')

    indication = fields.Char("Indication", compute='get_indication')

    def get_indication(self):
        for fu in self:
            ind = []
            for fud in fu.parent_follow_up.parent_mtm_follow.detail_mtm:
                ind.append(fud.indication)
            fu.indication = ",".join(ind)

    drug = fields.Char("Drug", compute='get_drugs')

    def get_drugs(self):
        for followup in self:
            drugs = []
            for f_drug in followup.parent_follow_up.parent_mtm_follow.detail_mtm:
                drugs.append(f_drug.drug.display_name)
            followup.drug = ",".join(drugs)

    remark = fields.Char('Remark')
