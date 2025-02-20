from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class Attendance(models.Model):
    _inherit = 'hr.attendance'

    attendance_machine_trans_id = fields.Char("Attendance Machine Trans ID")
    attendance_date = fields.Date("Attendance Date", default=datetime.now().date())

    real_worked_hours = fields.Float(string="Real Work Hours", compute="compute_real_worked_hours")

    employee_badge_id = fields.Char(related='employee_id.barcode', string='Badge ID')
    department = fields.Char(related='employee_id.department_name', string='Department')
    attendance_from = fields.Selection([('Attendance Machine', 'Attendance Machine'), ('Kiosk Mode', 'Kiosk Mode')],
                                       default='Attendance Machine', string='Attendance From')

    @api.model
    def create(self, vals):
        # search record for the current employee

        check_in = datetime.strptime(str(vals['check_in']), '%Y-%m-%d %H:%M:%S')
        check_in = check_in.strftime('%Y-%m-%d')

        employee_id = vals['employee_id']
        check_in_record = self.env["hr.attendance"].search(
            [('check_in', '<=', check_in), ('check_in', '>=', check_in), ('employee_id', '=', employee_id)])

        if 'attendance_date' in vals:
            vals["attendance_from"] = "Attendance Machine"
        else:
            vals["attendance_from"] = "Kiosk Mode"

        if check_in_record:
            raise ValidationError("You can't create check in more than once!")
        else:
            res = super(Attendance, self).create(vals)
            return res

    def update_not_checked_out_records(self):
        dt = datetime.utcnow()
        check_in = dt.strftime('%Y-%m-%d')

        attendances = self.env['hr.attendance'].search([('check_out', '=', False)])
        for attendance in attendances:
            attendance['check_out'] = attendance['check_in']

    @api.depends('worked_hours')
    def compute_real_worked_hours(self):
        for record in self:
            record.real_worked_hours = 1
            date_object = record.check_in
            if record.worked_hours == 0:
                record.real_worked_hours = 0
            elif date_object.weekday() in [5, 6]:
                record.real_worked_hours = record.worked_hours
            else:
                record.real_worked_hours = record.worked_hours - 1


class AttendanceReport(models.Model):
    _name = 'droga.hr.attendance.report'

    _order = 'date desc'

    employee_id = fields.Many2one("hr.employee")
    department = fields.Char(related='employee_id.department_name', string='Department', store=True)
    employee_badge_id = fields.Char(related='employee_id.barcode', string='Badge ID', store=True)
    date = fields.Date("Attendance Day")
    check_in = fields.Datetime("Check In")
    check_out = fields.Datetime("Check Out")
    day_count = fields.Float("Day Count")
    is_absent = fields.Boolean("Absent", default=False)
    absence_reason = fields.Char("Reason")
    company_id = fields.Many2one("res.company")
    late_minute = fields.Float("Late Minute")
    worked_hours = fields.Float("Worked Hours")
    real_worked_hours = fields.Float("Real Worked Hours")

    def update_attendance_report(self, start_day_str):
        # get active employees
        vals = {}

        start_day = datetime.strptime(str(start_day_str), "%Y-%m-%d").date()
        # Get the current day
        current_day = datetime.now().date()

        active_employees = self.env["hr.employee"].search(
            [('active', '=', True), ('is_attendance_required', '=', True)])

        for employee in active_employees:

            # Define the loop range using timedelta
            day = start_day

            while day <= current_day:

                # check for sunday
                if day.weekday() == 6:
                    day += timedelta(days=1)
                    continue

                emp_attendances = self.env["hr.attendance"].search(
                    [('employee_id', '=', employee.id), ('attendance_date', '=', day)])

                attendance_report = self.env['droga.hr.attendance.report'].search(
                    [('employee_id', '=', employee.id), ('date', '=', day)])

                if len(emp_attendances) == 0 and len(attendance_report) == 0:
                    # create absent record
                    vals["employee_id"] = employee.id
                    vals["date"] = day
                    vals["is_absent"] = True
                    vals["absence_reason"] = "Not Showed Up"
                    vals["company_id"] = employee.company_id.id
                    vals["late_minute"] = 0
                    vals["check_in"] = None
                    vals["check_out"] = None
                    vals["worked_hours"] = 0
                    vals["real_worked_hours"] = 0

                    self.env["droga.hr.attendance.report"].create(vals)

                for attendance in emp_attendances:

                    check_in_time = datetime.strptime(str(attendance.check_in), '%Y-%m-%d %H:%M:%S')

                    minutes_late = 0
                    is_absent = False
                    absence_reason = ""
                    real_worked_hours = 0

                    real_worked_hours = self.compute_real_worked_hours(attendance)

                    # Calculate five minutes late
                    if check_in_time.hour >= 5:
                        start_time_str = str(check_in_time.date()) + " 05:00:00"

                        # Convert string representations to datetime objects
                        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                        end_time = datetime.strptime(str(check_in_time), "%Y-%m-%d %H:%M:%S")

                        # Calculate the time difference
                        time_difference = end_time - start_time

                        # Extract the total minutes from the time difference
                        minutes_late = time_difference.total_seconds() / 60

                    if minutes_late > 30 and attendance.worked_hours == 0 and employee.check_out:
                        is_absent = True
                        absence_reason = "Late >30 Min & No Check Out"
                    elif minutes_late > 30 and attendance.worked_hours != 0:
                        absence_reason = "Late >30 Min"
                        is_absent = True
                    elif attendance.worked_hours == 0 and employee.check_out:
                        absence_reason = "No Check Out"
                        is_absent = True
                    else:
                        is_absent = False
                        absence_reason = "Showed Up"

                    # if employee don't require check out time set the check out to 5:00
                    check_out = attendance.check_out
                    if not employee.check_out:
                        check_out = str(day) + " 14:00:00"
                        check_out = datetime.strptime(check_out, '%Y-%m-%d %H:%M:%S')

                    if len(attendance_report) == 0:  # insert new record

                        vals["employee_id"] = employee.id
                        vals["date"] = check_in_time.date()
                        vals["is_absent"] = is_absent
                        vals["absence_reason"] = absence_reason
                        vals["company_id"] = employee.company_id.id
                        vals["late_minute"] = minutes_late
                        vals["check_in"] = attendance.check_in
                        vals["check_out"] = check_out
                        vals["worked_hours"] = attendance.worked_hours
                        vals["real_worked_hours"] = real_worked_hours

                        self.env["droga.hr.attendance.report"].create(vals)

                    else:  # update record

                        attendance_report.write(
                            {'is_absent': is_absent, 'absence_reason': absence_reason,
                             'check_in': attendance.check_in,
                             'check_out': attendance.check_out, 'late_minute': minutes_late,
                             'real_worked_hours': real_worked_hours})

                # Move to the next day
                day += timedelta(days=1)

    def compute_real_worked_hours(self, attendance):
        for record in attendance:
            date_object = record.check_in
            if record.worked_hours == 0:
                return 0
            elif date_object.weekday() in [5, 6]:
                return record.worked_hours
            else:
                return record.worked_hours - 1


class AttendanceOvertTimeReport(models.Model):
    _name = 'droga.hr.attendance.over.time'

    _order = 'date desc'

    def _get_employee_id(self):
        # assigning the related employee of the logged in user
        employee_rec = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    employee_id = fields.Many2one("hr.employee")
    manager_id = fields.Many2one(related='employee_id.parent_id', string='Manager', store=True)
    department = fields.Char(related='employee_id.department_name', string='Department', store=True)
    employee_badge_id = fields.Char(related='employee_id.barcode', string='Badge ID', store=True)
    date = fields.Date("Attendance Day")
    check_in = fields.Datetime("Check In")
    check_out = fields.Datetime("Check Out")
    company_id = fields.Many2one("res.company")
    worked_hours = fields.Float("Worked Hours")
    real_worked_hours = fields.Float("Real Worked Hours")
    over_time_hour = fields.Float("Over Time Hour")
    approval_status = fields.Selection([('Approved', 'Approved'), ('Not Approved', 'Not Approved'),('Rejected', 'Rejected')], tracking=True,
                                       default='Not Approved')

    current_employee_id = fields.Many2one("hr.employee", default=_get_employee_id)

    def update_over_time_records(self, start_day_str):
        vals = {}

        start_day = datetime.strptime(str(start_day_str), "%Y-%m-%d").date()
        attendances = self.env['droga.hr.attendance.report'].search(
            [('is_absent', '=', False), ('real_worked_hours', '>=', 9), ('date', '>=', start_day)])

        for attendance in attendances:
            overtime = self.env["droga.hr.attendance.over.time"].search(
                [('employee_id', '=', attendance.employee_id.id), ('date', '=', attendance.date)])

            if len(overtime) == 0:
                over_time_hour = attendance.real_worked_hours - 8
                vals["employee_id"] = attendance.employee_id.id
                vals["date"] = attendance.date
                vals["check_in"] = attendance.check_in
                vals["check_out"] = attendance.check_out
                vals["company_id"] = attendance.company_id.id
                vals["worked_hours"] = attendance.worked_hours
                vals["real_worked_hours"] = attendance.real_worked_hours
                vals["over_time_hour"] = over_time_hour

                self.env["droga.hr.attendance.over.time"].create(vals)

    def approve_over_time(self):
        for record in self:
            if record.approval_status == 'Approved':
                raise ValidationError("It is already approved")
            else:
                record.write({'approval_status': 'Approved'})

    def reject_over_time(self):
        for record in self:
            if record.approval_status == 'Rejected':
                raise ValidationError("It is already rejected")
            else:
                record.write({'approval_status': 'Rejected'})



class AttendanceOvertTimeReport1(models.Model):
    _name = 'droga.hr.attendance.overt_time'

    _order = 'date desc'

    employee_id = fields.Many2one("hr.employee")
    department = fields.Char(related='employee_id.department_name', string='Department', store=True)
    employee_badge_id = fields.Char(related='employee_id.barcode', string='Badge ID', store=True)
    date = fields.Date("Attendance Day")
    check_in = fields.Datetime("Check In")
    check_out = fields.Datetime("Check Out")
    company_id = fields.Many2one("res.company")
    worked_hours = fields.Float("Worked Hours")
    real_worked_hours = fields.Float("Real Worked Hours")
    over_time_hour = fields.Float("Over Time Hour")
    approval_status = fields.Selection([('Approved', 'Approved'), ('Not Approved', 'Not Approved')], tracking=True,
                                       default='Not Approved')
