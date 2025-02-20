from odoo import api, fields, models
from odoo.osv import expression


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    division = fields.Many2one('droga.hr.division')

    @api.depends('division')
    def _compute_employee_ids(self):
        for wizard in self:
            domain = wizard._get_available_contracts_domain()
            if wizard.division:
                domain = expression.AND([
                    domain,
                    [('division', '=', self.division.id)]
                ])

            if wizard.department_id:
                domain = expression.AND([
                    domain,
                    [('department_id', 'child_of', self.department_id.id)]
                ])
            wizard.employee_ids = self.env['hr.employee'].search(domain)
