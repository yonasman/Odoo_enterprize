from odoo import api, fields, models
from io import BytesIO
import xlsxwriter
import base64
import re


class ReportWizard(models.TransientModel):
    _name = "fleet.cost.report.wizard"
    _description = "Fleet cost Report"
    fileout = fields.Binary(string='File Output')


    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date')

    def action_get_xls(self,vehicle,domain):
        file_io = BytesIO()
        f_name = []

        file_name = "Fleet cost report"

        workbook = xlsxwriter.Workbook(file_io)
        self.generate_xls_report(workbook, vehicle,domain, file_name)
        workbook.close()

        self.fileout = base64.b64encode(file_io.getvalue())
        file_io.close()

        datetime_string = fields.Datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = file_name + f' From {self.date_from} to {self.date_to}.xlsx'

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': f'web/content/?model={self._name}&id={self.id}&field=fileout&download=true&filename={filename}'
        }

    def generate_xls_report(self, workbook, vehicle_searched,domain,title_name):

        sheet = workbook.add_worksheet('Fixed Monthly Costs')

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
        sheet.merge_range('A' + str(row_start + 1) + ':O' + str(row_start + 1), 'DROGA PHARMA P.L.C', header_format)
        sheet.merge_range('A' + str(row_start + 2) + ':O' + str(row_start + 2), title_name, main_title_format)
        sheet.merge_range('A' + str(row_start + 3) + ':G' + str(row_start + 7), 'Date from : ' + str(self.date_from),
                          parameter_format)
        sheet.merge_range('H' + str(row_start + 3) + ':O' + str(row_start + 7), 'Date to : ' + str(self.date_to),
                          parameter_format)

        # Set column widths

        sheet.set_column(0, 0, 15)  # vehicle plate
        sheet.set_column(1, 1, 15)  # fuel cost per quota
        sheet.set_column(2, 2, 20)  # rent

        sheet.set_column(4, 4, 15)  # Date of refuel
        sheet.set_column(5, 5, 15)  # cost of refuel
        sheet.set_column(6, 6, 15)  # Date of maintenance
        sheet.set_column(7, 7, 15)  # cost of maintenance

        sheet.set_column(7, 7, 20)  # Date of refuel
        sheet.set_column(8, 8, 20)  # cost of refuel
        sheet.set_column(9, 9, 20)  # Date of maintenance
        sheet.set_column(10, 10, 20)  # cost of maintenance





        row = 9
        col = 0
        sheet.write(row, col + 0, 'Vehicle Licence Plate', title_format)

        sheet.write(row, col + 1, 'Fuel cost Per Quota', title_format)
        sheet.write(row, col + 2, 'Monthly Rent', title_format)


        for vehicle in vehicle_searched:
            row = row + 1
            plate = str(vehicle.license_plate)
            rent = str(vehicle.rent_fee)
            fuel_quota = str(vehicle.fuel_consumption_per_quota)

            maintainance_fee = []


            sheet.write(row, col + 0, plate)
            sheet.write(row, col + 1, fuel_quota)
            sheet.write(row, col + 2, rent)

        total_monthly_cost=0
        total_monthly_fuel_quota_cost = 0
        total_monthly_rent_cost = 0
        for vehicle in vehicle_searched:
            total_monthly_cost = total_monthly_cost + vehicle.rent_fee + vehicle.fuel_consumption_per_quota

            total_monthly_fuel_quota_cost = total_monthly_fuel_quota_cost + vehicle.fuel_consumption_per_quota

            total_monthly_rent_cost = total_monthly_rent_cost + vehicle.rent_fee

        row = row + 2
        sheet.write(9, 7, 'Total Monthly Fuel Quota Cost', title_format)
        sheet.write(9 , 8, 'Total Monthly Rent Cost', title_format)
        sheet.write(9, 9, 'Total Monthly Cost', title_format)

        sheet.write(10, 7, str(total_monthly_fuel_quota_cost))
        sheet.write(10 ,8 , str(total_monthly_rent_cost))
        sheet.write(10 ,9, str(total_monthly_cost))




        sheet = workbook.add_worksheet('Fuel and Maintenance Costs')
        # set header
        row_start = 1
        sheet.set_row(row_start + 1, 30)
        sheet.merge_range('A' + str(row_start + 1) + ':O' + str(row_start + 1), 'DROGA PHARMA P.L.C', header_format)
        sheet.merge_range('A' + str(row_start + 2) + ':O' + str(row_start + 2), "Fuel And Maintenance Costs", main_title_format)
        sheet.merge_range('A' + str(row_start + 3) + ':G' + str(row_start + 7), 'Date from : ' + str(self.date_from),
                          parameter_format)
        sheet.merge_range('H' + str(row_start + 3) + ':O' + str(row_start + 7), 'Date to : ' + str(self.date_to),
                          parameter_format)

        # Set column widths

        sheet.set_column(0, 0, 15)  # vehicle plate
        sheet.set_column(1, 1, 15)  # type
        sheet.set_column(2, 2, 20)  # date
        sheet.set_column(4, 4, 15)  # cost

        sheet.set_column(1, 1, 15)  # total fuel
        sheet.set_column(2, 2, 20)  # total maintainance
        sheet.set_column(4, 4, 15)  # total cose

        sheet.set_column(7, 7, 20)  # Date of refuel
        sheet.set_column(8, 8, 20)  # cost of refuel
        sheet.set_column(9, 9, 20)  # Date of maintenance
        sheet.set_column(10, 10, 20)  # cost of maintenance


        row = 9
        col = 0
        sheet.write(row, col + 0, 'Vehicle Licence Plate', title_format)

        sheet.write(row, col + 1, 'Expense Type', title_format)
        sheet.write(row, col + 2, 'Date', title_format)
        sheet.write(row, col + 3, 'Cost', title_format)


        dmn = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),


        ]

        data = self.env['vehicle.maintenance.fee'].search(dmn)
        unique_vehicles = list(set(data.mapped('vehicle_id.license_plate')))




        total_maintenance_costs_by_license_plate = {}
        total_fuel_costs_by_license_plate = {}
        total_costs_by_license_plate = {}

        for license_plate in unique_vehicles:
            # Filter maintenance fees by license plate
            fees_for_license_plate = data.filtered(lambda fee: fee.vehicle_id.license_plate == license_plate)

            # Calculate total maintenance cost for the license plate
            total_maintenance_cost = sum(fee.cost for fee in fees_for_license_plate if fee.type == 'maintenance')
            total_maintenance_costs_by_license_plate[license_plate] = total_maintenance_cost

            # Calculate total fuel cost for the license plate
            total_fuel_cost = sum(fee.cost for fee in fees_for_license_plate if fee.type == 'fuel')
            total_fuel_costs_by_license_plate[license_plate] = total_fuel_cost

            # Calculate total cost for the license plate
            total_cost = sum(fees_for_license_plate.mapped('cost'))
            total_costs_by_license_plate[license_plate] = total_cost


        for vehicle in data:
            row = row + 1
            sheet.write(row, col + 0, vehicle.vehicle_id.license_plate)
            sheet.write(row, col + 1, vehicle.type)
            sheet.write(row, col + 2, str(vehicle.date))
            sheet.write(row, col + 3, vehicle.cost)

        row = row + 2

        rw = 9
        cl = 7
        sheet.write(rw , cl + 0, 'Vehicle License Plate', title_format)
        sheet.write(rw , cl + 1, 'Total Vehicle Maintenance Cost', title_format)
        sheet.write(rw , cl + 2, 'Total Vehicle Fuel Cost', title_format)
        sheet.write(rw, cl + 3, 'Total Vehicle Cost', title_format)

        for vehicle in unique_vehicles:
            rw = rw + 1
            sheet.write(rw, cl + 0, str(vehicle))
            sheet.write(rw, cl + 1, str(total_maintenance_costs_by_license_plate[vehicle]))
            sheet.write(rw, cl + 2, str(total_fuel_costs_by_license_plate[vehicle]))
            sheet.write(rw, cl + 3, str(total_costs_by_license_plate[vehicle]))

        # Calculate total maintenance costs of all license plates
        total_maintenance_costs_all = sum(total_maintenance_costs_by_license_plate.values())

        # Calculate total fuel costs of all license plates
        total_fuel_costs_all = sum(total_fuel_costs_by_license_plate.values())

        # Calculate total costs of all license plates
        total_costs_all = sum(total_costs_by_license_plate.values())

        sheet.write(9, 11 + 1 , 'Total Maintenance cost  ', title_format)
        sheet.write(9  ,12  + 1 , 'Total Fuel cost  ', title_format)
        sheet.write(9 , 13 + 1 , 'Total cost  ', title_format)

        sheet.write(10, 11 + 1 , str(total_maintenance_costs_all))
        sheet.write(10,12 + 1 , str(total_fuel_costs_all))
        sheet.write(10, 13 + 1 , str(total_costs_all))


    def action_wizard_print_excel_report(self):

        domain = [

        ]

        vehicle = self.env['fleet.vehicle'].search(domain)


        return self.action_get_xls(vehicle, domain )

    def action_cancel(self):

        return {'type': 'ir.actions.act_window_close'}
