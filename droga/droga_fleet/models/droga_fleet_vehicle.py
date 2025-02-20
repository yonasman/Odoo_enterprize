from odoo import api, models, fields
from datetime import timedelta


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'
    _rec_name = 'license_plate'

    vehicle_status = fields.Selection(selection=[("rented", "Rented"), ("owned", "Owned")])
    maintenance_status = fields.Selection(selection=[("in_maintenance", "In Maintenance"),
                                                     ("maintenance_completed", "Available For Use")],
                                          default="maintenance_completed")


    four_wheels = fields.Boolean("All 4 wheels")
    mud_flaps = fields.Boolean("Mud Flaps")
    spare_tire = fields.Boolean("Spare Tire")
    radio_tape = fields.Boolean("Radio/Tape")
    wheel_screw = fields.Boolean("Wheel Screw")
    molded_carpet = fields.Boolean("Molded carpet")
    car_jack = fields.Boolean("Car Jack")
    side_mirror = fields.Boolean("Side view mirror")
    antenna = fields.Boolean("Antenna")
    car_type = fields.Char("Car Type")
    plate_number = fields.Char("Plate Number")
    fuel_amount = fields.Char("Fuel amount")
    rent_type = fields.Char("Rent Type")
    with_driver = fields.Boolean("Rented with driver")
    return_place = fields.Char("Return Place")
    rent_fee = fields.Float("Rent fee per day")
    cc = fields.Float("CC")
    additional_info = fields.Text("Additional info")
    bolo_renewal_date = fields.Date("Bolo renewal date")
    bolo_due_date = fields.Date("Bolo Due date")
    insurance_renewal_date = fields.Date("Insurance renewal date")
    insurance_due_date = fields.Date("Insurance Due date")

    available = fields.Boolean("Available", Tracking=True)
    tasks = fields.Many2many('droga.fleet.request.task', 'vehicle_id',string="Current Tasks")


    service_details = fields.One2many('service.date', 'header')
    contract_details = fields.One2many('contract.date', 'header')



    def add_to_maintenance(self):
        self.maintenance_status = "in_maintenance"
        self.available = False

    def remove_from_maintenance(self):
        self.maintenance_status = "maintenance_completed"
        self.available = True

    def set_false(self):
        self.available = False
    def set_true(self):
        self.available=True

    def add_task(self, task_ids):
        print("task : " + str(task_ids))
        self.write({
            'tasks': [(4, task_id) for task_id in task_ids]
        })
        self.set_false()

    def remove_task(self, task_ids):
        print("task : " + str(task_ids) )
        self.write({
            'tasks': [(3, task_id,0) for task_id in task_ids]
        })
        if not self.tasks:
            self.set_true()

    @api.depends('tasks.is_delivered')
    def _compute_availability(self):
        for vehicle in self:
            if all(task.is_delivered for task in vehicle.tasks):
                vehicle.set_true()
            else:
                vehicle.available = False


    def get_users_for_roles(self, role, company_id):
        users = []
        roles = self.env['res.groups'].search([('name', '=', role)])

        for user in roles.users:
            if user.company_id.id == company_id:
                users.append(user.id)
        return users

    def notify(self, message):
        self.env['bus.bus']._sendone(self.env.user.partner_id, "simple_notification", {
            "title": "Reminder for due date",
            "message": message,
            "sticky": True,
            "warning": True
        })

    def activity_fleet_man(self, message, vehicle):
        users = self.get_users_for_roles('Fleet Manager', self.company_id.id)
        for user in users:
            self.env['mail.activity'].sudo().create({
                'res_model_id': self.env.ref('fleet.model_fleet_vehicle').id,
                'res_name': message,
                'res_id': vehicle.id,
                'automated': True,
                'user_id': user.id,
                'activity_type_id': 4,
                'summary': message,
                'note': vehicle['license_plate']
            })

    def activity_gen_man(self, message, vehicle):
        users = self.get_users_for_roles('General Service Manager', self.company_id.id)
        for user in users:
            self.env['mail.activity'].sudo().create({
                'res_model_id': self.env.ref('fleet.model_fleet_vehicle').id,
                'res_name': message,
                'res_id': vehicle.id,
                'automated': True,
                'user_id': user.id,
                'activity_type_id': 4,
                'summary': message,
                'note': vehicle['license_plate']
            })

    def activity_hr_man(self, message, vehicle):
        users = self.get_users_for_roles('HR Manager', self.company_id.id)
        for user in users:
            self.env['mail.activity'].sudo().create({
                'res_model_id': self.env.ref('fleet.model_fleet_vehicle').id,
                'res_name': message,
                'res_id': vehicle.id,
                'automated': True,
                'user_id': user.id,
                'activity_type_id': 4,
                'summary': message,
                'note': vehicle['license_plate']
            })

    def send_insurance_reminder(self):
        today = fields.Date.today()
        one_month_from_now = today + timedelta(days=30)
        two_weeks_from_now = today + timedelta(days=15)
        one_week_from_now = today + timedelta(days=7)
        three_days_from_now = today + timedelta(days=3)

        vehicles_insurance_one_month = self.search([('insurance_due_date', '=', one_month_from_now)])
        vehicles_insurance_two_weeks = self.search([('insurance_due_date', '=', two_weeks_from_now)])
        vehicles_insurance_one_week = self.search([('insurance_due_date', '=', one_week_from_now)])
        vehicles_insurance_three_days = self.search([('insurance_due_date', '=', three_days_from_now)])
        vehicles_service_one_week = self.search([('service_due_date', '=', one_week_from_now)])
        vehicles_service_three_days = self.search([('service_due_date', '=', three_days_from_now)])
        vehicles_bolo_one_month = self.search([('bolo_due_date', '=', one_month_from_now)])
        vehicles_bolo_two_weeks = self.search([('bolo_due_date', '=', two_weeks_from_now)])
        vehicles_bolo_one_week = self.search([('bolo_due_date', '=', one_week_from_now)])
        vehicles_bolo_three_days = self.search([('bolo_due_date', '=', three_days_from_now)])
        vehicles_contract_one_month = self.search([('contract_due_date', '=', one_month_from_now)])
        vehicles_contract_two_weeks = self.search([('contract_due_date', '=', two_weeks_from_now)])
        vehicles_contract_one_week = self.search([('contract_due_date', '=', one_week_from_now)])
        vehicles_contract_three_days = self.search([('contract_due_date', '=', three_days_from_now)])

        for vehicle in vehicles_insurance_one_month:
            message = "The due date for insurance of the vehicle with license plate " + vehicle.license_plate + " is only a month away!"
            self.notify(message)
            self.activity_fleet_man(message, vehicle)
        for vehicle in vehicles_insurance_two_weeks:
            message = "The due date for insurance of the vehicle with license plate " + vehicle.license_plate + " is only 15 days away!"
            self.notify(message)
            self.activity_fleet_man(message, vehicle)
        for vehicle in vehicles_insurance_one_week:
            message = "The due date for insurance of the vehicle with license plate " + vehicle.license_plate + " is only 7 days away!"
            self.notify(message)
            self.activity_gen_man(message, vehicle)
        for vehicle in vehicles_insurance_three_days:
            message = "The due date for insurance of the vehicle with license plate " + vehicle.license_plate + " is only 3 days away!"
            self.notify(message)
            self.activity_hr_man(message, vehicle)
        for vehicle in vehicles_service_one_week:
            message = "The due date for service of the vehicle with license plate " + vehicle.license_plate + " is only 7 days away!"
            self.notify(message)
            self.activity_fleet_man(message, vehicle)
        for vehicle in vehicles_service_three_days:
            message = "The due date for service of the vehicle with license plate " + vehicle.license_plate + " is only 3 days away!"
            self.notify(message)
            self.activity_gen_man(message, vehicle)
        for vehicle in vehicles_bolo_one_month:
            message = "The due date for bolo of the vehicle with license plate " + vehicle.license_plate + " is only a month away!"
            self.notify(message)
            self.activity_fleet_man(message, vehicle)
        for vehicle in vehicles_bolo_two_weeks:
            message = "The due date for bolo of the vehicle with license plate " + vehicle.license_plate + " is only 15 days away!"
            self.notify(message)
            self.activity_fleet_man(message, vehicle)
        for vehicle in vehicles_bolo_one_week:
            message = "The due date for bolo of the vehicle with license plate " + vehicle.license_plate + " is only 7 days away!"
            self.notify(message)
            self.activity_gen_man(message, vehicle)
        for vehicle in vehicles_bolo_three_days:
            message = "The due date for bolo of the vehicle with license plate " + vehicle.license_plate + " is only 3 days away!"
            self.notify(message)
            self.activity_hr_man(message, vehicle)
        for vehicle in vehicles_contract_one_month:
            message = "The due date for contract of the vehicle with license plate " + vehicle.license_plate + " is only a month away!"
            self.notify(message)
            self.activity_fleet_man(message, vehicle)
        for vehicle in vehicles_contract_two_weeks:
            message = "The due date for contract of the vehicle with license plate " + vehicle.license_plate + " is only 15 days away!"
            self.notify(message)
            self.activity_fleet_man(message, vehicle)
        for vehicle in vehicles_contract_one_week:
            message = "The due date for contract of the vehicle with license plate " + vehicle.license_plate + " is only 7 days away!"
            self.notify(message)
            self.activity_gen_man(message, vehicle)
        for vehicle in vehicles_contract_three_days:
            message = "The due date for contract of the vehicle with license plate " + vehicle.license_plate + " is only 3 days away!"
            self.notify(message)
            self.activity_hr_man(message, vehicle)




    maintenance_fees = fields.One2many('vehicle.maintenance.fee',
                                       'vehicle_id', string='Maintenance Fees')

    fuel_consumption_per_use = fields.One2many('vehicle.maintenance.fee','vehicle_id',string='Fuel Consumption per Use')
    fuel_consumption_per_quota = fields.Float(string='Fuel Consumption per Quota',default=0)

    rent_fee = fields.Float(string='Rent Fee', default=0)



class VehicleMaintenanceFee(models.Model):
    _name = 'vehicle.maintenance.fee'
    _description = 'Vehicle Maintenance Fee'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')

    date = fields.Date(string='Date of maintenance')
    cost = fields.Float(string='Cost of maintenance', default=0)

    type = fields.Selection(selection=[("fuel", "Fuel"), ("maintenance", "Maintenance")])



class VehicleFuelFee(models.Model):
    _name = 'vehicle.fuel.fee'
    _description = 'Vehicle Fuel Fee'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    date = fields.Date(string='Date')
    cost = fields.Float(string='Cost')







class Service_date (models.Model):
    _name = "service.date"

    service_renewal_date = fields.Date("Service renewal date")
    service_due_date = fields.Date("Service Due date")
    service_date = fields.Date("Service Date")

    header = fields.Many2one('fleet.vehicle')


class Contract_date(models.Model):
    _name = "contract.date"

    contract_renewal_date = fields.Date("Contract Starting date")
    contract_due_date = fields.Date("Contract Due date")

    header = fields.Many2one('fleet.vehicle')






