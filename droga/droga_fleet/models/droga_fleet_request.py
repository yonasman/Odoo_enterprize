from math import radians, sin, cos, atan2, sqrt

from odoo import api, fields, models
from datetime import timedelta

from odoo.exceptions import UserError
from odoo.http import request


class FleetRequest(models.Model):
    _name = "droga.fleet.request"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _description = "Droga fleet request"
    _rec_name = 'name'
    name = fields.Char(
        string='Fleet Request No.',default='NEW',
        readonly=True,
    )
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 index=True, default=lambda self: self.env.company.id,readonly=True)
    sale_origin=fields.Many2one('sale.order')

    @api.model
    def create(self, vals_list):
        vals_list['name']=self.env['ir.sequence'].next_by_code('droga.fleet.request')
        return super().create(vals_list)

    visibility = fields.Selection([("visible", "Visible"), ("invisible", "Invisible")],default='invisible')
    cancel_reason = fields.Char(string="Cancel Reason")

    def get_requestor_id(self):
        self.requestor_id = self.env.user.id

    requestor_id = fields.Integer(compute='get_requestor_id', required=True)

    def create_string_array(self,characters):
        string_array = []
        current_string = ""

        for char in characters:
            if char == ",":
                string_array.append(current_string)
                current_string = ""
            else:
                current_string += char

        # Add the last string after the last comma (if any)
        if current_string:
            string_array.append(current_string)

        return string_array










    requested_by = fields.Many2one("res.users", string="Requested by", index=True, default=lambda self: self.env.user,readonly=True)
    date = fields.Datetime("Requested Date", default= fields.Datetime.now(), readonly=True)
    request_type = fields.Selection([ ('employee_transportation', 'Employee Transportation'),  ('resource_transportation', 'Resource Transportation') ], string='Request Type', required=True)
    purpose = fields.Char(string='Purpose')
    company = fields.Many2one('res.company', string='Company',default=lambda self: self.env.company , readonly=True)
    department = fields.Many2one('hr.department', string='Department',default=lambda self: self.env.user.department_id, readonly=True)
    status = fields.Selection( [("draft", "Draft"), ("submitted", "submitted"), ("approved", "Approved"),("queued", "Queued"),("assigned", "Assigned"), ("completed", "Completed"),("cancelled", "Cancelled")], default='draft',tracking=True,required=True)

    def get_delivered_to(self):
        for req in self:
            result = ""
            if req.create_uid == self.env.user.id:

                for partner in req.task_ids:
                        delivered_to = partner.delivered_to
                        name = str(partner.name)
                        if delivered_to != 'False':
                            result = result + str(delivered_to.name) + ","

                req.delivered_to = result
            else:
                req.delivered_to = result

    def get_requested_for(self):
        for req in self:
            result = ""
            if req.requested_by.id == self.env.user.id:

                for task in req.task_ids:
                    if task.requested_for:
                        req_for = str(task.requested_for)
                        if req_for != 'False':
                            result = result + str(req_for) + ","
                    else:
                        del_to = str(task.delivered_to.name)
                        if del_to != 'False':
                            result = result + str(del_to) + ","
                req.requested_for = result
            else:
                req.requested_for = result



    def get_travel_log(self):
        for req in self:
            result = ""
            if req.requested_by.id == self.env.user.id:

                for partner in req.task_ids:
                    from_location = str(partner.from_location)
                    to_location = str(partner.to_location)
                    if (from_location != 'False' or to_location != 'False'):
                        result = result + str(from_location) + " to " + str(to_location) + ","
                req.travel_log = result
            else:
                req.travel_log = result



    def get_vehicle_used(self):
        for req in self:
            result = ""
            if req.requested_by.id == self.env.user.id:

                for partner in req.task_ids:
                    vehicle = str(partner.vehicle.license_plate)
                    if (vehicle != 'False'):
                        result = result + vehicle+ ","
                req.vehicle_used = result
            else:
                req.vehicle_used = result


    def get_resource_name(self):
        for req in self:
            result = ""
            if req.requested_by.id == self.env.user.id:

                for partner in req.task_ids:
                    res_name = str(partner.resource_name)
                    if (res_name != 'False'):
                        result = result + res_name + ","
                req.resource_name = result
            else:
                req.resource_name = result



    def get_amount(self):
        for req in self:
            result = ""
            if req.requested_by.id == self.env.user.id:

                for partner in req.task_ids:
                    amt = str(partner.amount)
                    if (amt != 'False'):
                        result = result + amt + ","
                req.amount = result
            else:
                req.amount = result


    def get_chauffeur(self):
        for req in self:
            result = ""
            if req.requested_by.id == self.env.user.id:

                for partner in req.task_ids:
                    chauffeur = str(partner.chauffeur_drivers.p_name)
                    if (chauffeur != 'False'):
                        result = result + chauffeur+ ","
                req.chauffeur = result
            else:
                req.chauffeur = result




    delivered_to = fields.Char(string='Delivered To', compute='get_delivered_to',required=True)

    requested_for = fields.Char(string='Requested For', compute='get_requested_for', required=True)
    resource_name = fields.Char(string='Resource Transported', compute='get_resource_name',required=True)
    amount = fields.Char(string='Quantity', compute='get_amount',required=True)
    chauffeur = fields.Char(string='Chauffeur', compute='get_chauffeur',required=True)
    vehicle_used = fields.Char(string='Vehicle Used', compute='get_vehicle_used',required=True)
    travel_log = fields.Char(string='Travel Log', compute='get_travel_log',required=True)
    distance_on_delivery = fields.Char('Distance on Delivery', readonly=True, default='Pending')



    # RELATIONS
    task_ids = fields.One2many('droga.fleet.request.task', 'request_id',string='Request Detail',tracking=True)


    def set_activity_done(self):
        activity = self.env["mail.activity"].search(
            [('res_name', '=', self.name)])
        if activity:
            activity.sudo().action_done()

    def get_users_for_roles(self, role, company_id):
        users = []
        roles = self.env['res.groups'].search([('name', '=', role)])

        for user in roles.users:
            if user.company_id.id == company_id:
                users.append(user.id)
        return users

    def create_activity_assign(self, user_id):
        # create mail activity for the approval
        todos = dict(res_id=self.id,
                     res_model_id=self.env['ir.model'].search([('model', '=', 'droga.fleet.request')]).id,
                     user_id=user_id, summary='Assign Driver', note='Assign Driver',
                     activity_type_id=4,
                     date_deadline=fields.datetime.now())

        self.env['mail.activity'].sudo().create(todos)


    def create_activity(self, user_id):
        # create mail activity for the approval
        todos = dict(res_id=self.id,
                     res_model_id=self.env['ir.model'].search([('model', '=', 'droga.fleet.request')]).id,
                     user_id=user_id, summary='Grant Approval', note='Incoming fleet',
                     activity_type_id=4,
                     date_deadline=fields.datetime.now())
        print(str(self.env['ir.model'].search([('model', '=', 'droga.fleet.request')]).id))
        self.env['mail.activity'].sudo().create(todos)
    def create_activity_reverse(self, user_id):
        # create mail activity for the approval
        todos = dict(res_id=self.id,
                     res_model_id=self.env['ir.model'].search([('model', '=', 'droga.fleet.request')]).id,
                     user_id=user_id, summary='Fleet Request Approval', note='Fleet Request Approval',
                     activity_type_id=4,
                     date_deadline=fields.datetime.now())

        self.env['mail.activity'].sudo().create(todos)

    def notify(self, message,user):
        self.env['bus.bus']._sendone(user, "simple_notification", {
            "title": "Fleet Request Status Update.",
            "message": message,
            "sticky": True,
            "warning": True
        })

    def set_to_cancel(self):
        self.status = 'cancelled'





    def sale_order_fleet_request(self):
        if self.task_ids:
            for task in self.task_ids:
                if task.requested_for or task.delivered_to:
                    if self.requested_by == 'resource_transportation':
                        if not (task.resource_name or task.amount):
                            raise UserError('Please fill in The Resource to transport and the Quantity.')
                    if not (task.from_location or task.to_location or task.service_time):
                        raise UserError('Please fill in the required location and time fields.')
                    else:
                        print('act')
                        self.status = 'submitted'
                        users = self.get_users_for_roles('Fleet Manager', self.company_id.id)
                        for user in users:
                            self.create_activity_reverse(user)
                else:
                    raise UserError('Please fill in the Employee requiring transport or the Partner to Deliver to.')
        else:
            raise UserError('No tasks found. Please add tasks to the fleet request.')

    def submit_fleet_request(self):
        if self.task_ids:
            for task in self.task_ids:
                if task.requested_for or task.delivered_to:
                    if self.requested_by == 'resource_transportation':
                        if not (task.resource_name or task.amount):
                            raise UserError('Please fill in The Resource to transport and the Quantity.')
                    if not (task.from_location or task.to_location or task.service_time):
                        raise UserError('Please fill in the required location and time fields.')
                    else:

                        self.status = 'submitted'
                        users = self.get_users_for_roles('Fleet Manager', self.company_id.id)
                        for user in users:
                            print(user)
                            self.create_activity_reverse(user)
                else:
                    raise UserError('Please fill in the Employee requiring transport or the Partner to Deliver to.')
        else:
            raise UserError('No tasks found. Please add tasks to the fleet request.')

    def cancel_submit_request(self):
        self.set_activity_done()
        return {
            'name': 'Cancel Request',
            'view_mode': 'form',
            'res_model': 'cancel.reason.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_users': self.requested_by.id,
                'default_request_num':self.name,
            }

        }


    def accept_request(self):

        self.status = 'approved'


    def reject_request(self):
        self.set_activity_done()
        return {
            'name': 'Cancel Request',
            'view_mode': 'form',
            'res_model': 'cancel.reason.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_users': self.requested_by.id,
                'default_request_num': self.name,
            }

        }

    def create_driver_activity(self, user_id,task):
        # create mail activity for the approval
        todos = dict(res_id=task.id,
                     res_model_id=task.env['ir.model'].search([('model', '=', 'droga.fleet.request.task')]).id,
                     user_id=user_id, summary='Delivery', note='Delivery',
                     activity_type_id=4,
                     date_deadline=fields.datetime.now())
        print(str(self.env['ir.model'].search([('model', '=', 'droga.fleet.request')]).id))
        self.env['mail.activity'].sudo().create(todos)


    def driver_assigned(self):
        for task in self.task_ids:
            if not (task.chauffeur or task.vehicle):
                raise UserError('Please fill in all the fields in the form.')
            else:
                #ADD TASK FOR THE VEHICLE
                plate = task.vehicle.license_plate
                vehicle_status = self.env['fleet.vehicle'].search([('license_plate', '=' , plate)])
                vehicle_status.add_task([task.id])

                #ADD TASK FOR THE DRIVER
                employee = task.chauffeur
                user = self.env['res.users'].search([('name', 'like', 'Driver%')])

                self.create_driver_activity(user.id, task)
                self.status = 'assigned'

                message = "Fleet Request Has been assigned accepted successfully."
                self.notify(message, self.create_uid)

    def driver_assigned_queue(self):
        for task in self.task_ids:
            if not (task.chauffeur or task.vehicle):
                raise UserError('Please fill in all the fields in the form.')
            else:
                # ADD TASK FOR THE VEHICLE
                plate = task.vehicle.license_plate
                vehicle_status = self.env['fleet.vehicle'].search([('license_plate', '=', plate)])
                vehicle_status.add_task([task.id])

                # ADD TASK FOR THE DRIVER
                employee = task.chauffeur
                user = self.env['res.users'].search([('id', '=', employee.user_id.id)])

                self.create_driver_activity(user.id, task)
                self.status = 'assigned'

                message = "Fleet Request Has been assigned accepted successfully."
                self.notify(message, self.create_uid)

    def reject_driver_queue(self):
        self.set_activity_done()
        return {
            'name': 'Cancel Request',
            'view_mode': 'form',
            'res_model': 'cancel.reason.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_users': self.requested_by.id,
                'default_request_num': self.name,
            }

        }

    def reject_driver(self):
        self.set_activity_done()
        return {
            'name': 'Cancel Request',
            'view_mode': 'form',
            'res_model': 'cancel.reason.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_users': self.requested_by.id,
                'default_request_num': self.name,
            }

        }



    def await_driver(self):
        self.status='queued'
        self.notify("Waiting For Driver To Be Assigned", self.create_uid)

    def completed(self):
        self.set_activity_done()
        self.status = 'completed'
        message = "Your fleet Request has been successfully completed."
        self.notify(message, self.create_uid)


    def delete_record(self):
            self.unlink()

    @api.onchange('task_ids.is_delivered')
    def check_delivered(self):
        count = 0
        for task in self.task_ids:
            count = count + 1

        check_count = 0
        for check in self.task_ids:
            if check.is_delivered == True:
                check_count = check_count + 1
        print(count)
        print(check_count)
        if count == check_count:
            self.completed()













class RequestTasks(models.Model):
    _name = "droga.fleet.request.task"
    _description = "Droga fleet request task"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _rec_name = 'travel_log'
    task_stage = fields.Selection([("start", "Start"), ("delivered", "Delivered")], default='start')
    start_time = fields.Datetime('start time')

    time_taken = fields.Char('Time Taken')

    def start(self):
        for task in self:
            current_time = fields.datetime.now()
            task.start_time = current_time
            task.task_stage = 'delivered'

    fleet_request_id = fields.Many2one('droga.fleet.request', string="Fleet Request")
    vehicle_id = fields.Many2one('fleet.vehicle')
    is_delivered=fields.Boolean('Delivered',default=False)
    active_status = fields.Boolean(default=True,string="Active Status" )
    travel_log = fields.Char(string='Travel Log', compute='get_travel_log',required=True)


    name = fields.Char(
        string='Fleet Request No.',
        required=True,
    )




    def set_activity_done(self):
        activity = self.env["mail.activity"].search(
            [('res_id', '=', self.id)])
        activities = self.env["mail.activity"].browse()
        for acr in activities:
            print(acr)
        if activity:
            activity.sudo().action_done()
        else:
            print("no activity")


    def delivered(self):
        for task in self:
                current_time = fields.datetime.now()
                time_difference = current_time - task.start_time
                task.time_taken = time_difference

                print("In task")
                task.is_delivered = True

                print("In task")
                task.vehicle_id.tasks -= task
                id = task.id
                task.vehicle.remove_task([id])
                print(task.vehicle_id)
                print(task.vehicle)
                if all(t.is_delivered for t in task.vehicle_id.tasks):
                    task.vehicle_id.set_true()

                task.active_status = False
                task.is_delivered = True
                task.request_id.check_delivered()
                task.set_activity_done()


    def get_travel_log(self):
        for req in self:
            result = ""
            for partner in req:
                    from_location = str(partner.from_location)
                    to_location = str(partner.to_location)
                    if (from_location != 'False' or to_location != 'False'):
                        result = result + str(from_location) + " to " + str(to_location) + ","
                        req.travel_log = result
                    else:
                        req.travel_log = result


    requested_for = fields.Many2one('hr.employee',
                                    string='Requested For',
                                   tracking=True)

    delivered_to = fields.Many2one('res.partner', String='Deliver To',tracking=True)
    resource_name = fields.Char(String='Resource to be Transported',tracking=True)
    amount = fields.Integer(String='Quantity',tracking=True)
    deliver_to = fields.Many2one('res.partner', string='Deliver To',tracking=True)



    #COMMON
    comment = fields.Text("Comment")
    service_time = fields.Datetime("Time For Service",tracking=True)
    from_location = fields.Char(string='From Location',tracking=True)
    to_location = fields.Char(string='To Location',tracking=True)



    vehicle = fields.Many2one('fleet.vehicle', string='Assign Vehicle')


    #EMPLOYEE

    chauffeur = fields.Many2one("hr.employee", string=" Driver (If Needed)")
    chauffeur_drivers=fields.Many2one('droga.pro.sales.master',string=" Driver (If Needed)",domain="[('employee_access_users', 'like', 'Driver%')]")
    def _get_pr_sales_logged(self):
        if not request:
            return False
        ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
        return False if len(ses) == 0 else ses[0].pro_id.ids[0]


    pr_sales_logged = fields.Many2one('droga.pro.sales.master', string="Driver ID log", store=False,
                                      default=_get_pr_sales_logged)

    is_record_owner = fields.Boolean('Show lead', store=False, compute="_is_record_owner", search="_search_field")

    @api.depends('pr_sales_logged')
    def _is_record_owner(self):
        for rec in self:
            if rec.chauffeur_drivers == rec.pr_sales_logged:
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
                is_rec_owner = self.env['droga.fleet.request.task'].sudo().search([('chauffeur_drivers', '=', ses[0].pro_id.ids[0])])
                # is_rec_inside_self=self.sudo().search([]).filtered(lambda x: x.pr_sales == ses[0].pro_id)
                return [('id', 'in', [x.id for x in is_rec_owner] if is_rec_owner else False)]
        else:
            return [('id', 'in', [])]

    request_id = fields.Many2one('droga.fleet.request')

    status = fields.Selection(
        [("draft", "Draft"), ("submitted", "Submitted"), ("approved", "Approved"), ("assigned", "Assigned"),
         ("completed", "Completed"), ("canceled", "Canceled")], default='draft', tracking=True,
        related='fleet_request_id.status')

    request_type = fields.Selection([
        ('employee_transportation', 'Employee Transportation'),
        ('resource_transportation', 'Resource Transportation')
    ], string='Request Type', required=True, related='request_id.request_type')


class CancelReasonWizard(models.TransientModel):
    _name = 'cancel.reason.wizard'


    rejection_reason = fields.Many2one('fleet.request.rejection.reason.header',
                             string="Rejection Reason")
    fleet_request = fields.Many2one('droga.fleet.request', string="Fleet Request")

    users = fields.Integer(string='User to Notify')
    request_num = fields.Char(string='Request Number')

    def notify(self, message,user):
        self.env['bus.bus']._sendone(user, "simple_notification", {
            "title": "Fleet Request Status Update.",
            "message": message,
            "sticky": True,
            "warning": True
        })
        print('notify')

    def confirm_cancel(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            request = self.env['droga.fleet.request'].browse(active_id)
            request.cancel_reason = self.rejection_reason.name
        self.notify(self.rejection_reason.name, self.users)

        req = self.env['droga.fleet.request'].search([('name', '=', self.request_num)])
        req.set_to_cancel()
        return {'type': 'ir.actions.act_window_close'}

    def cancel(self):
        self.notify(self.rejection_reason.name ,self.users)
        return {'type': 'ir.actions.act_window_close'}

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    driver_license_type = fields.Selection([
        ('type_a', 'Automobile'),
        ('type_b', 'Hizb 1'),
        ('type_c', 'Derek 1'),
        ('type_d', 'Motor Cycle'),

    ], string='Driver License Type')


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'
    driver_license_type=fields.Selection([
        ('type_a', 'Automobile'),
        ('type_b', 'Hizb 1'),
        ('type_c', 'Derek 1'),
        ('type_d', 'Motor Cycle'),

    ], string='Driver License Type')







