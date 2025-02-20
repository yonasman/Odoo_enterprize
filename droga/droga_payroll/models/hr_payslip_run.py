from odoo import models, fields, api
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    # add year and period
    fiscal_year = fields.Many2one("account.fiscal.year", "Fiscal Year")
    period = fields.Many2one("account.fiscal.year.period", domain="[('fiscal_year_id', '=', fiscal_year)]")
    mail_server = fields.Char(compute="get_outgoing_email")

    date_start = fields.Date(string='Date From')
    date_end = fields.Date(string='Date To')

    @api.depends('date_start', 'date_end')
    def get_outgoing_email(self):
        self.mail_server = ""
        # Search for the outgoing mail server with the lowest priority (default)
        mail_servers = self.env['ir.mail_server'].search([], order='sequence', limit=1)

        if mail_servers:
            self.mail_server = mail_servers.smtp_user

    def action_paid(self):
        # Call the original 'action_paid' method
        result = super(HrPayslipRun, self).action_paid()
        # update variable transactions to paid
        variable_transactions = self.env["hr.payroll.variable.payment"].search([('period', '=', self.period.id)])

        for record in variable_transactions:
            record.write({'status': 'Paid'})

        return result

    def droga_payroll_sheet_report_action(self):

        view = self.env.ref(
            'droga_payroll.droga_payroll_sheet_report_form')

        return {
            'name': 'Payroll Master Report',
            'view_mode': 'form',
            'res_model': 'hr.payslip.run.report',
            'view_id': view.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_batch': self.id
            }
        }

    def action_send_payslip_email(self):

        # if self.state == 'close' or self.state == 'paid':

        for payslip in self.slip_ids:
            try:
                mail_template = self.env.ref('droga_payroll.email_template_payslip')
                if mail_template and payslip.employee_id.work_email:
                    # Sanitize dynamic content
                    sanitized_employee_name = payslip.employee_id.name.replace('\n', ' ').replace('\r', ' ')
                    sanitized_period_description = payslip.period.description.replace('\n', ' ').replace('\r',
                                                                                                         ' ') if payslip.period else ''
                    sanitized_date_from = payslip.date_from or ''
                    sanitized_date_to = payslip.date_to or ''

                    # Update context with sanitized content
                    context = {
                        'default_employee_name': sanitized_employee_name,
                        'default_period_description': sanitized_period_description,
                        'default_date_from': sanitized_date_from,
                        'default_date_to': sanitized_date_to
                    }

                    # Send email with context
                    mail_template.with_context(context).send_mail(payslip.id, force_send=True)
                    _logger.info(f'Payslip email sent successfully for {payslip.employee_id.name}')
                else:
                    _logger.warning('Email template not found: droga_payroll.email_template_payslip')
            except Exception as e:
                _logger.error(f'Error sending payslip email for {payslip.employee_id.name}: {str(e)}')

    # else:
    # raise ValidationError(
    # "The status must be changed to done to send payslip email")

    @api.onchange("period")
    def _on_period_change(self):
        for record in self:
            record.date_start = record.period.date_from
            record.date_end = record.period.date_to
