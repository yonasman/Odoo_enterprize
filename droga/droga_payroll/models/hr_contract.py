import datetime

from odoo import models, fields, api
from datetime import date


class HrContract(models.Model):
    _inherit = 'hr.contract'

    housing_allowance = fields.Float("Housing Allowance", default=0, tracking=True)
    transport_allowance = fields.Float("Transport Allowance", default=0)
    representation_allowance = fields.Float("Representation Allowance", default=0)
    fuel_allowance = fields.Float("Fuel Allowance", default=0)
    acting_allowance = fields.Float("Acting Allowance", default=0)
    telephone_allowance = fields.Float("Telephone Allowance", default=0)
    pension_contribution = fields.Boolean("Contribute Pension", default=True)
    sales = fields.Boolean("Sales",
                           help="For sales transport allowance upto 2200 is not taxable for others it is upto 600")
    canteen = fields.Boolean("Uses Canteen Service", help="If the employee uses canteen service tick the check box");
    has_company_vehicle = fields.Boolean('Company Vehicle',
                                         help="If the employee provided company vehicle tick the check box. The system will not calculate transport allowance")

    custom_salary_structure = fields.Boolean("Custom Salary Structure", default=False)
    salary_structure = fields.One2many(related="job_id.salary_structure")
    salary_structure_custom = fields.One2many("hr.job.salary", "contract_id")
    payment_deductions = fields.One2many("hr.payroll.payment.deduction", 'contract_id')
    paid_by_usd = fields.Boolean("Payment Currency USD")

    # sales commission
    sales_commission = fields.Float("Sales Commission")

    # get contract rate
    def get_employee_rate(self, payment_code):
        amount = 0
        for record in self:
            if record.state == 'open':
                if record.custom_salary_structure:  # get rate from custom salary structure

                    salary_structures = record.salary_structure_custom

                    for salary_structure in salary_structures:
                        if salary_structure.date_to >= date.today():
                            rates = salary_structure.salary_detail
                            for rate in rates:
                                if rate.payment_type.code == payment_code:
                                    amount = rate.amount
                else:  # get rate from main salary structure
                    salary_structures = record.salary_structure

                    for salary_structure in salary_structures:

                        if salary_structure.date_to >= date.today():
                            rates = salary_structure.salary_detail
                            for rate in rates:
                                if rate.payment_type.code == payment_code:
                                    amount = rate.amount

        return amount

    def get_payment_deduction_rate(self, pd_code):
        amount = 0
        for record in self:
            if record.state == 'open':
                payment_deductions = record.payment_deductions.search(
                    [('input_types.code', '=', pd_code), ('contract_id', '=', record.id)])
                for payment_deduction in payment_deductions:
                    amount = payment_deduction.amount

        return amount

    def get_fixed_rate(self, pd_code):

        # get fuel rate
        rates = self.env['hr.payroll.rate'].search(
            [('code', '=', pd_code), ('date_to', '>=', datetime.datetime.now())])

        rate = 0
        for rate in rates:
            rate = rate.rate

        return rate

    def get_variable_payment(self, employee_id, variable_payment_type):
        rate = 0
        variable_payments = self.env["hr.payroll.variable.payment"].search(
            [('employee_id', '=', employee_id), ('input_types.code', '=', variable_payment_type),
             ('status', '=', 'Not Paid')])

        for variable_payment in variable_payments:
            rate = variable_payment.rate

        return rate
