from datetime import datetime, timedelta
from math import radians, sin, cos, atan2, sqrt

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.http import request


class cust_contact_extension(models.Model):
    _inherit = 'res.partner'

    name = fields.Char(index=True, default_export_compatible=True, tracking=True)
    display_name = fields.Char(compute='_compute_display_name', recursive=True, store=True, index=True, tracking=True)
    company_type = fields.Selection(string='Company Type',
                                    selection=[('company', 'Company'), ('person', 'Individual')], default='company')
    cust_grade = fields.Many2one('droga.cust.grade', string='Customer grade')
    cust_type_ext = fields.Many2one('droga.cust.type', string='Customer type', tracking=True)
    contact_tobe_accessed_by = fields.Selection(
        [('Promotors', 'Promotors'), ('Sales reps', 'Sales reps'), ('Both', 'Both')], string='Contact used by')
    type = fields.Selection(
        [('contact', 'Contact'),
         ('invoice', 'Invoice Address'),
         ('delivery', 'Delivery Address'),
         ('private', 'Private Address'),
         ('other', 'Other Address'),
         ], string='Address Type',
        default='contact',
        help="- Contact: Use this to organize the contact details of employees of a given company (e.g. CEO, CFO, ...).\n"
             "- Invoice Address : Preferred address for all invoices. Selected by default when you invoice an order that belongs to this company.\n"
             "- Delivery Address : Preferred address for all deliveries. Selected by default when you deliver an order that belongs to this company.\n"
             "- Private: Private addresses are only visible by authorized users and contain sensitive data (employee home addresses, ...).\n"
             "- Other: Other address for the company (e.g. subsidiary, ...)")
    # region = fields.Many2one('droga.crm.settings.region')
    # city_custom = fields.Many2one('droga.crm.settings.city')
    city_name = fields.Many2one('droga.crm.settings.city', tracking=True)
    area = fields.Many2one('droga.crm.settings.area')
    location = fields.Char('Location')
    contacts = fields.One2many('droga.crm.contacts', 'parent_customer')
    street = fields.Char(compute='_get_add')
    key_account = fields.Boolean('Key account')
    x_exclude_maturity_for_reconciliation = fields.Boolean('Temporarly exclude maturity for reconciliation',tracking=True)
    partner_latitude = fields.Float(string='Geo Latitude', digits=(10, 7), tracking=True)
    partner_longitude = fields.Float(string='Geo Longitude', digits=(10, 7), tracking=True)
    loc_history = fields.One2many('droga.crm.loc.history', 'partner')
    loc_set=fields.Boolean('Location set',default=False,compute='_is_loc_set',store=True)
    mature_individually = fields.Boolean('Mature individually', default=False)

    @api.depends('partner_latitude','partner_longitude')
    def _is_loc_set(self):
        for rec in self:
            if rec.partner_latitude!=0 or rec.partner_longitude!=0:
                rec.loc_set=True
            else:
                rec.loc_set = False

    # lati_custom =fields.Float('Geo Latitude',digits=(10,7))
    # long_custom = fields.Float('Geo Longtude',digits=(10,7))

    @api.model
    def update_latitude_longitude(self, partners):
        pass

    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company, index=True)

    def _def_rec(self):
        cid = self.env.company.id
        acc = self.env['account.account'].search([('company_id', '=', cid), ('code', '=', '114001')])
        return acc[0].id if len(acc) > 0 else False

    property_account_receivable_id = fields.Many2one('account.account', company_dependent=True,
                                                     string="Account Receivable",
                                                     domain="[('account_type', '=', 'asset_receivable'), ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
                                                     help="This account will be used instead of the default one as the receivable account for the current partner",
                                                     required=True, default=_def_rec)

    def _def_pay(self):
        cid = self.env.company.id
        acc = self.env['account.account'].search([('company_id', '=', cid), ('code', '=', '211001')])
        return acc[0].id if len(acc) > 0 else False

    property_account_payable_id = fields.Many2one('account.account', company_dependent=True,
                                                  string="Account Payable",
                                                  domain="[('account_type', '=', 'liability_payable'), ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
                                                  help="This account will be used instead of the default one as the payable account for the current partner",
                                                  required=True, default=_def_pay)

    def write(self, vals):
        for rec in self:
            if 'vat' in vals and rec.vat and not self.env.user.has_group('droga_crm.tin_admin'):
                raise UserError("You can not edit Tin no.")
            if 'name' in vals and rec.vat and not self.env.user.has_group('droga_crm.tin_admin'):
                raise UserError("You can not edit name.")
        return super(cust_contact_extension, self).write(vals)

    def update_current_locations(self, res_id, latitude, longitude):
        for res in self.env['res.partner'].search([('id', '=', res_id)]):
            # res.lati_custom=float(latitude)

            if not self.env.user.has_group('droga_crm.crm_cust_loc'):
                pass

            if len(self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])) > 0:
                logged_user = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])[
                    0].pro_id.p_name
            else:
                logged_user = self.env.user.name

            loc_vals = {
                'update_user_loc': logged_user,
                'partner': res.id,
                'old_lati': res.partner_latitude,
                'new_lati': float(latitude),
                'old_long': res.partner_longitude,
                'new_long': float(longitude)
            }

            self.env['droga.crm.loc.history'].sudo().create(loc_vals)
            res.partner_longitude = float(longitude)
            res.partner_latitude = float(latitude)

    @api.model
    def create(self, vals):
        if 'supplier_rank' in vals and 'vat' in vals:
            if not self.env.user.has_group('droga_crm.crm_cust_create') and vals['supplier_rank'] == 0:
                raise UserError("You don't have access to create a customer.")
            # if vals['supplier_rank'] == 0:
            # if len(vals['vat']) == 0:
            # raise UserError("Please enter Tin no. It is mandatory")
            if vals['supplier_rank'] == 0 and vals['vat']:
                if (len(vals['vat']) < 10 or len(vals['vat']) > 14) and vals['company_id']==1:
                    raise UserError("Length of Tin no should either be 10 or 13, please amend accordingly.")
        return super(cust_contact_extension, self).create(vals)

    @api.depends('location', 'area')
    def _get_add(self):
        for rec in self:
            rec.street = ((rec.area.area_name + ' - ') if rec.area else '') + rec.location if rec.location else ''

    def _get_pr_sales_logged(self):
        if not request:
            return False
        ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
        return False if len(ses) == 0 else ses[0].pro_id.ids[0]

    pr_sales_logged = fields.Many2one('droga.pro.sales.master', string="Promotor ID log", store=False,
                                      default=_get_pr_sales_logged)

    def _get_areas(self):
        if self.env.user.has_group('droga_crm.crm_cust'):
            return self.env['droga.crm.settings.city'].search([(1, '=', 1)]).ids
        else:
            ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
            return False if len(ses) == 0 else ses[0].pro_id[0].p_regions.ids
            # return self.pr_sales_logged.p_regions

    pr_avail_area = fields.Many2many('droga.crm.settings.city', default=_get_areas)


    def _is_cust_loc_avail(self):
        if not self.env.user.name.upper().startswith('CRM') and self.env.user.has_group('droga_crm.crm_cust'):
            for rec in self:
                rec.is_cust_available = True
        else:
            for rec in self:
                if rec.city_name in rec.pr_avail_areas:
                    rec.is_cust_available = True
                else:
                    rec.is_cust_available = False

    is_cust_available = fields.Boolean('Show cust', store=False, compute="_is_cust_loc_avail",
                                       search="_search_cust_avail")

    def _search_cust_avail(self, operator, value):
        if not self.env.user.name.upper().startswith('CRM') and self.env.user.has_group('droga_crm.crm_cust'):
            return [('id', 'in', [x.id for x in self.env['res.partner'].search([(1, '=', 1)])])]
        ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
        if not request or len(ses) == 0:
            return [('id', 'in', [])]
        is_cust_avail = self.env['res.partner'].sudo().search(
            [('city_name', 'in', ses[0].pro_id[0].p_regions.ids)])
        return [('id', 'in', [x.id for x in is_cust_avail] if is_cust_avail else False)]

    # this method updated customer category in account.move model if the customer category changed
    def update_customer_category_on_account_move(self, recs):
        for record in recs:
            # search account.move
            account_moves = self.env['account.move'].search(
                [('move_type', '=', 'out_invoice'), ('partner_id', '=', record.id)])

            for account_move in account_moves:
                # update customer category type
                self.env.cr.execute(
                    """ update account_move set customer_category=%s where id=%s""",
                    (record.cust_type_ext.cust_org_type, account_move.id))


class cust_history(models.Model):
    _name = 'droga.crm.loc.history'
    update_user_loc = fields.Char('Update user')
    partner = fields.Many2one('res.partner')
    update_date = fields.Datetime('Update date', default=fields.Datetime.now)
    old_lati = fields.Float(string='Old Latitude', digits=(10, 7))
    new_lati = fields.Float(string='New Latitude', digits=(10, 7))
    old_long = fields.Float(string='Old Longitude', digits=(10, 7))
    new_long = fields.Float(string='New Longitude', digits=(10, 7))


class account_move_pr_sales(models.Model):
    _inherit = "account.move"
    cust_location = fields.Many2one('droga.crm.settings.city', related='partner_id.city_name')
    cust_region = fields.Many2one('droga.crm.settings.region', related='partner_id.city_name.parent_id')
    is_cust_available = fields.Boolean(related='partner_id.is_cust_available')

    def _get_pr_sales_logged(self):
        sale = self.env['sale.order'].search([('name', '=', self.invoice_origin)])
        return False if len(sale) == 0 else sale[0].pr_sales

    pr_sales = fields.Many2one('droga.pro.sales.master', readonly=True, store=True, string="Promotor ID",
                               default=_get_pr_sales_logged)


class sales_team_extension(models.Model):
    _inherit = 'crm.team'
    _rec_name = 'city_name'
    city_name = fields.Many2one('droga.crm.settings.city')


class crm_lead_extension(models.Model):
    _inherit = 'crm.lead'

    plan_id = fields.Many2one('droga.customer.visit.detail')
    contacts_schedule_single = fields.Many2one('droga.crm.contacts.schedule')
    ordered_prods = fields.One2many('droga.lead.ordered.products', 'leads')
    follow_up_visits = fields.One2many('crm.lead', 'leads')
    leads = fields.Many2one('crm.lead')
    contact_custom = fields.Many2one('droga.crm.contacts', domain="[('parent_customer','=',partner_id)]")
    city_name = fields.Many2one('droga.crm.settings.city', related='partner_id.city_name')
    core_products = fields.Many2many('product.template', domain=[('is_core_product', '=', 'true')])
    closed_sales = fields.Boolean('Sales is closed')
    # co_travel_crm = fields.Many2many('hr.employee', string='Co-travelers')
    co_travel_crm = fields.Many2many('droga.pro.sales.master', string='Co-travelers')
    date_planned = fields.Datetime('Lead date', default=fields.Date.today())
    origin_user_id = fields.Many2one('res.users')
    is_from_plan=fields.Boolean(Default=False,string='From plan')

    planned_visit_selection = fields.Selection([
        ('Early Morning', 'Early Morning'),
        ('Late Morning', 'Late Morning'),
        ('Lunch', 'Lunch'),
        ('Early Afternoon', 'Early Afternoon'),
        ('Late Afternoon', 'Late Afternoon'),
    ], string='Visit session', default="Early Morning")
    specialty = fields.Many2one('droga.cust.specialty', string='Specialty', related='contact_custom.specialty')
    phone = fields.Char(
        'Phone', tracking=50,
        compute='_compute_phone', inverse='_inverse_phone', readonly=False, store=True)

    check_in_lati = fields.Float('Geo Latitude', digits=(10, 7))
    check_in_long = fields.Float('Geo Longtude', digits=(10, 7))
    check_in_distance_meters = fields.Integer('Check in distance in meters', tracking=True)
    check_in_time_and_date = fields.Datetime('Check in date and time')
    check_in_descr = fields.Char('Check in')

    check_out_lati = fields.Float('Geo Latitude', digits=(10, 7))
    check_out_long = fields.Float('Geo Longtude', digits=(10, 7))
    check_out_distance_meters = fields.Integer('Check out distance in meters', tracking=True)
    check_out_time_and_date = fields.Datetime('Check out date and time')
    check_out_descr = fields.Char('Check out')

    visit_status = fields.Char('Visit status')

    referral_distri = fields.Many2many('res.partner', string='Referral to distributor')

    def update_check_in_locations(self, res_id, lati, long):
        for res in self.env['crm.lead'].search([('id', '=', res_id)]):
            # res.lati_custom=float(latitude)
            if res.check_in_lati == 0:
                res.check_in_lati = float(lati)
                res.check_in_long = float(long)
                dist = self.calculate_distance(float(lati), float(long), res.partner_id.partner_latitude,
                                               res.partner_id.partner_longitude)
                res.check_in_distance_meters = int(dist)
                res.check_in_time_and_date = datetime.now()
                res.check_in_descr = (res.check_in_time_and_date + timedelta(hours=3)).strftime(
                    "%d %b, %H:%M") + ' (' + f"{int(dist):,}" + ' m)'


    def update_check_out_locations(self, res_id, lati, long):
        for res in self.env['crm.lead'].search([('id', '=', res_id)]):
            if res.check_out_lati == 0:
                res.check_out_lati = float(lati)
                res.check_out_long = float(long)
                dist = self.calculate_distance(float(lati), float(long), res.partner_id.partner_latitude,
                                               res.partner_id.partner_longitude)
                res.check_out_distance_meters = int(dist)
                res.check_out_time_and_date = datetime.now()
                res.check_out_descr = (res.check_out_time_and_date + timedelta(hours=3)).strftime(
                    "%d %b, %H:%M") + ' (' + f"{int(dist):,}" + ' m)'

    def calculate_distance(self, lat1, lon1, lat2, lon2):

        lat1 = radians(lat1)
        lon1 = radians(lon1)
        lat2 = radians(lat2)
        lon2 = radians(lon2)

        R = 6371000

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c

        return distance

    def _get_pr_sales_logged(self):
        if not request:
            return False
        ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
        return False if len(ses) == 0 else ses[0].pro_id.ids[0]

    pr_sales = fields.Many2one('droga.pro.sales.master', readonly=True, store=True, string="Promotor ID",
                               default=_get_pr_sales_logged, required=True, tracking=True)
    pr_lead = fields.Many2one('droga.pro.sales.master', default=_get_pr_sales_logged)
    pr_sales_logged = fields.Many2one('droga.pro.sales.master', string="Promotor ID log", store=False,
                                      default=_get_pr_sales_logged)

    def _get_areas(self):
        if self.env.user.has_group('droga_crm.crm_cust'):
            return self.env['droga.crm.settings.city'].search([(1, '=', 1)]).ids
        else:
            ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
            return False if len(ses) == 0 else ses[0].pro_id[0].p_regions.ids

    pr_avail_areas = fields.Many2many('droga.crm.settings.city', default=_get_areas)
    partner_id = fields.Many2one(
        'res.partner', string='Customer', check_company=True, index=True, tracking=10,
        domain="['&',('city_name', 'in',pr_avail_areas),'|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference.")
    is_record_owner = fields.Boolean('Show lead', store=False, compute="_is_record_owner", search="_search_field")

    @api.depends('pr_sales_logged')
    def _is_record_owner(self):
        for rec in self:
            if rec.pr_sales == rec.pr_sales_logged:
                rec.is_record_owner = True
            else:
                rec.is_record_owner = False

    def _search_field(self, operator, value):
        if operator == '=':
            if not request:
                return [('id', 'in', [])]
            ses = self.env['droga.pro.sales.master.visit'].sudo().search([('s_id', '=', request.session.sid)])
            if len(ses) == 0:
                return [('id', 'in', [])]
            else:
                is_rec_owner = self.env['crm.lead'].sudo().search([('pr_sales', '=', ses[0].pro_id.ids[0])])
                # is_rec_inside_self=self.sudo().search([]).filtered(lambda x: x.pr_sales == ses[0].pro_id)
                return [('id', 'in', [x.id for x in is_rec_owner] if is_rec_owner else False)]
        else:
            return [('id', 'in', [])]

    def _convert_opportunity_data(self, customer, team_id=False):
        upd_values = {
            'type': 'opportunity',
            'date_open': self.env.cr.now(),
            'date_conversion': self.env.cr.now(),
        }
        if customer != self.partner_id:
            upd_values['partner_id'] = customer.id if customer else False

        if self.closed_sales:
            upd_values['stage_id'] = self.env['crm.stage'].search([('is_won', '=', True)])[0].id
        else:
            new_team_id = team_id if team_id else self.team_id.id
            stage = self._stage_find(team_id=new_team_id)
            upd_values['stage_id'] = stage.id
        return upd_values

    @api.depends('contact_custom.mobile')
    def _compute_phone(self):
        for lead in self:
            if lead.contact_custom.mobile and not lead.phone:
                lead.phone = lead.contact_custom.mobile

    def _inverse_phone(self):
        for lead in self:
            lead.contact_custom.mobile = lead.phone

    def unlink(self):
        raise UserError("You can not delete the record. Please mark it as lost instead.")

    @api.model
    def create(self, vals):

        if 'leads' in vals:
            lead = self.env['crm.lead'].search([('id', '=', vals['leads'])])
            lead_vals = {
                'name': lead.name.replace(" - Follow up", "").replace("opportunity's", "").replace("opportunity",
                                                                                                   "") + ' - Follow up',
                'pr_sales': lead.pr_sales.id,
                'pr_lead': lead.pr_sales.id,
                'origin_user_id': lead.user_id.id,
                'user_id': lead.user_id.id,
                'company_id': self.env.company.id,
                'type': 'lead',
                'stage_id': 1,
                'expected_revenue': 0,
                'partner_id': lead.partner_id.id,
                'planned_visit_selection': lead.planned_visit_selection,
                'leads': vals['leads'],
                'date_planned': vals['date_planned']
                # 'contact_name': det['visit_contact'].name,
            }

            return super(crm_lead_extension, self).create(lead_vals)
        else:
            vals.update({'name': vals['name'].replace("opportunity", "") + "lead"})
            return super(crm_lead_extension, self).create(vals)


class crm_prod_template_extension(models.Model):
    _inherit = 'product.template'
    crm_group = fields.Many2one('droga.crm.settings.prod_group', string='CRM Group')
