from odoo import api,fields, models
from io import BytesIO
import xlsxwriter
import base64
import re


class ReportWizard(models.TransientModel):
    _name = "mtm.report.wizard"
    _description = "Print MTM Excel Report"
    fileout = fields.Binary(string='File Output')

    customer = fields.Many2one('res.partner', string='Customer')
    client = fields.Many2one('res.partner', string='Client')
    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date')


    def action_get_xls(self, data):
        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)
        self.generate_xls_report(workbook, data)
        workbook.close()

        self.fileout = base64.b64encode(file_io.getvalue())
        file_io.close()

        datetime_string = fields.Datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'MTM Follow up From {self.date_from}_{datetime_string}.xlsx'

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': f'web/content/?model={self._name}&id={self.id}&field=fileout&download=true&filename={filename}'
        }

    def generate_xls_report(self, workbook, excel_data):
        sheet = workbook.add_worksheet('MTM Report')
        bold = workbook.add_format({'bold': True})

        row = 0
        col = 3
        sheet.write(row, col, 'MTM Report', bold)
        row = 2
        col = 0
        sheet.write(row, col + 1, 'Client', bold)
        sheet.write(row, col + 2, 'Customer', bold)
        sheet.write(row, col + 3, 'Indication', bold)
        sheet.write(row, col + 4, 'Drug Therapy Problem', bold)
        sheet.write(row, col + 5, 'Drug Therapy Cause', bold)
        sheet.write(row, col + 6, 'Intervention', bold)
        sheet.write(row, col + 7, 'Intervention Implemented', bold)
        sheet.write(row, col + 8, 'Assessment and Care Plan', bold)
        sheet.write(row, col + 9, 'Intervention / Recommendation', bold)

        for ed in excel_data:
            row += 1
            sheet.write(row, col + 1, re.search(r"'([^']*)'", str(ed.get('client', ''))).group(1), bold)
            sheet.write(row, col + 2, re.search(r"'([^']*)'", str(ed.get('customer', ''))).group(1), bold)
            sheet.write(row, col + 3, re.sub('<[^<]+?>', '', str(ed.get('indication', ''))), bold)
            sheet.write(row, col + 4, re.search(r"'([^']*)'", str(ed.get('drug_therapy_problem', ''))).group(1), bold)
            sheet.write(row, col + 5, re.search(r"'([^']*)'", str(ed.get('drug_therapy_cause', ''))).group(1), bold)
            sheet.write(row, col + 6, re.sub('<[^<]+?>', '', str(ed.get('intervention', ''))), bold)
            sheet.write(row, col + 7, re.sub('<[^<]+?>', '', str(ed.get('intervention_implemented', ''))), bold)
            # sheet.write(row, col + 8, re.sub('<[^<]+?>', '', str(ed.get('asses_care_plan', ''))), bold)
            # sheet.write(row, col + 9, re.sub('<[^<]+?>', '', str(ed.get('recs_inter', ''))), bold)

    def action_wizard_print_excel_report(self):
        _client = self.client
        _customer = self.customer

        domain = [
            ('create_date', '>=', self.date_from),
            ('create_date', '<=', self.date_to),
        ]
        if _client:
            domain.append(('client', '=', _client.id))

        if _customer:
            domain.append(('customer', '=', _customer.id))
        excel_data = self.env['droga.pharma.mtm.follow_up.detail'].search_read(domain)
        return self.action_get_xls(excel_data)

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}


