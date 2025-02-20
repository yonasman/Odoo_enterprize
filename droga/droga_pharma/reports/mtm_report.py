import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from io import BytesIO
import xlsxwriter
import base64
import re


class ReportWizard(models.TransientModel):
    _name = "mtm.report.wizard"
    _description = "Print MTM Excel Report"
    fileout = fields.Binary(string='File Output')

    customer = fields.Many2one('droga.pharma.cust.employees', string='Customer')
    client = fields.Many2one('res.partner', string='Client')
    date_to = fields.Date(string='To Date',default=datetime.date.today() + relativedelta(weeks=0,weekday=-1))
    date_from= fields.Date(string='From Date',default=datetime.date.today() - relativedelta(weeks=1,weekday=0))

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

        header_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 22})
        main_title_format = workbook.add_format({
            'bold': 0,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 16})
        parameter_format = workbook.add_format({
            'bold': 1,
            'border': 7,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 12,
            'fg_color': '#F6F5F5'})

        separator_format = workbook.add_format({
            'bold': 1,
            'border': 7,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 12,
            'fg_color': '#D9D9D9'})

        title_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})

        # set header
        row_start = 1
        sheet.set_row(row_start + 1, 30)
        sheet.merge_range('A' + str(row_start + 1) + ':L' + str(row_start + 1), 'DROGA PHARMA P.L.C', header_format)
        sheet.merge_range('A' + str(row_start + 2) + ':L' + str(row_start + 2), 'MTM Follow Up', main_title_format)
        sheet.merge_range('A' + str(row_start + 3) + ':F' + str(row_start + 7), 'Date from : ' + str(self.date_from),
                          parameter_format)
        sheet.merge_range('G' + str(row_start + 3) + ':L' + str(row_start + 7), 'Date to : ' + str(self.date_to),
                          parameter_format)

        # Set column widths

        sheet.set_column(0, 0, 15)  # Client
        sheet.set_column(1, 1, 15)  # Customer
        sheet.set_column(2, 2, 20)  # Indication
        sheet.set_column(3, 3, 25)  # Drug Therapy Problem
        sheet.set_column(4, 4, 25)  # Drug Therapy Cause
        sheet.set_column(5, 5, 20)  # Intervention
        sheet.set_column(6, 6, 30)  # Intervention Implemented
        sheet.set_column(7, 7, 30)  # Intervention Implemented
        sheet.set_column(8, 8, 30)  # Intervention Implemented

        row = 9
        col = 0
        sheet.write(row, col + 0, 'Client', title_format)
        sheet.write(row, col + 1, 'Customer', title_format)
        sheet.write(row, col + 2, 'Indication', title_format)
        sheet.write(row, col + 3, 'Drug Therapy Probl,em', title_format)
        sheet.write(row, col + 4, 'Drug Therapy Cause', title_format)
        sheet.write(row, col + 5, 'Intervention', title_format)
        sheet.write(row, col + 6, 'Intervention Implemented', title_format)
        sheet.write(row, col + 7, 'Assessment and Care Plan', title_format)
        sheet.write(row, col + 8, 'Intervention/ Recommendation', title_format)

    # Iterate over excel_data and write the values to the sheet
        for index, ed in enumerate(excel_data):
            row = row + 1
            client_match = re.findall(r"'([^']*)'", str(ed.get('client', '')))
            client_value = client_match[0] if client_match else ''
            sheet.write(row, col + 0, client_value, bold)

            customer_match = re.search(r"'([^']*)'", str(ed.get('customer', '')))
            customer_value = customer_match.group(1) if customer_match else ''
            sheet.write(row, col + 2, customer_value, bold)

            sheet.write(row, col + 2, re.sub('<[^<]+?>', '', str(ed.get('indication', ''))))
            sheet.write(row, col + 3, re.search(r"'([^']*)'", str(ed.get('drug_therapy_problem', ''))).group(1))

            drug_cause_match = re.search(r"'([^']*)'", str(ed.get('drug_therapy_cause', '')))
            drug_cause_value = drug_cause_match.group(1) if drug_cause_match else ''
            sheet.write(row, col + 4, drug_cause_value, bold)

            sheet.write(row, col + 5, re.sub('<[^<]+?>', '', str(ed.get('intervention', ''))))
            sheet.write(row, col + 6, re.sub('<[^<]+?>', '', str(ed.get('intervention_implemented', ''))))
            # sheet.write(row, col + 7, re.sub('<[^<]+?>', '', str(ed.get('asses_care_plan', ''))))
            # sheet.write(row, col + 8, re.sub('<[^<]+?>', '', str(ed.get('recs_inter', ''))))

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
