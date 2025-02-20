from odoo import api, fields, models, tools
from io import BytesIO
import xlsxwriter
from datetime import datetime

from odoo.exceptions import UserError
from odoo.tools.sql import drop_view_if_exists

try:
    from base64 import encodebytes
except ImportError:
    from base64 import encodestring as encodebytes


class CustomerOutStandingBalanceReport(models.TransientModel):
    _name = 'droga.finance.customer.balance.excel.report'

    date = fields.Date("As of Date", required=True, default=datetime.today())
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 index=True, default=lambda self: self.env.company.id)

    fileout = fields.Binary('File', readonly=True)

    # This generates our Excel file
    file_io = BytesIO()
    workbook = xlsxwriter.Workbook(file_io)

    def generate_workbook(self):
        self.workbook = xlsxwriter.Workbook(self.file_io)

    def action_get_xls(self):
        # clear workbook

        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        records = self.env['droga.finance.customer.balance'].sudo().search([])

        self.cash_sales_by_costcenter(workbook, records)
        self.credit_sales_by_costcenter(workbook, records)
        self.cash_sale_by_channel(workbook, records)
        self.credit_sales_by_channel(workbook, records)
        self.cash_customer_balance(workbook, records)
        self.credit_customer_balance(workbook, records)
        self.total_customer_balance(workbook, records)

        self.cash_sales_by_customer_type(workbook, records)
        self.credit_sales_by_customer_type(workbook, records)
        workbook.close()

        # The file to download will be stored under fileout field
        self.fileout = encodebytes(file_io.getvalue())
        file_io.close()

        # The file name is stored under filename
        datetime_string = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = '%s_%s' % ('Customer Outstanding Balance', datetime_string)

        # This downloads file. The file is fileout and the name if filename
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + filename,
        }

    def cash_sales_by_costcenter(self, workbook, records):

        sheet = workbook.add_worksheet('Summary')

        num_format = workbook.add_format({'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 11})
        num_format_total = workbook.add_format(
            {'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 11, 'bold': True,
             'fg_color': '#F6F5F5'})
        main_title_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 16})
        title_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})

        sheet.set_column('A:A', 25)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 25)
        sheet.set_column('F:F', 25)
        sheet.set_column('G:G', 25)

        # get data
        import_division = records.search([('order_type', '=', 'IM'), ('sales_type', '=', 'Cash')])
        whole_sales = records.search([('order_type', '=', 'WS'), ('sales_type', '=', 'Cash')])
        no_branch = records.search([('order_type', 'not in', ('IM', 'WS')), ('sales_type', '=', 'Cash')])

        import_division_7_days = 0
        import_division_15_days = 0
        import_division_other_days = 0
        import_no_due_outstanding = 0

        wholesale_7_days = 0
        wholesale_15_days = 0
        wholesale_other_days = 0
        wholesale_no_due_outstanding = 0

        nobranch_7_days = 0
        nobranch_15_days = 0
        nobranch_other_days = 0
        nobranch_no_due_outstanding = 0

        for rec in import_division:
            if rec.date_diff < 0:
                import_no_due_outstanding += rec.amount_residual
            elif rec.date_diff <= 7:
                import_division_7_days += rec.amount_residual
            elif rec.date_diff <= 15:
                import_division_15_days += rec.amount_residual
            else:
                import_division_other_days += rec.amount_residual

        for rec in whole_sales:
            if rec.date_diff < 0:
                wholesale_no_due_outstanding += rec.amount_residual
            elif rec.date_diff <= 7:
                wholesale_7_days += rec.amount_residual
            elif rec.date_diff <= 15:
                wholesale_15_days += rec.amount_residual
            else:
                wholesale_other_days += rec.amount_residual

        for rec in no_branch:
            if rec.date_diff < 0:
                nobranch_no_due_outstanding += rec.amount_residual
            elif rec.date_diff <= 7:
                nobranch_7_days += rec.amount_residual
            elif rec.date_diff <= 15:
                nobranch_15_days += rec.amount_residual
            else:
                nobranch_other_days += rec.amount_residual

        import_division_total = import_division_7_days + import_division_15_days + import_division_other_days
        wholesale_total = wholesale_7_days + wholesale_15_days + wholesale_other_days
        no_branch_total = nobranch_7_days + nobranch_15_days + nobranch_other_days

        sheet.merge_range('A1:G1', self.company_id.name, main_title_format)
        sheet.merge_range('A2:G2', "Customers Outstanding Balance", main_title_format)
        sheet.merge_range('A3:G3', "As of " + str(self.date), main_title_format)

        sheet.merge_range('A4:G4', "Weekly Customers Outstanding Balance By Division", title_format)
        sheet.write(4, 0, 'Cash Sales', title_format)
        sheet.write(4, 1, '0-7 Days', title_format)
        sheet.write(4, 2, '7-15 Days', title_format)
        sheet.write(4, 3, ' > 15 Days ', title_format)
        sheet.write(4, 4, 'Outstanding With Due Date', title_format)
        sheet.write(4, 5, 'Outstanding With No Due Date', title_format)
        sheet.write(4, 6, 'Total', title_format)

        sheet.write(5, 0, 'Import Division', num_format)
        sheet.write(5, 1, import_division_7_days, num_format)
        sheet.write(5, 2, import_division_15_days, num_format)
        sheet.write(5, 3, import_division_other_days, num_format)
        sheet.write(5, 4, import_division_total, num_format)
        sheet.write(5, 5, import_no_due_outstanding, num_format)
        sheet.write_formula(5, 6, '=E6+F6', num_format)

        sheet.write(6, 0, 'Wholesale', num_format)
        sheet.write(6, 1, wholesale_7_days, num_format)
        sheet.write(6, 2, wholesale_15_days, num_format)
        sheet.write(6, 3, wholesale_other_days, num_format)
        sheet.write(6, 4, wholesale_total, num_format)
        sheet.write(6, 5, wholesale_no_due_outstanding, num_format)
        sheet.write_formula(6, 6, '=E7+F7', num_format)

        if no_branch.ids:
            sheet.write(7, 0, 'No Cost Center Old Data', num_format)
            sheet.write(7, 1, nobranch_7_days, num_format)
            sheet.write(7, 2, nobranch_15_days, num_format)
            sheet.write(7, 3, nobranch_other_days, num_format)
            sheet.write(7, 4, no_branch_total, num_format)
            sheet.write(7, 5, nobranch_no_due_outstanding, num_format)
            sheet.write_formula(7, 6, '=E8+F8', num_format)

        # sum total
        sheet.write_formula(8, 1, '=SUM(B6:B8)', num_format_total)
        sheet.write_formula(8, 2, '=SUM(C6:C8)', num_format_total)
        sheet.write_formula(8, 3, '=SUM(D6:D8)', num_format_total)
        sheet.write_formula(8, 4, '=SUM(E6:E8)', num_format_total)
        sheet.write_formula(8, 5, '=SUM(F6:F8)', num_format_total)
        sheet.write_formula(8, 6, '=E9+F9', num_format_total)

    def credit_sales_by_costcenter(self, workbook, records):
        sheet = workbook.get_worksheet_by_name("Summary")

        num_format = workbook.add_format({'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 11})
        num_format_total = workbook.add_format(
            {'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 11, 'bold': True,
             'fg_color': '#F6F5F5'})
        main_title_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 16})
        title_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})
        title_left_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})

        # get data
        import_division = records.search([('order_type', '=', 'IM'), ('sales_type', '=', 'Credit')])
        whole_sales = records.search([('order_type', '=', 'WS'), ('sales_type', '=', 'Credit')])
        no_branch = records.search([('order_type', 'not in', ('IM', 'WS')), ('sales_type', '=', 'Credit')])

        import_division_45_days = 0
        import_division_60_days = 0
        import_division_other_days = 0
        import_no_due_outstanding = 0

        wholesale_45_days = 0
        wholesale_60_days = 0
        wholesale_other_days = 0
        wholesale_no_due_outstanding = 0

        nobranch_45_days = 0
        nobranch_60_days = 0
        nobranch_other_days = 0
        nobranch_no_due_outstanding = 0

        for rec in import_division:
            if rec.date_diff < 0:
                import_no_due_outstanding += rec.amount_residual
            elif rec.date_diff <= 45:
                import_division_45_days += rec.amount_residual
            elif rec.date_diff <= 60:
                import_division_60_days += rec.amount_residual
            else:
                import_division_other_days += rec.amount_residual

        for rec in whole_sales:
            if rec.date_diff < 0:
                wholesale_no_due_outstanding += rec.amount_residual
            elif rec.date_diff <= 45:
                wholesale_45_days += rec.amount_residual
            elif rec.date_diff <= 60:
                wholesale_60_days += rec.amount_residual
            else:
                wholesale_other_days += rec.amount_residual

        for rec in no_branch:
            if rec.date_diff < 0:
                nobranch_no_due_outstanding += rec.amount_residual
            elif rec.date_diff <= 45:
                nobranch_45_days += rec.amount_residual
            elif rec.date_diff <= 60:
                nobranch_60_days += rec.amount_residual
            else:
                nobranch_other_days += rec.amount_residual

        import_division_total = import_division_45_days + import_division_60_days + import_division_other_days
        wholesale_total = wholesale_45_days + wholesale_60_days + wholesale_other_days
        no_branch_total = nobranch_45_days + nobranch_60_days + nobranch_other_days

        sheet.write(11, 0, 'Credit Sales', title_format)
        sheet.write(11, 1, '0-45 Days', title_format)
        sheet.write(11, 2, '46-60 Days', title_format)
        sheet.write(11, 3, ' > 60 Days ', title_format)
        sheet.write(11, 4, 'Outstanding With Due Date', title_format)
        sheet.write(11, 5, 'Outstanding With No Due Date', title_format)
        sheet.write(11, 6, 'Total', title_format)

        sheet.write(12, 0, 'Import Division', num_format)
        sheet.write(12, 1, import_division_45_days, num_format)
        sheet.write(12, 2, import_division_60_days, num_format)
        sheet.write(12, 3, import_division_other_days, num_format)
        sheet.write(12, 4, import_division_total, num_format)
        sheet.write(12, 5, import_no_due_outstanding, num_format)
        sheet.write_formula(12, 6, "=E13+F13", num_format)

        sheet.write(13, 0, 'Wholesale', num_format)
        sheet.write(13, 1, wholesale_45_days, num_format)
        sheet.write(13, 2, wholesale_60_days, num_format)
        sheet.write(13, 3, wholesale_other_days, num_format)
        sheet.write(13, 4, wholesale_total, num_format)
        sheet.write(13, 5, wholesale_no_due_outstanding, num_format)
        sheet.write_formula(13, 6, "=E14+F14", num_format)

        if no_branch.ids:
            sheet.write(14, 0, 'No Cost Center Old Data', num_format)
            sheet.write(14, 1, nobranch_45_days, num_format)
            sheet.write(14, 2, nobranch_60_days, num_format)
            sheet.write(14, 3, nobranch_other_days, num_format)
            sheet.write(14, 4, no_branch_total, num_format)
            sheet.write(14, 5, nobranch_no_due_outstanding, num_format)
            sheet.write_formula(14, 6, "=E15+F15", num_format)

        # sum total
        sheet.write_formula(15, 1, '=SUM(B13:B15)', num_format_total)
        sheet.write_formula(15, 2, '=SUM(C13:C15)', num_format_total)
        sheet.write_formula(15, 3, '=SUM(D13:D15)', num_format_total)
        sheet.write_formula(15, 4, '=SUM(E13:E15)', num_format_total)
        sheet.write_formula(15, 5, '=SUM(F13:F15)', num_format_total)
        sheet.write_formula(15, 6, "=E16+F16", num_format_total)

        sheet.merge_range('A18:D18', "Import Division Customers Outstanding Balance", title_format)
        sheet.write_formula(17, 4, "=E6+E13", num_format_total)
        sheet.write_formula(17, 5, "=F6+F13", num_format_total)
        sheet.write_formula(17, 6, "=G6+G13", num_format_total)

        sheet.merge_range('A19:D19', "Wholesales Division Customers Outstanding Balance", title_format)
        sheet.write_formula(18, 4, "=E7+E14", num_format_total)
        sheet.write_formula(18, 5, "=F7+F14", num_format_total)
        sheet.write_formula(18, 6, "=G7+G14", num_format_total)

        sheet.merge_range('A20:D20', "No Cost Center Customers Outstanding Balance", title_format)
        sheet.write_formula(19, 4, "=E8+E15", num_format_total)
        sheet.write_formula(19, 5, "=F8+F15", num_format_total)
        sheet.write_formula(19, 6, "=G8+G15", num_format_total)

        sheet.merge_range('A21:D21', "Grand Total", title_format)
        sheet.write_formula(20, 4, "=E18+E19+E20", num_format_total)
        sheet.write_formula(20, 5, "=F18+F19+F20", num_format_total)
        sheet.write_formula(20, 6, "=G18+G19+G20", num_format_total)

    def cash_sales_by_customer_type(self, workbook, records):

        sheet = workbook.get_worksheet_by_name('Summary')

        num_format = workbook.add_format({'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 11})
        num_format_total = workbook.add_format(
            {'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 11, 'bold': True,
             'fg_color': '#F6F5F5'})
        main_title_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 16})
        title_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})

        sheet.set_column('A:A', 25)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 20)

        # get data

        cust_types = records.search([('sales_type', '=', 'Cash')])

        government_45_days = 0
        government_60_days = 0
        government_other_days = 0
        government_no_due_outstanding = 0

        ngo_45_days = 0
        ngo_60_days = 0
        ngo_other_days = 0
        ngo_no_due_outstanding = 0

        private_45_days = 0
        private_60_days = 0
        private_other_days = 0
        private_no_due_outstanding = 0

        others_45_days = 0
        others_60_days = 0
        others_other_days = 0
        others_no_due_outstanding = 0

        for rec in cust_types:
            if rec.partner_id.cust_type_ext.cust_org_type == "Government":
                if rec.date_diff < 0:
                    government_no_due_outstanding += rec.amount_residual
                elif rec.date_diff <= 7:
                    government_45_days += rec.amount_residual
                elif rec.date_diff <= 15:
                    government_60_days += rec.amount_residual
                else:
                    government_other_days += rec.amount_residual

            elif rec.partner_id.cust_type_ext.cust_org_type == "NGO":
                if rec.date_diff < 0:
                    ngo_no_due_outstanding += rec.amount_residual
                elif rec.date_diff <= 7:
                    ngo_45_days += rec.amount_residual
                elif rec.date_diff <= 15:
                    ngo_60_days += rec.amount_residual
                else:
                    ngo_other_days += rec.amount_residual

            elif rec.partner_id.cust_type_ext.cust_org_type == "Private":
                if rec.date_diff < 0:
                    private_no_due_outstanding += rec.amount_residual
                elif rec.date_diff <= 7:
                    private_45_days += rec.amount_residual
                elif rec.date_diff <= 15:
                    private_60_days += rec.amount_residual
                else:
                    private_other_days += rec.amount_residual
            else:
                if rec.date_diff < 0:
                    others_no_due_outstanding += rec.amount_residual
                elif rec.date_diff <= 7:
                    others_45_days += rec.amount_residual
                elif rec.date_diff <= 15:
                    others_60_days += rec.amount_residual
                else:
                    others_other_days += rec.amount_residual

        import_division_total = government_45_days + government_60_days + government_other_days
        wholesale_total = ngo_45_days + ngo_60_days + ngo_other_days
        no_branch_total = private_45_days + private_60_days + private_other_days
        others_total = others_45_days + others_60_days + others_other_days

        sheet.merge_range('A40:G40', "Weekly Customers Outstanding Balance By Customer Type", title_format)
        sheet.write(41, 0, 'Cash Sales', title_format)
        sheet.write(41, 1, '0-7 Days', title_format)
        sheet.write(41, 2, '7-15 Days', title_format)
        sheet.write(41, 3, ' > 15 Days ', title_format)
        sheet.write(41, 4, 'Outstanding With Due Date', title_format)
        sheet.write(41, 5, 'Outstanding With No Due Date', title_format)
        sheet.write(41, 6, 'Total', title_format)

        sheet.write(42, 0, 'Government', num_format)
        sheet.write(42, 1, government_45_days, num_format)
        sheet.write(42, 2, government_60_days, num_format)
        sheet.write(42, 3, government_other_days, num_format)
        sheet.write(42, 4, import_division_total, num_format)
        sheet.write(42, 5, government_no_due_outstanding, num_format)
        sheet.write_formula(42, 6, '=E43+F43', num_format)

        sheet.write(43, 0, 'Ngo', num_format)
        sheet.write(43, 1, ngo_45_days, num_format)
        sheet.write(43, 2, ngo_60_days, num_format)
        sheet.write(43, 3, ngo_other_days, num_format)
        sheet.write(43, 4, wholesale_total, num_format)
        sheet.write(43, 5, government_no_due_outstanding, num_format)
        sheet.write_formula(43, 6, '=E44+F44', num_format)

        sheet.write(44, 0, 'Private', num_format)
        sheet.write(44, 1, private_45_days, num_format)
        sheet.write(44, 2, private_60_days, num_format)
        sheet.write(44, 3, private_other_days, num_format)
        sheet.write(44, 4, no_branch_total, num_format)
        sheet.write(44, 5, government_no_due_outstanding, num_format)
        sheet.write_formula(44, 6, '=E45+F45', num_format)

        sheet.write(45, 0, 'Others', num_format)
        sheet.write(45, 1, others_45_days, num_format)
        sheet.write(45, 2, others_60_days, num_format)
        sheet.write(45, 3, others_other_days, num_format)
        sheet.write(45, 4, others_total, num_format)
        sheet.write(45, 5, government_no_due_outstanding, num_format)
        sheet.write_formula(45, 6, '=E46+F46', num_format)

        # sum total
        sheet.write_formula(46, 1, '=SUM(B41:B46)', num_format_total)
        sheet.write_formula(46, 2, '=SUM(C41:C46)', num_format_total)
        sheet.write_formula(46, 3, '=SUM(D41:D46)', num_format_total)
        sheet.write_formula(46, 4, '=SUM(E41:E46)', num_format_total)
        sheet.write_formula(46, 5, '=SUM(F41:F46)', num_format_total)
        sheet.write_formula(46, 6, '=SUM(G41:G46)', num_format_total)

    def credit_sales_by_customer_type(self, workbook, records):

        sheet = workbook.get_worksheet_by_name('Summary')

        num_format = workbook.add_format({'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 11})
        num_format_total = workbook.add_format(
            {'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 11, 'bold': True,
             'fg_color': '#F6F5F5'})
        main_title_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 16})
        title_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})

        sheet.set_column('A:A', 25)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 20)

        # get data

        cust_types = records.search([('sales_type', '=', 'Credit')])
        ngo = records.search([('sales_type', '=', 'Credit')])
        private = records.search([('sales_type', '=', 'Credit')])

        government_45_days = 0
        government_60_days = 0
        government_other_days = 0
        government_no_due_outstanding = 0

        ngo_45_days = 0
        ngo_60_days = 0
        ngo_other_days = 0
        ngo_no_due_outstanding = 0

        private_45_days = 0
        private_60_days = 0
        private_other_days = 0
        private_no_due_outstanding = 0

        others_45_days = 0
        others_60_days = 0
        others_other_days = 0
        others_no_due_outstanding = 0

        for rec in cust_types:
            if rec.partner_id.cust_type_ext.cust_org_type == "Government":
                if rec.date_diff < 0:
                    government_no_due_outstanding += rec.amount_residual
                elif rec.date_diff <= 45:
                    government_45_days += rec.amount_residual
                elif rec.date_diff <= 60:
                    government_60_days += rec.amount_residual
                else:
                    government_other_days += rec.amount_residual

            elif rec.partner_id.cust_type_ext.cust_org_type == "NGO":
                if rec.date_diff < 0:
                    ngo_no_due_outstanding += rec.amount_residual
                elif rec.date_diff <= 45:
                    ngo_45_days += rec.amount_residual
                elif rec.date_diff <= 60:
                    ngo_60_days += rec.amount_residual
                else:
                    ngo_other_days += rec.amount_residual

            elif rec.partner_id.cust_type_ext.cust_org_type == "Private":
                if rec.date_diff < 0:
                    private_no_due_outstanding += rec.amount_residual
                elif rec.date_diff <= 45:
                    private_45_days += rec.amount_residual
                elif rec.date_diff <= 60:
                    private_60_days += rec.amount_residual
                else:
                    private_other_days += rec.amount_residual
            else:
                if rec.date_diff < 0:
                    others_no_due_outstanding += rec.amount_residual
                elif rec.date_diff <= 45:
                    others_45_days += rec.amount_residual
                elif rec.date_diff <= 60:
                    others_60_days += rec.amount_residual
                else:
                    others_other_days += rec.amount_residual

        import_division_total = government_45_days + government_60_days + government_other_days
        wholesale_total = ngo_45_days + ngo_60_days + ngo_other_days
        no_branch_total = private_45_days + private_60_days + private_other_days
        others_total = others_45_days + others_60_days + others_other_days

        sheet.write(49, 0, 'Credit Sales', title_format)
        sheet.write(49, 1, '0-45 Days', title_format)
        sheet.write(49, 2, '46-60 Days', title_format)
        sheet.write(49, 3, ' > 60 Days ', title_format)
        sheet.write(49, 4, 'Outstanding With Due Date', title_format)
        sheet.write(49, 5, 'Outstanding With No Due Date', title_format)
        sheet.write(49, 6, 'Total', title_format)

        sheet.write(50, 0, 'Government', num_format)
        sheet.write(50, 1, government_45_days, num_format)
        sheet.write(50, 2, government_60_days, num_format)
        sheet.write(50, 3, government_other_days, num_format)
        sheet.write(50, 4, import_division_total, num_format)
        sheet.write(50, 5, government_no_due_outstanding, num_format)
        sheet.write_formula(50, 6, '=E51+F51', num_format)

        sheet.write(51, 0, 'Ngo', num_format)
        sheet.write(51, 1, ngo_45_days, num_format)
        sheet.write(51, 2, ngo_60_days, num_format)
        sheet.write(51, 3, ngo_other_days, num_format)
        sheet.write(51, 4, wholesale_total, num_format)
        sheet.write(51, 5, ngo_no_due_outstanding, num_format)
        sheet.write_formula(51, 6, '=E52+F52', num_format)

        sheet.write(52, 0, 'Private', num_format)
        sheet.write(52, 1, private_45_days, num_format)
        sheet.write(52, 2, private_60_days, num_format)
        sheet.write(52, 3, private_other_days, num_format)
        sheet.write(52, 4, no_branch_total, num_format)
        sheet.write(52, 5, private_no_due_outstanding, num_format)
        sheet.write_formula(52, 6, '=E53+F53', num_format)

        sheet.write(53, 0, 'Others', num_format)
        sheet.write(53, 1, others_45_days, num_format)
        sheet.write(53, 2, others_60_days, num_format)
        sheet.write(53, 3, others_other_days, num_format)
        sheet.write(53, 4, others_total, num_format)
        sheet.write(53, 5, others_no_due_outstanding, num_format)
        sheet.write_formula(53, 6, '=E54+F54', num_format)

        # sum total
        sheet.write_formula(54, 1, '=SUM(B49:B54)', num_format_total)
        sheet.write_formula(54, 2, '=SUM(C49:C54)', num_format_total)
        sheet.write_formula(54, 3, '=SUM(D49:D54)', num_format_total)
        sheet.write_formula(54, 4, '=SUM(E49:E54)', num_format_total)
        sheet.write_formula(54, 4, '=SUM(F49:F54)', num_format_total)
        sheet.write_formula(54, 4, '=SUM(G49:G54)', num_format_total)

        sheet.merge_range('A55:D55', "Total Government Organization Sales Outstanding Balance", title_format)
        sheet.write_formula(54, 4, "=E43+E51", num_format_total)
        sheet.write_formula(54, 5, "=F43+F51", num_format_total)
        sheet.write_formula(54, 6, "=G43+G51", num_format_total)

        sheet.merge_range('A56:D56', "Total NGO Organization Sales Outstanding Balance", title_format)
        sheet.write_formula(55, 4, "=E44+E52", num_format_total)
        sheet.write_formula(55, 5, "=F44+F52", num_format_total)
        sheet.write_formula(55, 6, "=G44+G52", num_format_total)

        sheet.merge_range('A57:D57', "Total Private Organization Sales Outstanding Balance", title_format)
        sheet.write_formula(56, 4, "=E45+E53", num_format_total)
        sheet.write_formula(56, 5, "=F45+F53", num_format_total)
        sheet.write_formula(56, 6, "=G45+G53", num_format_total)

        sheet.merge_range('A58:D58', "Total Other Organization Sales Outstanding Balance", title_format)
        sheet.write_formula(57, 4, "=E46+E54", num_format_total)
        sheet.write_formula(57, 5, "=F46+F54", num_format_total)
        sheet.write_formula(57, 6, "=G46+G54", num_format_total)

        sheet.merge_range('A59:D59', "Grand Total", title_format)
        sheet.write_formula(58, 4, "=E55+E56+E57+E58", num_format_total)
        sheet.write_formula(58, 5, "=F55+F56+F57+F58", num_format_total)
        sheet.write_formula(58, 6, "=G55+G56+G57+G58", num_format_total)

    def cash_sale_by_channel(self, workbook, records):
        sheet = workbook.get_worksheet_by_name('Summary')

        num_format = workbook.add_format({'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 11})
        num_format_total = workbook.add_format(
            {'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 11, 'bold': True,
             'fg_color': '#F6F5F5'})
        main_title_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 16})
        title_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})
        title_left_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})

        # get data
        tender = records.search([('sales_channel', '=', 'Tender'), ('sales_type', '=', 'Cash')])
        marketing = records.search([('sales_channel', '=', 'Marketing'), ('sales_type', '=', 'Cash')])
        no_branch = records.search([('sales_channel', 'not in', ('Tender', 'Marketing')), ('sales_type', '=', 'Cash')])

        marketing_7_days = 0
        marketing_15_days = 0
        marketing_other_days = 0
        marketing_no_due_outstanding = 0

        tender_7_days = 0
        tender_15_days = 0
        tender_other_days = 0
        tender_no_due_outstanding = 0

        nobranch_7_days = 0
        nobranch_15_days = 0
        nobranch_other_days = 0
        nobranch_no_due_outstanding = 0

        for rec in marketing:
            if rec.date_diff < 0:
                marketing_no_due_outstanding += rec.amount_residual
            elif rec.date_diff <= 7:
                marketing_7_days += rec.amount_residual
            elif rec.date_diff <= 15:
                marketing_15_days += rec.amount_residual
            else:
                marketing_other_days += rec.amount_residual

        for rec in tender:
            if rec.date_diff < 0:
                tender_no_due_outstanding += rec.amount_residual
            elif rec.date_diff <= 7:
                tender_7_days += rec.amount_residual
            elif rec.date_diff <= 15:
                tender_15_days += rec.amount_residual
            else:
                tender_other_days += rec.amount_residual

        for rec in no_branch:
            if rec.date_diff < 0:
                nobranch_no_due_outstanding += rec.amount_residual
            elif rec.date_diff <= 7:
                nobranch_7_days += rec.amount_residual
            elif rec.date_diff <= 15:
                nobranch_15_days += rec.amount_residual
            else:
                nobranch_other_days += rec.amount_residual

        marketing_total = marketing_7_days + marketing_15_days + marketing_other_days
        tender_total = tender_7_days + tender_15_days + tender_other_days
        no_branch_total = nobranch_7_days + nobranch_15_days + nobranch_other_days

        sheet.merge_range('A23:G23', "Weekly Customers Outstanding Balance Sales Channel", title_format)
        sheet.write(24, 0, 'Cash Sales', title_format)
        sheet.write(24, 1, '0-7 Days', title_format)
        sheet.write(24, 2, '7-15 Days', title_format)
        sheet.write(24, 3, ' > 15 Days ', title_format)
        sheet.write(24, 4, 'Outstanding With Due Date', title_format)
        sheet.write(24, 5, 'Outstanding With No Due Date', title_format)
        sheet.write(24, 6, 'Total', title_format)

        sheet.write(25, 0, 'Marketing', num_format)
        sheet.write(25, 1, marketing_7_days, num_format)
        sheet.write(25, 2, marketing_15_days, num_format)
        sheet.write(25, 3, marketing_other_days, num_format)
        sheet.write(25, 4, marketing_total, num_format)
        sheet.write(25, 5, marketing_no_due_outstanding, num_format)
        sheet.write_formula(25, 6, '=E26+F26', num_format)

        sheet.write(26, 0, 'Tender', num_format)
        sheet.write(26, 1, tender_7_days, num_format)
        sheet.write(26, 2, tender_15_days, num_format)
        sheet.write(26, 3, tender_other_days, num_format)
        sheet.write(26, 4, tender_total, num_format)
        sheet.write(26, 5, tender_no_due_outstanding, num_format)
        sheet.write_formula(26, 6, '=E27+F27', num_format)

        """if no_branch.ids:
            sheet.write(26, 0, 'No Sales Channel Old Data', self.num_format)
            sheet.write(26, 1, nobranch_7_days, self.num_format)
            sheet.write(26, 2, nobranch_15_days, self.num_format)
            sheet.write(26, 3, nobranch_other_days, self.num_format)
            sheet.write(26, 4, no_branch_total, self.num_format)"""

        # sum total
        sheet.write_formula(27, 1, '=SUM(B26:B27)', num_format_total)
        sheet.write_formula(27, 2, '=SUM(C26:C27)', num_format_total)
        sheet.write_formula(27, 3, '=SUM(D26:D27)', num_format_total)
        sheet.write_formula(27, 4, '=SUM(E26:E27)', num_format_total)
        sheet.write_formula(27, 5, '=SUM(F26:F27)', num_format_total)
        sheet.write_formula(27, 6, '=SUM(G26:G27)', num_format_total)

    def credit_sales_by_channel(self, workbook, records):
        sheet = workbook.get_worksheet_by_name("Summary")

        num_format = workbook.add_format({'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 11})
        num_format_total = workbook.add_format(
            {'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 11, 'bold': True,
             'fg_color': '#F6F5F5'})
        main_title_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 16})
        title_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})
        title_left_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})

        # get data
        tender = records.search([('sales_channel', '=', 'Tender'), ('sales_type', '=', 'Credit')])
        marketing = records.search([('sales_channel', '=', 'Marketing'), ('sales_type', '=', 'Credit')])
        no_branch = records.search(
            [('sales_channel', 'not in', ('Tender', 'Marketing')), ('sales_type', '=', 'Credit')])

        marketing_45_days = 0
        marketing_60_days = 0
        marketing_other_days = 0
        marketing_no_due_outstanding = 0

        tender_45_days = 0
        tender_60_days = 0
        tender_other_days = 0
        tender_no_due_outstanding = 0

        nobranch_45_days = 0
        nobranch_60_days = 0
        nobranch_other_days = 0
        nobranch_no_due_outstanding = 0

        for rec in marketing:
            if rec.date_diff < 0:
                marketing_no_due_outstanding += rec.amount_residual
            elif rec.date_diff <= 45:
                marketing_45_days += rec.amount_residual
            elif rec.date_diff <= 60:
                marketing_60_days += rec.amount_residual
            else:
                marketing_other_days += rec.amount_residual

        for rec in tender:
            if rec.date_diff < 0:
                tender_no_due_outstanding += rec.amount_residual
            elif rec.date_diff <= 45:
                tender_45_days += rec.amount_residual
            elif rec.date_diff <= 60:
                tender_60_days += rec.amount_residual
            else:
                tender_other_days += rec.amount_residual

        for rec in no_branch:
            if rec.date_diff < 0:
                nobranch_no_due_outstanding += rec.amount_residual
            elif rec.date_diff <= 45:
                nobranch_45_days += rec.amount_residual
            elif rec.date_diff <= 60:
                nobranch_60_days += rec.amount_residual
            else:
                nobranch_other_days += rec.amount_residual

        import_division_total = marketing_45_days + marketing_60_days + marketing_other_days
        wholesale_total = tender_45_days + tender_60_days + tender_other_days
        no_branch_total = nobranch_45_days + nobranch_60_days + nobranch_other_days

        sheet.write(30, 0, 'Credit Sales', title_format)
        sheet.write(30, 1, '0-45 Days', title_format)
        sheet.write(30, 2, '46-60 Days', title_format)
        sheet.write(30, 3, ' > 60 Days ', title_format)
        sheet.write(30, 4, 'Outstanding With Due Date', title_format)
        sheet.write(30, 5, 'Outstanding With No Due Date', title_format)
        sheet.write(30, 6, 'Total', title_format)

        sheet.write(31, 0, 'Marketing', num_format)
        sheet.write(31, 1, marketing_45_days, num_format)
        sheet.write(31, 2, marketing_60_days, num_format)
        sheet.write(31, 3, marketing_other_days, num_format)
        sheet.write(31, 4, import_division_total, num_format)
        sheet.write(31, 5, marketing_no_due_outstanding, num_format)
        sheet.write_formula(31, 6, '=E32+F32', num_format)

        sheet.write(32, 0, 'Tender', num_format)
        sheet.write(32, 1, tender_45_days, num_format)
        sheet.write(32, 2, tender_60_days, num_format)
        sheet.write(32, 3, tender_other_days, num_format)
        sheet.write(32, 4, wholesale_total, num_format)
        sheet.write(32, 5, tender_no_due_outstanding, num_format)
        sheet.write_formula(32, 6, '=E33+F33', num_format)

        # sum total
        sheet.write_formula(33, 1, '=SUM(B32:B33)', num_format_total)
        sheet.write_formula(33, 2, '=SUM(C32:C33)', num_format_total)
        sheet.write_formula(33, 3, '=SUM(D32:D33)', num_format_total)
        sheet.write_formula(33, 4, '=SUM(E32:E33)', num_format_total)
        sheet.write_formula(33, 5, '=SUM(F32:F33)', num_format_total)
        sheet.write_formula(33, 6, '=SUM(G32:G33)', num_format_total)

        sheet.merge_range('A36:D36', "Total Marketing Sales Outstanding Balance", title_format)
        sheet.write_formula(35, 4, "=E26+E32", num_format_total)
        sheet.write_formula(35, 5, "=F26+F32", num_format_total)
        sheet.write_formula(35, 6, "=G26+G32", num_format_total)

        sheet.merge_range('A37:D37', "Total Tender Sales Outstanding Balance", title_format)
        sheet.write_formula(36, 4, "=E27+E33", num_format_total)
        sheet.write_formula(36, 5, "=F27+F33", num_format_total)
        sheet.write_formula(36, 6, "=G27+G33", num_format_total)

        sheet.merge_range('A38:D38', "Grand Total", title_format)
        sheet.write_formula(37, 4, "=E36+E37", num_format_total)
        sheet.write_formula(37, 5, "=F36+F37", num_format_total)
        sheet.write_formula(37, 6, "=G36+G37", num_format_total)

    def cash_customer_balance(self, workbook, records):
        sheet = workbook.add_worksheet('Cash Customer Balance')

        num_format = workbook.add_format({'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 11})
        num_format_total = workbook.add_format(
            {'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 11, 'bold': True,
             'fg_color': '#F6F5F5'})
        main_title_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 16})
        title_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})
        title_left_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})

        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 45)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 20)
        sheet.set_column('E:E', 20)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 20)

        sheet.merge_range('A1:E1', self.company_id.name, main_title_format)
        sheet.merge_range('A2:E2', "As of " + str(self.date), main_title_format)

        row_start = 3

        sheet.write(row_start, 0, 'No', title_format)
        sheet.write(row_start, 1, 'Customer Name', title_format)
        sheet.write(row_start, 2, '0-7 Days', title_format)
        sheet.write(row_start, 3, '7-15 Days', title_format)
        sheet.write(row_start, 4, '>15 Days', title_format)
        sheet.write(row_start, 5, 'Total', title_format)
        sheet.write(row_start, 6, 'Responsible Person', title_format)
        sheet.write(row_start, 7, 'Remark', title_format)
        row_start += 1

        # get data
        records = records.search([('sales_type', '=', 'Cash')])

        partner_ids = []

        total7 = 0
        total15 = 0
        totalother = 0

        for cash in records:
            if cash.partner_id.id not in partner_ids and cash.partner_id.id:
                days7 = self.get_remaining_amount_by_days(cash.partner_id.id, 0, 7, 'Cash')
                days15 = self.get_remaining_amount_by_days(cash.partner_id.id, 8, 15, 'Cash')
                days_other = self.get_remaining_amount_by_days(cash.partner_id.id, 16, 10000000000000, 'Cash')

                if days7 + days15 + days_other != 0:
                    total7 += days7
                    total15 += days15
                    totalother += days_other

                    sheet.write(row_start, 0, row_start - 3, title_format)
                    sheet.write(row_start, 1, cash.partner_id.name, title_left_format)

                    # get amount
                    sheet.write(row_start, 2, days7, num_format)
                    sheet.write(row_start, 3, days15, num_format)
                    sheet.write(row_start, 4, days_other, num_format)
                    sheet.write(row_start, 5, days7 + days15 + days_other, num_format)
                    if cash.order_type == 'WS':
                        sheet.write(row_start, 6, "Wholesale", num_format)
                    elif cash.order_type == 'IM':
                        sheet.write(row_start, 6, "Import", num_format)
                    else:
                        sheet.write(row_start, 6, "No Data", num_format)

                    sheet.write(row_start, 7, "", num_format)
                    partner_ids.append(cash.partner_id.id)
                    row_start += 1

        sheet.write(row_start, 1, 'Total', title_format)
        sheet.write(row_start, 2, total7, num_format_total)
        sheet.write(row_start, 3, total15, num_format_total)
        sheet.write(row_start, 4, totalother, num_format_total)
        sheet.write(row_start, 5, total7 + total15 + totalother, num_format_total)

    def credit_customer_balance(self, workbook, records):
        sheet = workbook.add_worksheet('Credit Customer Balance')

        num_format = workbook.add_format({'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 11})
        num_format_total = workbook.add_format(
            {'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 11, 'bold': True,
             'fg_color': '#F6F5F5'})
        main_title_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 16})
        title_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})
        title_left_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})

        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 45)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 20)
        sheet.set_column('E:E', 20)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 20)
        sheet.set_column('H:H', 20)
        sheet.set_column('I:I', 20)

        sheet.merge_range('A1:E1', self.company_id.name, main_title_format)
        sheet.merge_range('A2:E2', "As of " + str(self.date), main_title_format)

        row_start = 3

        sheet.write(row_start, 0, 'No', title_format)
        sheet.write(row_start, 1, 'Customer Name', title_format)
        sheet.write(row_start, 2, '0-45 Days', title_format)
        sheet.write(row_start, 3, '45-60 Days', title_format)
        sheet.write(row_start, 4, '>60 Days', title_format)
        sheet.write(row_start, 5, 'Outstanding With Due Date', title_format)
        sheet.write(row_start, 6, 'Outstanding With No Due Date', title_format)
        sheet.write(row_start, 7, 'Total', title_format)
        sheet.write(row_start, 8, 'Responsible Person', title_format)
        sheet.write(row_start, 9, 'Remark', title_format)
        row_start += 1

        # get data
        records = records.search([('sales_type', '=', 'Credit')])

        partner_ids = []

        total7 = 0
        total15 = 0
        totalother = 0
        total_no_due_days_amount = 0

        for cash in records:
            if cash.partner_id.id not in partner_ids and cash.partner_id.id:
                days7 = self.get_remaining_amount_by_days(cash.partner_id.id, 0, 45, "Credit")
                days15 = self.get_remaining_amount_by_days(cash.partner_id.id, 46, 60, "Credit")
                days_other = self.get_remaining_amount_by_days(cash.partner_id.id, 61, 10000000000000, "Credit")
                no_due_days_amount = self.get_remaining_amount_with_no_due_date(cash.partner_id.id, "Credit")

                if days7 + days15 + days_other + no_due_days_amount != 0:
                    total7 += days7
                    total15 += days15
                    totalother += days_other
                    total_no_due_days_amount += no_due_days_amount

                    sheet.write(row_start, 0, row_start - 3, title_format)
                    sheet.write(row_start, 1, cash.partner_id.name, title_left_format)

                    # get amount
                    sheet.write(row_start, 2, days7, num_format)
                    sheet.write(row_start, 3, days15, num_format)
                    sheet.write(row_start, 4, days_other, num_format)

                    sheet.write(row_start, 5, days7 + days15 + days_other, num_format)
                    sheet.write(row_start, 6, no_due_days_amount, num_format)

                    sheet.write(row_start, 7, days7 + days15 + days_other + no_due_days_amount, num_format)
                    if cash.order_type == 'WS':
                        sheet.write(row_start, 8, "Wholesale", num_format)
                    elif cash.order_type == 'IM':
                        sheet.write(row_start, 8, "Import", num_format)
                    else:
                        sheet.write(row_start, 8, "No Data", num_format)

                    sheet.write(row_start, 9, "", num_format)
                    partner_ids.append(cash.partner_id.id)
                    row_start += 1

        sheet.write(row_start, 1, 'Total', title_format)
        sheet.write(row_start, 2, total7, num_format_total)
        sheet.write(row_start, 3, total15, num_format_total)
        sheet.write(row_start, 4, totalother, num_format_total)
        sheet.write(row_start, 5, total7 + total15 + totalother, num_format_total)
        sheet.write(row_start, 6, total_no_due_days_amount, num_format_total)
        sheet.write(row_start, 7, total7 + total15 + totalother + total_no_due_days_amount, num_format_total)

    def total_customer_balance(self, workbook, records):
        sheet = workbook.add_worksheet('Total Customer Balance')

        num_format = workbook.add_format({'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 11})
        num_format_total = workbook.add_format(
            {'num_format': 43, 'border': 1, 'font_name': 'Calibri', 'font_size': 11, 'bold': True,
             'fg_color': '#F6F5F5'})
        main_title_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 16})
        title_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})
        title_left_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})

        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 45)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 20)
        sheet.set_column('E:E', 20)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 20)
        sheet.set_column('H:H', 20)
        sheet.set_column('I:I', 20)

        sheet.merge_range('A1:E1', self.company_id.name, main_title_format)
        sheet.merge_range('A2:E2', "As of " + str(self.date), main_title_format)

        row_start = 3

        sheet.write(row_start, 0, 'No', title_format)
        sheet.write(row_start, 1, 'Customer Name', title_format)
        sheet.write(row_start, 2, '0-45 Days', title_format)
        sheet.write(row_start, 3, '45-60 Days', title_format)
        sheet.write(row_start, 4, '>60 Days', title_format)
        sheet.write(row_start, 5, 'Outstanding With Due Date', title_format)
        sheet.write(row_start, 6, 'Outstanding With No Due Date', title_format)
        sheet.write(row_start, 7, 'Total', title_format)
        sheet.write(row_start, 8, 'Responsible Person', title_format)
        sheet.write(row_start, 9, 'Remark', title_format)
        row_start += 1

        # get data
        # records = records.search([])

        partner_ids = []

        total7 = 0
        total15 = 0
        totalother = 0
        total_no_due_days_amount = 0

        for cash in records:
            if cash.partner_id.id not in partner_ids and cash.partner_id.id:
                days7 = self.get_remaining_amount_by_days(cash.partner_id.id, 0, 45, "")
                days15 = self.get_remaining_amount_by_days(cash.partner_id.id, 46, 60, "")
                days_other = self.get_remaining_amount_by_days(cash.partner_id.id, 61, 10000000000000, "")
                no_due_days_amount = self.get_remaining_amount_with_no_due_date(cash.partner_id.id, "")

                if days7 + days15 + days_other + total_no_due_days_amount != 0:
                    total7 += days7
                    total15 += days15
                    totalother += days_other
                    total_no_due_days_amount += no_due_days_amount

                    sheet.write(row_start, 0, row_start - 3, title_format)
                    sheet.write(row_start, 1, cash.partner_id.name, title_left_format)

                    # get amount
                    sheet.write(row_start, 2, days7, num_format)
                    sheet.write(row_start, 3, days15, num_format)
                    sheet.write(row_start, 4, days_other, num_format)

                    sheet.write(row_start, 5, days7 + days15 + days_other, num_format)
                    sheet.write(row_start, 6, no_due_days_amount, num_format)

                    sheet.write(row_start, 7, days7 + days15 + days_other + no_due_days_amount, num_format)
                    if cash.order_type == 'WS':
                        sheet.write(row_start, 8, "Wholesale", num_format)
                    elif cash.order_type == 'IM':
                        sheet.write(row_start, 8, "Import", num_format)
                    else:
                        sheet.write(row_start, 8, "No Data", num_format)

                    sheet.write(row_start, 9, "", num_format)
                    partner_ids.append(cash.partner_id.id)
                    row_start += 1

        sheet.write(row_start, 1, 'Total', title_format)
        sheet.write(row_start, 2, total7, num_format_total)
        sheet.write(row_start, 3, total15, num_format_total)
        sheet.write(row_start, 4, totalother, num_format_total)
        sheet.write(row_start, 5, total7 + total15 + totalother, num_format_total)
        sheet.write(row_start, 6, total_no_due_days_amount, num_format_total)
        sheet.write(row_start, 7, total7 + total15 + totalother + total_no_due_days_amount, num_format_total)

    def get_remaining_amount_by_days(self, customer_id, min_date, max_date, sales_type):
        if sales_type == "":
            self.env.cr.execute(
                """ select coalesce(sum(amount_residual),0) as amt from droga_finance_customer_balance where  date_diff between %s and %s and partner_id=%s """,
                (min_date, max_date, customer_id))
            amount = self.env.cr.dictfetchall()
            return amount[0]['amt']

        self.env.cr.execute(
            """ select coalesce(sum(amount_residual),0) as amt from droga_finance_customer_balance where sales_type=%s and date_diff between %s and %s and partner_id=%s """,
            (sales_type, min_date, max_date, customer_id))
        amount = self.env.cr.dictfetchall()
        return amount[0]['amt']

    def get_remaining_amount_with_no_due_date(self, customer_id, sales_type):
        if sales_type == "":
            self.env.cr.execute(
                """ select coalesce(sum(amount_residual),0) as amt from droga_finance_customer_balance where  date_diff<0  and partner_id=%s """ %
                (customer_id))
            amount = self.env.cr.dictfetchall()
            return amount[0]['amt']

        self.env.cr.execute(
            """ select coalesce(sum(amount_residual),0) as amt from droga_finance_customer_balance where sales_type=%s and date_diff < 0 and partner_id=%s """,
            (sales_type, customer_id))
        amount = self.env.cr.dictfetchall()
        return amount[0]['amt']


class CustomerOutStandingBalanceQuery(models.Model):
    _name = 'droga.finance.customer.balance'
    _auto = False
    _order = 'partner_id'

    id = fields.Integer('Id')
    invoice_id = fields.Char("Number")
    partner_id = fields.Many2one("res.partner")
    cust_org_type = fields.Char("Customer Category")
    sales_type = fields.Char("Sales Type")
    order_type = fields.Selection([('IM', 'Import'), ('WS', 'Wholesale'), ('PT', 'Physiotherapy')])
    sales_channel = fields.Char("Sales Channel")
    sales_initiator = fields.Char("Sales Person", compute="_get_sales_person")
    invoice_date_due = fields.Date("Due Date")
    date_diff = fields.Integer("Passed Days")
    amount_residual = fields.Float("Remaining Amount")
    amount_total = fields.Float("Total Amount")

    def update_credit_limit(self):
        records = self.env['account.move'].search([('create_uid', '=', 2), ('move_type', '=', 'out_invoice')])

        for rec in records:
            delta = rec.invoice_date_due - rec.invoice_date

            if delta.days == 0:  # cash
                rec.invoice_payment_term_id = 12
            elif delta.days <= 15:
                rec.invoice_payment_term_id = 2
            elif delta.days <= 30:
                rec.invoice_payment_term_id = 4
            elif delta.days <= 45:
                rec.invoice_payment_term_id = 5
            elif delta.days <= 60:
                rec.invoice_payment_term_id = 6
            elif delta.days <= 179:
                rec.invoice_payment_term_id = 13
            else:
                rec.invoice_payment_term_id = 14

    def _get_sales_person(self):
        self.sales_initiator = ''
        for record in self:
            # search sales order
            sale_order = self.env["sale.order"].sudo().search([('name', '=', record.invoice_id)])
            for order in sale_order:
                record.sales_initiator = order.sales_initiator

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'droga_finance_customer_balance')
        self.env.cr.execute("""
                   create or replace view droga_finance_customer_balance as (

                         select  row_number() over () as id,a.name as invoice_id,a.partner_id,COALESCE(ct.cust_org_type,'Others') as cust_org_type,a.sales_type,COALESCE(s.order_type,'Others') as order_type,
                        CASE
                          WHEN s.tender_origin_form_tender IS NULL Then 'Marketing'
                          WHEN s.tender_origin_form_tender IS not NULL Then'Tender'
                          ELSE 'Data Not Found'
                         END AS sales_channel,'' as sales_initiator,
                        a.invoice_date_due,CURRENT_DATE-a.invoice_date_due as date_diff,a.amount_residual,a.amount_total_signed as amount_total
                        from account_move a left join sale_order s on a.invoice_origin=s.name
                        left join res_partner r on r.id=a.partner_id left join droga_cust_type ct on ct.id=r.cust_type_ext

                        where a.payment_state in('not_paid','partial')
                        and a.move_type in('out_invoice') and amount_residual!=0  and a.partner_id is not null  and a.state in('posted')    
                   )""")
