from odoo import models, fields, api
from datetime import date
from odoo.exceptions import ValidationError


class HrPayrollPaymentDeductions(models.Model):
    _name = 'hr.payroll.payment.deduction'

    contract_id = fields.Many2one("hr.contract", domain="[('state', '=', 'open')]")
    employee_id = fields.Many2one(related='contract_id.employee_id')
    input_type = fields.Selection([('Payment', 'Payment'), ('Deduction', 'Deduction')])
    input_types = fields.Many2one('hr.payslip.input.type', 'Input Types')
    date_from = fields.Date("Date From")
    date_to = fields.Date("Date To")
    amount = fields.Float("Amount")
    total_amount = fields.Float("Total Amount")
    rem_amount = fields.Float("Remaining Amount")

    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 index=True, default=lambda self: self.env.company.id)

    def update_contract_id(self):
        pds = self.env["hr.payroll.payment.deduction"].search([('contract_id.state', '!=', 'open')])

        for pd in pds:
            # Get the active contract for the employee
            active_contract = pd.employee_id.contract_id.filtered(lambda c: c.state == 'open')
            if active_contract:
                # update the contract id
                pd.contract_id = active_contract.id


class HrPayrollVariablePayments(models.Model):
    _name = 'hr.payroll.variable.payment'

    employee_id = fields.Many2one('hr.employee', rquired=True)
    division = fields.Many2one(related="employee_id.division")
    input_types = fields.Many2one('hr.payslip.input.type', 'Input Types')
    fiscal_year = fields.Many2one("account.fiscal.year", "Fiscal Year")
    period = fields.Many2one("account.fiscal.year.period", domain="[('fiscal_year_id', '=', fiscal_year)]")
    rate = fields.Float("Rate", digits=(12, 4))
    status = fields.Selection([('Not Paid', 'Not Paid'), ('Paid', 'Paid')], default='Not Paid')

    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 index=True, default=lambda self: self.env.company.id)

    # def write(self, vals):
    # for record in self:
    # if record.status == 'Paid':
    # raise ValidationError('You cannot update records with status "paid".')
    # return super(HrPayrollVariablePayments, self).write(vals)

    def unlink(self):
        for record in self:
            if record.status == 'Paid':
                raise ValidationError('You cannot delete records with status "paid".')
        return super(HrPayrollVariablePayments, self).unlink()


class HrPayrollRates(models.Model):
    _name = 'hr.payroll.rate'

    code = fields.Char("Code")
    rate = fields.Float("Rate", digits=(12, 4))
    date_from = fields.Date("Date From")
    date_to = fields.Date("Date To")

    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 index=True, default=lambda self: self.env.company.id)
