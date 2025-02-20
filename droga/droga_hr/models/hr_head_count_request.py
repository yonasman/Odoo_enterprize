from odoo import _, api, fields, models
from datetime import datetime
from odoo.exceptions import ValidationError


class HeadCountRequest(models.Model):
    _name = "hr.head.count.request"
    _order = 'name desc'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']

    def _get_department_id(self):
        # assigning the related employee of the logged in user
        employee_rec = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.department_id

    def _get_employee_id(self):
        # assigning the related employee of the logged in user
        employee_rec = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    def identify_requester(self):
        context = self._context

        if context.get('uid') == self.create_uid.id:
            self.requester = True
        else:
            self.requester = False

    requester = fields.Boolean('Requester', default=False, compute='identify_requester')

    name = fields.Char("Request Number", default='New')
    requesting_department = fields.Many2one("hr.department", required=True, default=_get_department_id)
    request_by = fields.Many2one(
        "hr.employee", string="Requested By", required=True, default=_get_employee_id)
    request_date = fields.Datetime("Date of Request", required=True, default=datetime.today())
    position_type = fields.Selection([("New Position", "New Position"), ("Existing Position", "Existing Position")],
                                     required=True)
    desired_hiring_date = fields.Date("Desired Hiring Date")
    work_location = fields.Char("Work Location", required=True)
    position_title = fields.Char("Proposed Position Title", required=True)
    working_condition = fields.Selection(
        [("Full Time", "Full Time"), ("Part Time", "Part Time"), ("Contract", "Contract")], required=True)
    working_hours = fields.Float("How Many Hours")
    hourly_rate = fields.Float("Hourly Rate")
    contract_start_date = fields.Date("Start Date")
    contract_end_date = fields.Date("End Date")

    supervisor = fields.Many2one("hr.employee", string="Supervisor (Working Directly Under)")
    education_level = fields.Selection(
        [("Below Degree", "Below Degree"), ("Degree", "Degree"), ("Above Degree", "Above Degree")], required=True)
    education_level_desc = fields.Char("Description")
    work_experience = fields.Char("Work Experience")
    recruitment_method = fields.Char("Recommended Source of Recruitment")

    state = fields.Selection([('Draft', 'Draft'), ("Submitted", "Submitted"),
                              ('Approved', 'Approved'), ("CEO", "CEO"), ('Cancelled', 'Cancelled')], default="Draft",
                             tracking=True)

    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 index=True, default=lambda self: self.env.company.id)
    # if the request is approved by department manager check this option
    approve_dept_manger = fields.Boolean("By Department", default=False,
                                         help="The request will be approved by the department manager")
    department_manager = fields.Many2one(
        "hr.employee", compute="_get_manager_id", store=True)

    @api.model
    def create(self, vals):
        # get sequence number for each company
        self_comp = self.with_company(self.company_id)
        vals['name'] = self_comp.env['ir.sequence'].next_by_code(
            'hr.head.count.request') or '/'
        res = super(HeadCountRequest, self_comp).create(vals)

        return res

    def submit_request(self):
        self.write({'state': 'Submitted'})
        # set activity done
        self.set_activity_done()
        # create new activity
        # get budget accountant
        users = self.get_users_for_roles('Human Resource Manager', self.company_id.id)
        for user in users:
            self.create_activity(user)

        self.return_to_tree_view()
        return True

    def approve_request(self):
        self.write({'state': 'Approved'})
        # set activity done
        self.set_activity_done()
        # create new activity
        # get budget accountant
        users = self.get_users_for_roles('CEO', self.company_id.id)
        for user in users:
            self.create_activity(user)

        self.return_to_tree_view()
        return True

    def approve_request_ceo(self):
        self.write({'state': 'CEO'})
        # set activity done
        self.set_activity_done()
        self.return_to_tree_view()
        return True

    def cancel_request(self):
        self.write({'state': 'Cancelled'})
        self.set_activity_done()
        self.return_to_tree_view()
        return True

    def reject_request(self):
        self.write({'state': 'Draft'})
        self.set_activity_done()
        self.return_to_tree_view()
        return True

    def get_users_for_roles(self, role, company_id):
        users = []
        roles = self.env['res.groups'].search([('name', '=', role)])

        for user in roles.users:
            if user.company_id.id == company_id:
                users.append(user.id)
        return users

    @api.depends("requesting_department")
    def _get_manager_id(self):
        for record in self:
            if record.approve_dept_manger:
                record.department_manager = record.department.manager_id
            else:
                record.department_manager = record.request_by.parent_id

    def set_activity_done(self):
        activity = self.env["mail.activity"].search(
            [('res_name', '=', self.name)])
        if activity:
            activity.sudo().action_done()

    def create_activity(self, user_id):
        # create mail activity for the approval
        todos = dict(res_id=self.id,
                     res_model_id=self.env['ir.model'].search([('model', '=', 'hr.head.count.request')]).id,
                     user_id=user_id, summary='Grant Approval', note='You have a request to approve',
                     activity_type_id=4,
                     date_deadline=datetime.now())

        self.env['mail.activity'].sudo().create(todos)

    def return_to_tree_view(self):
        view = self.env.ref('droga_hr.droga_hr_head_count_request_tree_view')
        return {
            'name': _('test'),
            'view_mode': 'tree',
            'view_id': view.id,
            'res_model': 'hr.head.count.request',
            'context': {},
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
