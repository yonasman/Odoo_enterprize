import datetime
from datetime import datetime,date,timedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class droga_pharma_customer(models.Model):
    _inherit = 'res.partner'
    allowed_product_groups = fields.Many2many('product.category')
    employees = fields.One2many('droga.pharma.cust.employees', 'parent_customer')
    memberships_partner=fields.One2many('droga.pharma.membership', 'parent_customer')
    company_type = fields.Selection(string='Company Type',
                                    selection=[('person', 'Individual'), ('company', 'Company')])
    childs = fields.One2many('droga.pharma.child', 'parent_cust', string='Childs')
    weight = fields.Float("Weight")
    height = fields.Float("Height (in meters)")
    bmi = fields.Float(compute='_get_bmi',string='BMI')

    @api.depends('weight','height')
    def _get_bmi(self):
        for rec in self:
            rec.bmi = rec.weight / (rec.height * rec.height) if rec.height != 0 else 0
    def open_children(self):
        return {
            'name': 'Children',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.partner',
            'view_id': self.env.ref('droga_pharma.droga_pharma_children_cust').id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            # This will pass the detail ID if a record is present
            'domain': [('parent_cust', '=', self.id)],
            'target': 'new',
        }
    dob = fields.Date("Date of Birth", store=True)
    age = fields.Integer("Age", compute="_compute_age", readonly=True)

    @api.depends("dob")
    def _compute_age(self):
        for record in self:
            if record.dob:
                record.age = datetime.now().year - record.dob.year
            else:
                record.age = 0

    gender = fields.Selection(
        [('Male', 'Male'), ('Female', 'Female')],
        string='Gender', tracking=True)
    profession = fields.Selection(
        [('hp', 'Health professional'), ('other', 'Other')],
        string='Profession')
    medical_history = fields.Html('Medical history', tracking=True)
    medication_history = fields.Html('Medication history and adherance', tracking=True)
    adr_allergy = fields.Html('ADRs and/or Allergies', tracking=True)
    immunization = fields.Html('Immunization', tracking=True)
    show_beauty_button = fields.Boolean(compute='_show_supp_vit',string='Has beauty pick reward')
    show_vit_button = fields.Boolean(compute='_show_supp_vit',string='Has vitamin reward')

    def _show_supp_vit(self):
        for rec in self:
            rec.show_beauty_button = False
            rec.show_vit_button = False
            if rec.is_company:
                return
            discount_per_acc = self.env['droga.pharma.reward.issue'].search(
                [('type', 'in', ('Referral reward', 'Speciality service reward'))])
            for disc in discount_per_acc:
                if disc.reward_req_points <= sum(self.env['droga.pharma.points.earned'].search(
                        [('customer', '=', rec.id), ('type', '=', disc.type), (
                                'earned_date', '>=',
                                date.today() - timedelta(days=disc.reward_req_frequ))]).mapped(
                    'points_earned')):
                    if disc.type == "Referral reward":
                        rec.show_beauty_button = True
                    else:
                        rec.show_vit_button = True

    def action_beautypicks(self):
        det_entries = []
        disc = self.env['droga.pharma.reward.issue'].search(
            [('type', '=', ('Referral reward'))])[0]
        det_entries.append({
            'product_id': self.env['product.product'].search([('product_tmpl_id', '=', disc.prod_template.id)])[0].id,
            'product_uom_pharma': disc.uom.id,
            'product_uom_qty': disc.quantity,
            'warehouse_id': [self.env.user.warehouse_ids_ph_disp + self.env.user.warehouse_ids_im_ws][0].ids[0]
        })
        return {
            'name': 'Reward - Beauty-picks',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'droga.inventory.consignment.issue',
            'views': [[self.env.ref('droga_pharma.droga_inventory_reward_issue_view_form').id, 'form']],
            'type': 'ir.actions.act_window',
            'context': {
                'default_issue_type': 'RWDB',
                'default_customer': self.id,
                'default_detail_entries':det_entries,
                'default_points_to_deduct':disc.reward_req_points
            },
        }

    def action_supp_rewards(self):
        det_entries = []
        disc = self.env['droga.pharma.reward.issue'].search(
            [('type', '=', ('Speciality service reward'))])[0]
        det_entries.append({
            'product_id': self.env['product.product'].search([('product_tmpl_id','=',disc.prod_template.id)])[0].id,
            'product_uom_pharma': disc.uom.id,
            'product_uom_qty': disc.quantity,
            'warehouse_id': [self.env.user.warehouse_ids_ph_disp + self.env.user.warehouse_ids_im_ws][0].ids[0]

        })
        return {
            'name': 'Reward - Supplements',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'droga.inventory.consignment.issue',
            'views': [[self.env.ref('droga_pharma.droga_inventory_reward_issue_view_form').id, 'form']],
            'type': 'ir.actions.act_window',
            'context': {
                'default_issue_type': 'RWDS',
                'default_customer': self.id,
                'default_detail_entries': det_entries,
                'default_points_to_deduct': disc.reward_req_points
            },
        }
class droga_pharma_customer_employees(models.Model):
    _name = 'droga.pharma.cust.employees'

    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']

    _rec_name = 'descr'

    memberships_employee = fields.One2many('droga.pharma.membership', 'parent_employee')
    sales=fields.One2many(  'sale.order','customer_emp')
    sales_detail=fields.One2many('sale.order.line',related='sales.order_line')

    descr = fields.Char('descr', compute='_get_descr',store=True)
    parent_customer = fields.Many2one('res.partner', string='Company Name')
    employer_name = fields.Char(related='parent_customer.name', store=True)
    employee_name = fields.Char('Employee Name', required=True)
    mobile = fields.Char('Mobile')
    job_position = fields.Char(string='Job position')
    company_limit= fields.Float(string='Credit limit', tracking=True,related='parent_customer.cust_credit_limit_pharma')
    employee_credit_limit=fields.Float('Credit limit',default=0,tracking=True)
    cust_id=fields.Char('Employee ID')
    gender = fields.Selection(
        [('Male', 'Male'), ('Female', 'Female')],
        string='Gender', tracking=True)
    profession=fields.Selection(
        [('hp', 'Health professional'),('other', 'Other')],
        string='Profession')
    medical_history = fields.Html('Medical history', tracking=True)
    medication_history = fields.Html('Medication history and adherance', tracking=True)
    adr_allergy = fields.Html('ADRs and/or Allergies', tracking=True)
    immunization = fields.Html('Immunization', tracking=True)
    age = fields.Integer(compute='_compute_age')
    phone_no = fields.Char('Phone No',tracking=True)
    dob = fields.Date('Date of birth', default=date.today(),tracking=True)
    additional_product_groups=fields.Many2many('product.category')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    max_amount=fields.Float(string='Max amount')
    from_date=fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    amount_valid_for=fields.Float(string='Period')
    amount_valid_type = fields.Selection(
        [('Day', 'Day'), ('Month', 'Month'),('Year', 'Year')],
        string='Period type')
    remaining_amount_period=fields.Char(string='Remaining',compute='_remain_amount_period')


    @api.model
    def create(self, vals):
        res=super(droga_pharma_customer_employees, self).create(vals)
        for rec in res:
            if rec.parent_customer.id!=15488 and rec.cust_id==False:
                raise UserError("Employee id must be entered.")
            if len(rec.env['droga.pharma.cust.employees'].sudo().search(
                    [('cust_id', '=',rec.cust_id), ('parent_customer', '!=', 15488),('id','!=',rec.ids[0]), ('parent_customer', '=', rec.parent_customer.id)]))>0:
                raise UserError("Employees ID must be unique per company.")
        return res

    def write(self,vals):
        for rec in self:
            if len(rec.env['droga.pharma.cust.employees'].sudo().search(
                    [('cust_id', '=',rec.cust_id), ('parent_customer', '!=', 15488),('id','!=',rec.ids[0]), ('parent_customer', '=', rec.parent_customer.id)]))>0:
                raise UserError("Employees ID must be unique per company.")
        return super(droga_pharma_customer_employees, self).write(vals)

    def open_children(self):
        return {
            'name': 'Children',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'droga.pharma.cust.employees',
            'view_id': self.env.ref('droga_pharma.droga_pharma_children').id,
            'type': 'ir.actions.act_window',

            # This will pass the detail ID if a record is present
            'res_id': self.id,
            'target': 'new',
        }

    def _remain_amount_period(self):
        for rec in self:
            rec.remaining_amount_period='FIX ME'

    @api.depends('phone_no','employee_name')
    def _get_descr(self):
        for record in self:
            try:
                name = ' - '+record.phone_no if record.phone_no else ''

                record.descr = record.employee_name+name
            except:
                record.descr = record.employee_name if record.employee_name else ' '

    @api.depends('dob')
    def _compute_age(self):
        for record in self:
            if record.dob:
                today = date.today()
                # Check if the date has passed this year
                if today.strftime("%m%d") >= record.dob.strftime("%m%d"):
                    record['age'] = today.year - record.dob.year
                else:
                    record['age'] = today.year - record.dob.year - 1
            else:
                record['age'] = 0

class droga_physiotherapist_list(models.Model):
    _name='droga.physiotherapist.list'
    _rec_name='physiotherapist_name'
    physiotherapist_name = fields.Many2one('hr.employee', string='Physiotherapist Name',required=True)
    branch=fields.Selection([('PT-4 Kilo', '4 kilo branch'), ('PT-Bole', 'Bole branch')])
    branch_w=fields.Many2one('stock.warehouse')
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')], required=True, default='Active')

class droga_pharma_child_list(models.Model):
    _name='droga.pharma.child'
    gender = fields.Selection(
        [('Male', 'Male'), ('Female', 'Female')],
        string='Child gender', tracking=True)
    child_dob= fields.Date('Child dob', default=datetime(2000,1,1),tracking=True)
    child_name=fields.Char('Child name')
    breast_feed_days=fields.Float('Breastfeed period in days',default=180)
    breat_feed_end_date=fields.Date(compute='get_end_date',store=True)

    parent_cust = fields.Many2one('res.partner', string='Parent')
    @api.depends('breast_feed_days','child_dob')
    def get_end_date(self):
        for rec in self:
            rec.breat_feed_end_date= rec.child_dob + timedelta(days=rec.breast_feed_days)
    @api.constrains('child_dob')
    def _is_dob_valid(self):
        for record in self:
            if record.child_dob > datetime.today().date():
                raise ValidationError(
                    "Date of birth should not be greater than current date.")
