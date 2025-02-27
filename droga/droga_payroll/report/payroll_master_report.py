from odoo import api, fields, models
from io import BytesIO
import xlsxwriter
import datetime

from odoo.exceptions import UserError

try:
    from base64 import encodebytes
except ImportError:
    from base64 import encodestring as encodebytes


class PayrollMasterReports(models.Model):
    _name = 'hr.payslip.run.report'

    #
    batch = fields.Many2one('hr.payslip.run', required=True)
    fileout = fields.Binary('File', readonly=True)
    cost_center = fields.Many2many("hr.department")
    cost_center_analytic = fields.Many2many("account.analytic.account", domain=[('plan_id.name', '=', 'Cost Center')])

    def convert_to_word(self, num):
        num_strings = str(num)
        numbers = num_strings.split('.')

        word = self.int_to_word(int(numbers[0])) + ' birr'

        if len(numbers) == 2:
            if int(numbers[1]) != 0:
                if len(numbers[1]) == 1:
                    numbers[1] = int(numbers[1]) * 10.0

                word = self.int_to_word(int(numbers[0])) + ' birr and ' + self.int_to_word(int(numbers[1])) + ' cents'

        return word.capitalize()

    def int_to_word(self, num):
        d = {0: 'zero', 1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five',
             6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten',
             11: 'eleven', 12: 'twelve', 13: 'thirteen', 14: 'fourteen',
             15: 'fifteen', 16: 'sixteen', 17: 'seventeen', 18: 'eighteen',
             19: 'nineteen', 20: 'twenty',
             30: 'thirty', 40: 'forty', 50: 'fifty', 60: 'sixty',
             70: 'seventy', 80: 'eighty', 90: 'ninety'}
        k = 1000
        m = k * 1000
        b = m * 1000
        t = b * 1000

        assert (0 <= num)

        if (num < 20):
            return d[num]

        if (num < 100):
            if num % 10 == 0:
                return d[num]
            else:
                return d[num // 10 * 10] + '-' + d[num % 10]

        if (num < k):
            if num % 100 == 0:
                return d[num // 100] + ' hundred'
            else:
                return d[num // 100] + ' hundred ' + self.int_to_word(num % 100)

        if (num < m):
            if num % k == 0:
                return self.int_to_word(num // k) + ' thousand'
            else:
                return self.int_to_word(num // k) + ' thousand ' + self.int_to_word(num % k)

        if (num < b):
            if (num % m) == 0:
                return self.int_to_word(num // m) + ' million'
            else:
                return self.int_to_word(num // m) + ' million ' + self.int_to_word(num % m)

        if (num < t):
            if (num % b) == 0:
                return self.int_to_word(num // b) + ' billion'
            else:
                return self.int_to_word(num // b) + ' billion ' + self.int_to_word(num % b)

        if (num % t == 0):
            return self.int_to_word(num // t) + ' trillion'
        else:
            return self.int_to_word(num // t) + ' trillion ' + self.int_to_word(num % t)

        raise AssertionError('num is too large: %s' % str(num))

    def action_generate_payroll_master_report(self):
        # This generates our Excel file
        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)
        self.payroll_sheet_report(workbook)

        self.payroll_net_report(workbook)
        self.deductions_report(workbook)
        self.payroll_reconciliation_report(workbook)
        self.mobile_card_report(workbook)
        self.company_vehicle_report(workbook)
        workbook.close()

        # The file to download will be stored under fileout field
        self.fileout = encodebytes(file_io.getvalue())
        file_io.close()

        # The file name is stored under filename
        datetime_string = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = '%s_%s' % ('Payroll Master Report ', datetime_string)

        # This downloads file. The file is fileout and the name if filename
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + filename,
        }

    def payroll_sheet_report(self, workbook):
        sheet = workbook.add_worksheet('Payroll Sheet')

        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 10)
        sheet.set_column('C:C', 30)
        sheet.set_column('D:D', 30)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 15)

        sheet.set_column('G:G', 15)
        sheet.set_column('H:H', 15)
        sheet.set_column('I:I', 15)
        sheet.set_column('J:J', 15)
        sheet.set_column('K:K', 15)
        sheet.set_column('L:L', 15)
        sheet.set_column('M:M', 15)
        sheet.set_column('N:N', 15)

        sheet.set_column('O:O', 15)
        sheet.set_column('P:P', 15)
        sheet.set_column('Q:Q', 15)
        sheet.set_column('R:R', 15)
        sheet.set_column('S:S', 15)
        sheet.set_column('T:T', 15)
        sheet.set_column('U:U', 15)
        sheet.set_column('V:V', 15)

        sheet.set_column('W:W', 15)
        sheet.set_column('X:X', 15)
        sheet.set_column('Y:Y', 15)
        sheet.set_column('Z:Z', 15)

        row_start = 2
        date_format = workbook.add_format(
            {'num_format': 'mm/dd/yyyy', 'border': 7})
        num_format = workbook.add_format({'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 9})
        num_format_sub_total = workbook.add_format({'num_format': 43, 'border': 1, 'bold': 1})
        cent_format = workbook.add_format({'num_format': 41, 'border': 1})
        border = workbook.add_format({'border': 1, 'font_name': 'Calibri', 'font_size': 9})
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 22})
        main_title_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Calibri',
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
            'font_size': 9,
            'font_name': 'Calibri',
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})
        title_format_num = workbook.add_format({
            'bold': 1,
            'border': 1,
            'num_format': 43,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})

        # search RFQ

        sheet.merge_range('A1:G1', self.batch.company_id.name, main_title_format)
        sheet.merge_range('A2:G2', self.batch.name, main_title_format)

        sheet.write(row_start, 0, 'No', title_format)
        sheet.write(row_start, 1, 'ID No', title_format)
        sheet.write(row_start, 2, 'Employee Name', title_format)
        sheet.write(row_start, 3, 'Job Position', title_format)
        sheet.write(row_start, 4, 'Cost Center', title_format)
        sheet.write(row_start, 5, 'Basic Salary', title_format)
        sheet.write(row_start, 6, 'Overtime', title_format)
        sheet.write(row_start, 7, 'Housing Allowance', title_format)
        sheet.write(row_start, 8, 'Transport Allowance', title_format)
        sheet.write(row_start, 9, 'Representation Allowance', title_format)
        sheet.write(row_start, 10, 'Fuel Allowance', title_format)
        sheet.write(row_start, 11, 'Acting Allowance', title_format)

        sheet.write(row_start, 12, 'Commission', title_format)
        sheet.write(row_start, 13, 'Parking & Lunch', title_format)

        sheet.write(row_start, 14, 'Other*', title_format)
        sheet.write(row_start, 15, 'Gross Earning', title_format)
        sheet.write(row_start, 16, 'Taxable Earning', title_format)
        sheet.write(row_start, 17, 'Income Tax', title_format)
        sheet.write(row_start, 18, 'Pension Employee', title_format)
        sheet.write(row_start, 19, 'Deductions', title_format)
        sheet.write(row_start, 20, 'Total Deduction', title_format)
        sheet.write(row_start, 21, 'Net Pay', title_format)
        sheet.write(row_start, 22, 'Pension Employer', title_format)
        row_start += 1

        # subtotal variable subtotal
        basic_sub_total = 0
        overtime_sub_total = 0
        housing_sub_total = 0
        transport_sub_total = 0
        rep_sub_total = 0
        fuel_sub_total = 0
        acting_sub_total = 0
        commission_sub_total = 0
        parking_lunch_total = 0
        other_sub_total = 0
        gross_sub_total = 0
        taxable_sub_total = 0
        income_tax_sub_total = 0
        pen1_sub_total = 0
        pen2_sub_total = 0
        ded_sub_total = 0
        total_ded_sub_total = 0
        net_pay_sub_total = 0

        # search based on cost center
        if self.cost_center_analytic.ids:
            slips = self.batch.slip_ids.search(
                [('contract_id.analytic_account_id', 'in', self.cost_center_analytic.ids),
                 ('period', '=', self.batch.period.id)])
        else:
            slips = self.batch.slip_ids

        for record in slips:
            sheet.write(row_start, 0, row_start - 2, border)
            sheet.write(row_start, 1, record.employee_id.barcode, border)
            sheet.write(row_start, 2, record.employee_id.name, border)
            sheet.write(row_start, 3, record.employee_id.job_title, border)
            sheet.write(row_start, 4, record.contract_id.analytic_account_id.name, border)

            # formatemployee_id
            num = 0
            sheet.write(row_start, 5, num, num_format)
            sheet.write(row_start, 6, num, num_format)
            sheet.write(row_start, 7, num, num_format)
            sheet.write(row_start, 8, num, num_format)
            sheet.write(row_start, 9, num, num_format)
            sheet.write(row_start, 10, num, num_format)
            sheet.write(row_start, 11, num, num_format)
            sheet.write(row_start, 12, num, num_format)
            sheet.write(row_start, 13, num, num_format)
            sheet.write(row_start, 14, num, num_format)
            sheet.write(row_start, 15, num, num_format)
            sheet.write(row_start, 16, num, num_format)
            sheet.write(row_start, 17, num, num_format)
            sheet.write(row_start, 18, num, num_format)
            sheet.write(row_start, 19, num, num_format)
            sheet.write(row_start, 20, num, num_format)
            sheet.write(row_start, 21, num, num_format)
            sheet.write(row_start, 22, num, num_format)

            # get payroll detail
            for payslip_detail in record.line_ids:
                # format the cell

                if payslip_detail.code == 'BASIC':
                    sheet.write(row_start, 5, payslip_detail.total, num_format)
                    basic_sub_total += payslip_detail.total
                elif payslip_detail.code == 'OTT':  # overtime
                    sheet.write(row_start, 6, payslip_detail.total, num_format)
                    overtime_sub_total += payslip_detail.total
                elif payslip_detail.code == 'HOALL':  # Housing Allowance
                    sheet.write(row_start, 7, payslip_detail.total, num_format)
                    housing_sub_total += payslip_detail.total
                elif payslip_detail.code == 'TRALL':  # Transport Allowance
                    sheet.write(row_start, 8, payslip_detail.total, num_format)
                    transport_sub_total += payslip_detail.total
                elif payslip_detail.code == 'REPALL':  # Representative Allowance
                    sheet.write(row_start, 9, payslip_detail.total, num_format)
                    rep_sub_total += payslip_detail.total
                elif payslip_detail.code == 'FUEALL':  # Fuel Allowance
                    sheet.write(row_start, 10, payslip_detail.total, num_format)
                    fuel_sub_total += payslip_detail.total
                elif payslip_detail.code == 'ACTALL':  # Acting Allowance
                    sheet.write(row_start, 11, payslip_detail.total, num_format)
                    acting_sub_total += payslip_detail.total

                elif payslip_detail.code == 'COMMTOTAL':  # Commission
                    sheet.write(row_start, 12, payslip_detail.total, num_format)
                    commission_sub_total += payslip_detail.total
                elif payslip_detail.code == 'PARLUN':  # Parking & lunch
                    sheet.write(row_start, 13, payslip_detail.total, num_format)
                    parking_lunch_total += payslip_detail.total


                elif payslip_detail.code == 'OTHALL':  # Othe Allowances
                    sheet.write(row_start, 14, payslip_detail.total, num_format)
                    other_sub_total += payslip_detail.total
                elif payslip_detail.code == 'GROSS':  # Gross Earning
                    sheet.write(row_start, 15, payslip_detail.total, num_format)
                    gross_sub_total += payslip_detail.total

                elif payslip_detail.code == 'TTI':  # Taxable Earning
                    sheet.write(row_start, 16, payslip_detail.total, num_format)
                    taxable_sub_total += payslip_detail.total
                elif payslip_detail.code == 'INCTAX':  # Income Tax
                    sheet.write(row_start, 17, payslip_detail.total, num_format)
                    income_tax_sub_total += payslip_detail.total
                elif payslip_detail.code == 'PEN1':  # Pension Employee
                    sheet.write(row_start, 18, payslip_detail.total, num_format)
                    pen1_sub_total += payslip_detail.total
                elif payslip_detail.code == 'NFALL':  # Deductions
                    sheet.write(row_start, 19, payslip_detail.total, num_format)
                    ded_sub_total += payslip_detail.total
                elif payslip_detail.code == 'DED':  # Total Deductions
                    sheet.write(row_start, 20, payslip_detail.total, num_format)
                    total_ded_sub_total += payslip_detail.total
                elif payslip_detail.code == 'NET':  # Net Pay
                    sheet.write(row_start, 21, payslip_detail.total, num_format)
                    net_pay_sub_total += payslip_detail.total
                elif payslip_detail.code == 'PEN2':  # Pension Employer
                    sheet.write(row_start, 22, payslip_detail.total, num_format)
                    pen2_sub_total += payslip_detail.total
            row_start += 1

        # sub total
        sheet.write(row_start, 5, basic_sub_total, num_format_sub_total)
        sheet.write(row_start, 6, overtime_sub_total, num_format_sub_total)
        sheet.write(row_start, 7, housing_sub_total, num_format_sub_total)
        sheet.write(row_start, 8, transport_sub_total, num_format_sub_total)
        sheet.write(row_start, 9, rep_sub_total, num_format_sub_total)

        sheet.write(row_start, 10, fuel_sub_total, num_format_sub_total)
        sheet.write(row_start, 11, acting_sub_total, num_format_sub_total)

        sheet.write(row_start, 12, other_sub_total, num_format_sub_total)
        sheet.write(row_start, 13, gross_sub_total, num_format_sub_total)

        sheet.write(row_start, 14, commission_sub_total, num_format_sub_total)
        sheet.write(row_start, 15, parking_lunch_total, num_format_sub_total)

        sheet.write(row_start, 16, taxable_sub_total, num_format_sub_total)

        sheet.write(row_start, 17, income_tax_sub_total, num_format_sub_total)
        sheet.write(row_start, 18, pen1_sub_total, num_format_sub_total)
        sheet.write(row_start, 19, ded_sub_total, num_format_sub_total)
        sheet.write(row_start, 20, total_ded_sub_total, num_format_sub_total)
        sheet.write(row_start, 21, net_pay_sub_total, num_format_sub_total)
        sheet.write(row_start, 22, pen2_sub_total, num_format_sub_total)

    def payroll_net_report(self, workbook):

        num_format = workbook.add_format({'num_format': 43, 'border': 1})
        num_format_sub_total = workbook.add_format({'num_format': 43, 'border': 1, 'bold': 1})
        border = workbook.add_format({'border': 1})

        big_header_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'left',
            'valign': 'vcenter',

            'font_size': 30})
        small_header_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 11})
        small1_header_format = workbook.add_format({
            'bold': 0,
            'border': 0,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 11})
        title_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})

        # get unique bank accounts
        bank_accounts = self.env['hr.employee'].read_group([], ['bank'], groupby=['bank'])

        for bank_account in bank_accounts:

            bank_id = False
            bank_name = ''
            bank_account_number = ''

            if bank_account['bank']:
                bank_id = bank_account['bank'][0]
                bank_name = str(bank_account['bank'][1])

                # get bank account number
                bank_account = self.env['res.bank'].search([('id', '=', bank_id)])

                if bank_account:
                    bank_account_number = bank_account.bic if bank_account.bic else ''

            sheet_name = bank_name + ' - Net Pay'
            sheet = workbook.add_worksheet(sheet_name)

            sheet.set_column('A:A', 5)
            sheet.set_column('B:B', 30)
            sheet.set_column('C:C', 15)
            sheet.set_column('D:D', 15)

            row_start = 13

            # add titles
            sheet.merge_range('A1:G1', self.batch.company_id.name, big_header_format)
            sheet.merge_range('A2:G2', 'Date:' + str(datetime.date.today()), small_header_format)
            sheet.merge_range('A3:G3', 'Our Ref. No.: ', small_header_format)
            sheet.merge_range('A4:G4', '', small_header_format)

            sheet.merge_range('A5:G5', bank_name, small_header_format)
            sheet.merge_range('A6:G6', 'Main Office', small_header_format)
            sheet.merge_range('A7:G7', '', small_header_format)
            sheet.merge_range('A8:G8', 'Re: PAYMENT TRANSFER', small_header_format)
            sheet.merge_range('A9:G9', '', small_header_format)

            sheet.merge_range('A10:G10',
                              'Dear Sir/ Madam- Please prepare the below payment from our Account No: ' + bank_account_number,
                              small1_header_format)
            sheet.merge_range('A11:G11', '', small_header_format)

            sheet.write(row_start, 0, 'No', title_format)
            sheet.write(row_start, 1, 'Employee Name', title_format)
            sheet.write(row_start, 2, 'Account', title_format)
            sheet.write(row_start, 3, 'Amount', title_format)
            row_start += 1
            total_net_pay = 0

            # search based on cost center
            # search based on cost center
            if self.cost_center_analytic.ids:
                slips = self.batch.slip_ids.search(
                    [('contract_id.analytic_account_id', 'in', self.cost_center_analytic.ids),
                     ('period', '=', self.batch.period.id)])
            else:
                slips = self.batch.slip_ids

            for record in slips:
                if record.employee_id.bank.id == bank_id:
                    bank_account = record.employee_id.bank_account if record.employee_id.bank_account else ''

                    sheet.write(row_start, 0, row_start - 13, border)
                    sheet.write(row_start, 1, record.employee_id.name, border)
                    sheet.write(row_start, 2, bank_account, border)
                    sheet.write(row_start, 3, record.net_wage, num_format)
                    row_start += 1
                    # total net pay
                    total_net_pay += record.net_wage

            # get total amount in word
            # amount_in_word = self.convert_to_word(total_net_pay)
            amount_in_word = self.env['account.move'].convert_to_word(round(total_net_pay, 2))

            sheet.merge_range('A12:G12', 'AMOUNT IN WORDS:' + str(amount_in_word),
                              small1_header_format)

            sheet.write(row_start, 2, "Total", num_format_sub_total)
            sheet.write(row_start, 3, total_net_pay, num_format_sub_total)

            row_start += 2
            row = 'A' + str(row_start) + ':G' + str(row_start)

            sheet.merge_range(row,
                              'Please debit our bank account with you for any of your regular bank service charges',
                              small1_header_format)

            row_start += 2
            row = 'A' + str(row_start) + ':G' + str(row_start)
            sheet.merge_range(row, 'Name: Henok Teka', small_header_format)

            row_start += 2
            row = 'A' + str(row_start) + ':G' + str(row_start)
            sheet.merge_range(row, 'Position: Chief Executive Officer       ________________________________',
                              small_header_format)

    def deductions_report(self, workbook):
        sheet = workbook.add_worksheet('Deductions')

        # Set column widths
        sheet.set_column('A:A', 8)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 10)
        sheet.set_column('D:D', 10)
        sheet.set_column('E:E', 10)
        sheet.set_column('F:F', 10)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:H', 10)
        sheet.set_column('I:I', 10)
        sheet.set_column('J:J', 10)
        sheet.set_column('K:K', 10)
        sheet.set_column('L:L', 10)
        sheet.set_column('M:M', 10)
        sheet.set_column('N:N', 10)
        sheet.set_column('O:O', 10)
        sheet.set_column('P:P', 10)
        sheet.set_column('Q:Q', 10)

        row_start = 2

        # Define formats
        date_format = workbook.add_format({'num_format': 'mm/dd/yyyy', 'border': 7})
        num_format = workbook.add_format({'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 9})
        num_format_sub_total = workbook.add_format({'num_format': 43, 'border': 1, 'bold': 1})
        cent_format = workbook.add_format({'num_format': 41, 'border': 1})
        border = workbook.add_format({'border': 1, 'font_name': 'Calibri', 'font_size': 9})
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format(
            {'bold': 1, 'border': 0, 'align': 'center', 'valign': 'vcenter', 'font_size': 22})
        main_title_format = workbook.add_format(
            {'bold': 1, 'border': 0, 'align': 'center', 'valign': 'vcenter', 'font_name': 'Calibri', 'font_size': 16})
        parameter_format = workbook.add_format(
            {'bold': 1, 'border': 7, 'align': 'left', 'valign': 'vcenter', 'font_size': 12, 'fg_color': '#F6F5F5'})
        separator_format = workbook.add_format(
            {'bold': 1, 'border': 7, 'align': 'left', 'valign': 'vcenter', 'font_size': 12, 'fg_color': '#D9D9D9'})
        title_format = workbook.add_format(
            {'bold': 1, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'font_name': 'Calibri',
             'text_wrap': 1, 'fg_color': '#F6F5F5'})
        title_format_num = workbook.add_format(
            {'bold': 1, 'border': 1, 'num_format': 43, 'align': 'center', 'valign': 'vcenter', 'font_size': 11,
             'text_wrap': 1, 'fg_color': '#F6F5F5'})

        # Write header
        sheet.merge_range('A1:G1', "Deductions", main_title_format)
        sheet.merge_range('A2:G2', self.batch.name, main_title_format)

        # Set column titles
        sheet.write(row_start, 0, 'ID No', title_format)
        sheet.write(row_start, 1, 'Employee Name', title_format)
        sheet.write(row_start, 2, 'Canteen', title_format)
        sheet.write(row_start, 3, 'Loan', title_format)
        sheet.write(row_start, 4, 'Fuel', title_format)
        sheet.write(row_start, 5, 'SACO Registration', title_format)
        sheet.write(row_start, 6, 'SACO Saving', title_format)
        sheet.write(row_start, 7, 'SACO Saving Additional', title_format)
        sheet.write(row_start, 8, "Edir", title_format)
        sheet.write(row_start, 9, 'SACO Share Purchase', title_format)
        sheet.write(row_start, 10, 'SACO Payment Deduction', title_format)
        sheet.write(row_start, 11, 'Cost Sharing', title_format)
        sheet.write(row_start, 12, 'Sport Contribution', title_format)
        sheet.write(row_start, 13, 'Others', title_format)
        sheet.write(row_start, 14, 'Total', title_format)

        row_start += 1

        # Search based on cost center
        if self.cost_center_analytic.ids:
            slips = self.batch.slip_ids.search([
                ('contract_id.analytic_account_id', 'in', self.cost_center_analytic.ids),
                ('period', '=', self.batch.period.id)
            ])
        else:
            slips = self.batch.slip_ids

        # Initialize totals
        totals = {
            'canteen': 0,
            'loan': 0,
            'fuel': 0,
            'saco_saving': 0,
            'saco_loan_payment': 0,
            'saco_registration': 0,
            'saco_additional_payment': 0,
            'edir': 0,
            'saco_share_payment': 0,
            'cost_sharing': 0,
            'sport_contribution': 0,
            'others': 0
        }

        # Loop through slips and write data
        for record in slips:
            sheet.write(row_start, 0, record.employee_id.barcode, border)
            sheet.write(row_start, 1, record.employee_id.name, border)

            # Set default values for deductions
            deductions = {
                'canteen': 0,
                'loan': 0,
                'fuel': 0,
                'saco_registration': 0,
                'saco_saving': 0,
                'saco_additional_payment': 0,
                'edir': 0,
                'saco_share_payment': 0,
                'saco_loan_payment': 0,
                'cost_sharing': 0,
                'sport_contribution': 0,
                'others': 0
            }

            # Write deduction values for each payslip
            for payslip_detail in record.line_ids:
                if payslip_detail.code == 'CANDED':  # canteen_total
                    deductions['canteen'] = payslip_detail.total
                    totals['canteen'] += payslip_detail.total
                elif payslip_detail.code == 'LOAN':  # loan_total
                    deductions['loan'] = payslip_detail.total
                    totals['loan'] += payslip_detail.total
                elif payslip_detail.code == 'NFALL':  # fuel
                    deductions['fuel'] = payslip_detail.total
                    totals['fuel'] += payslip_detail.total
                elif payslip_detail.code == 'SACOREG':  # saco Registration
                    deductions['saco_registration'] = payslip_detail.total
                    totals['saco_registration'] += payslip_detail.total
                elif payslip_detail.code == 'SACOSAV':  # saco saving
                    deductions['saco_saving'] = payslip_detail.total
                    totals['saco_saving'] += payslip_detail.total
                elif payslip_detail.code == 'SACOSAVAD':  # saco additional payment
                    deductions['saco_additional_payment'] = payslip_detail.total
                    totals['saco_additional_payment'] += payslip_detail.total
                elif payslip_detail.code == 'EDIR':  # Edir
                    deductions['edir'] = payslip_detail.total
                    totals['edir'] += payslip_detail.total
                elif payslip_detail.code == 'SACOSHA':  # saco share payment
                    deductions['saco_share_payment'] = payslip_detail.total
                    totals['saco_share_payment'] += payslip_detail.total
                elif payslip_detail.code == 'SACOPAY':  # saco payment deduction
                    deductions['saco_loan_payment'] = payslip_detail.total
                    totals['saco_loan_payment'] += payslip_detail.total
                elif payslip_detail.code == 'COSTSHA':  # cost sharing
                    deductions['cost_sharing'] = payslip_detail.total
                    totals['cost_sharing'] += payslip_detail.total
                elif payslip_detail.code == 'SPOCONT':  # sport contribution
                    deductions['sport_contribution'] = payslip_detail.total
                    totals['sport_contribution'] += payslip_detail.total

            # Write deduction values to the sheet
            sheet.write(row_start, 2, deductions['canteen'], num_format)
            sheet.write(row_start, 3, deductions['loan'], num_format)
            sheet.write(row_start, 4, deductions['fuel'], num_format)
            sheet.write(row_start, 5, deductions['saco_registration'], num_format)
            sheet.write(row_start, 6, deductions['saco_saving'], num_format)
            sheet.write(row_start, 7, deductions['saco_additional_payment'], num_format)
            sheet.write(row_start, 8, deductions['edir'], num_format)
            sheet.write(row_start, 9, deductions['saco_share_payment'], num_format)
            sheet.write(row_start, 10, deductions['saco_loan_payment'], num_format)
            sheet.write(row_start, 11, deductions['cost_sharing'], num_format)
            sheet.write(row_start, 12, deductions['sport_contribution'], num_format)
            sheet.write(row_start, 13, deductions['others'], num_format)

            row_start += 1

        # Write sub-totals
        sheet.write(row_start, 2, totals['canteen'], num_format_sub_total)
        sheet.write(row_start, 3, totals['loan'], num_format_sub_total)
        sheet.write(row_start, 4, totals['fuel'], num_format_sub_total)
        sheet.write(row_start, 5, totals['saco_registration'], num_format_sub_total)
        sheet.write(row_start, 6, totals['saco_saving'], num_format_sub_total)
        sheet.write(row_start, 7, totals['saco_additional_payment'], num_format_sub_total)
        sheet.write(row_start, 8, totals['edir'], num_format_sub_total)
        sheet.write(row_start, 9, totals['saco_share_payment'], num_format_sub_total)
        sheet.write(row_start, 10, totals['saco_loan_payment'], num_format_sub_total)
        sheet.write(row_start, 11, totals['cost_sharing'], num_format_sub_total)
        sheet.write(row_start, 12, totals['sport_contribution'], num_format_sub_total)
        sheet.write(row_start, 13, totals['others'], num_format_sub_total)

    # get employee mobile card excel
    def mobile_card_report(self, workbook):
        sheet = workbook.add_worksheet('Mobile Card')

        sheet.set_column('A:A', 8)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 10)
        sheet.set_column('D:D', 10)
        sheet.set_column('E:E', 20)

        row_start = 0

        date_format = workbook.add_format(
            {'num_format': 'mm/dd/yyyy', 'border': 7})
        num_format = workbook.add_format({'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 9})
        num_format_no = workbook.add_format({'num_format': '@', 'border': 1, 'font_name': 'Calibri', 'font_size': 9})

        title_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 9,
            'font_name': 'Calibri',
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})

        sheet.write(row_start, 0, 'No', title_format)
        sheet.write(row_start, 1, 'Name', title_format)
        sheet.write(row_start, 2, 'Total Price', title_format)
        sheet.write(row_start, 3, 'Phone No', title_format)
        sheet.write(row_start, 4, 'Analytical Account', title_format)
        row_start += 1

        # get employee list who have a benefit for mobile card
        mobile_cards = self.env['hr.payroll.payment.deduction'].search([('input_types.code', '=', 'MOBCAR')])

        no = 1  # counter
        for mobile_card in mobile_cards:
            sheet.write(row_start, 0, no, num_format_no)
            sheet.write(row_start, 1, mobile_card.employee_id.name, num_format)
            sheet.write(row_start, 2, mobile_card.amount, num_format)
            if mobile_card.employee_id.mobile_phone:
                sheet.write(row_start, 3, mobile_card.employee_id.mobile_phone, num_format_no)
            else:
                sheet.write(row_start, 3, ' ', num_format_no)
            if mobile_card.contract_id.analytic_account_id.name:
                sheet.write(row_start, 4, mobile_card.contract_id.analytic_account_id.name, num_format_no)
            else:
                sheet.write(row_start, 4, ' ', num_format_no)

            no += 1
            row_start += 1

    def company_vehicle_report(self, workbook):
        sheet = workbook.add_worksheet('Company Vehicle')

        sheet.set_column('A:A', 8)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 10)
        sheet.set_column('D:D', 10)
        sheet.set_column('E:E', 10)
        sheet.set_column('F:F', 10)
        sheet.set_column('G:G', 20)

        row_start = 0

        date_format = workbook.add_format(
            {'num_format': 'mm/dd/yyyy', 'border': 7})
        num_format = workbook.add_format({'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 9})
        num_format_no = workbook.add_format({'num_format': '@', 'border': 1, 'font_name': 'Calibri', 'font_size': 9})

        title_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 9,
            'font_name': 'Calibri',
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})

        sheet.write(row_start, 0, 'No', title_format)
        sheet.write(row_start, 1, 'Name', title_format)
        sheet.write(row_start, 2, 'Quantity', title_format)
        sheet.write(row_start, 3, 'Unit Price', title_format)
        sheet.write(row_start, 4, 'Total Price', title_format)
        sheet.write(row_start, 5, 'Phone No', title_format)
        sheet.write(row_start, 6, 'Analytical Account', title_format)
        row_start += 1

        # get employee list who have a benefit for fuel
        fules = self.env['hr.payroll.payment.deduction'].search([('input_types.code', '=', 'FUEL')])

        # get fuel rate
        fuel_rates = self.env['hr.payroll.rate'].search(
            [('code', '=', 'FUEL'), ('date_to', '>=', datetime.datetime.now())])

        rate = 0
        for fuel_rate in fuel_rates:
            rate = fuel_rate.rate

        no = 1  # counter
        for fuel in fules:
            sheet.write(row_start, 0, no, num_format_no)
            sheet.write(row_start, 1, fuel.employee_id.name, num_format)
            sheet.write(row_start, 2, fuel.amount, num_format)
            sheet.write(row_start, 3, rate, num_format)
            sheet.write(row_start, 4, rate * fuel.amount, num_format)
            if fuel.employee_id.mobile_phone:
                sheet.write(row_start, 5, fuel.employee_id.mobile_phone, num_format_no)
            else:
                sheet.write(row_start, 5, ' ', num_format_no)
            if fuel.contract_id.analytic_account_id.name:
                sheet.write(row_start, 6, fuel.contract_id.analytic_account_id.name, num_format_no)
            else:
                sheet.write(row_start, 6, ' ', num_format_no)

            no += 1
            row_start += 1

    def payroll_reconciliation_report(self, workbook):
        sheet = workbook.add_worksheet('Reconciliation')

        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 10)
        sheet.set_column('C:C', 30)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 20)

        row_start = 2

        date_format = workbook.add_format(
            {'num_format': 'mm/dd/yyyy', 'border': 7})
        num_format = workbook.add_format({'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 9})
        num_format_sub_total = workbook.add_format({'num_format': 43, 'border': 1, 'bold': 1})
        cent_format = workbook.add_format({'num_format': 41, 'border': 1})
        border = workbook.add_format({'border': 1, 'font_name': 'Calibri', 'font_size': 9})
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 22})
        main_title_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Calibri',
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
            'font_size': 9,
            'font_name': 'Calibri',
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})
        title_format_num = workbook.add_format({
            'bold': 1,
            'border': 1,
            'num_format': 43,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})

        sheet.merge_range('A1:G1', "Reconciliation - Net pay", main_title_format)
        sheet.merge_range('A2:G2', self.batch.name, main_title_format)

        sheet.write(row_start, 0, 'No', title_format)
        sheet.write(row_start, 1, 'ID No', title_format)
        sheet.write(row_start, 2, 'Employee Name', title_format)
        sheet.write(row_start, 3, 'Previous Month', title_format)
        sheet.write(row_start, 4, 'Current Month', title_format)
        sheet.write(row_start, 5, 'Difference', title_format)
        sheet.write(row_start, 6, 'Remark', title_format)
        row_start += 1

        # unique employee list
        emp_list = self.get_unique_employee_id()

        # search employees from hr.employee
        employees = self.env['hr.employee'].search([('id', 'in', emp_list)])
        # search based on cost center
        if self.cost_center_analytic.ids:
            slips = self.batch.slip_ids.search(
                [('contract_id.analytic_account_id', 'in', self.cost_center_analytic.ids),
                 ('period', '=', self.batch.period.id)])
        else:
            slips = self.batch.slip_ids

        current_period = self.batch.period
        previous_period = self.get_period()

        for record in slips:
            sheet.write(row_start, 0, row_start - 2, border)
            sheet.write(row_start, 1, record.employee_id.barcode, border)
            sheet.write(row_start, 2, record.employee_id.name, border)

            previous_net_wage = self.get_net_pay_amount(previous_period, record.employee_id.id)
            current_net_wage = self.get_net_pay_amount(current_period, record.employee_id.id)
            difference = previous_net_wage - current_net_wage

            sheet.write(row_start, 3, previous_net_wage, num_format)
            sheet.write(row_start, 4, current_net_wage, num_format)
            sheet.write(row_start, 5, difference, num_format)
            sheet.write(row_start, 6, '', border)

            row_start += 1

    def get_period(self):
        # get the last two items
        period = ''
        company_id = ''
        for record in self.batch:
            period_last = record.period.name[-2:]
            period_first = record.period.name[0:4]
            company_id = record.company_id.id

            period_last = int(period_last)
            period_first = int(period_first)

            if period_last == 1:
                period = str(period_first - 1) + str('12')
            else:
                period_last -= 1
                period = str(period_first) + "{0:0=2d}".format(period_last)

        periods = self.env['account.fiscal.year.period'].search(
            [('name', '=', period)])

        for x in periods:
            if x.fiscal_year_id.company_id.id == company_id:
                period = x

        return period

    # get unique employee id from two payroll periods
    def get_unique_employee_id(self):
        unique_employee_list = []
        # get current and previous period
        for record in self:
            current_period = record.batch.period
            previous_period = self.get_period()

        # get current period employee list
        current_period_employees = self.batch

        # get previous period employee list
        if hasattr(previous_period, 'id'):
            previous_period_employees = self.env['hr.payslip.run'].search([('period', '=', previous_period.id)])

            # add employee list from previous period
            for record in previous_period_employees.slip_ids.employee_id:
                unique_employee_list.append(record.id)

        for record in current_period_employees.slip_ids.employee_id:
            if record.id not in unique_employee_list:
                unique_employee_list.append(record.id)

        return unique_employee_list

    def get_net_pay_amount(self, period, emp_id):
        net_wage = 0
        if (hasattr(period, 'id')):
            batch = self.env['hr.payslip.run'].search([('period', '=', period.id)])

            for slips in batch.slip_ids:
                if slips.employee_id.id == emp_id:
                    net_wage += slips.net_wage

        return net_wage
