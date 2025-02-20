import base64
import calendar
import io

from odoo import api, fields, models
from io import BytesIO
import xlsxwriter
import datetime
from odoo.exceptions import UserError

try:
    from base64 import encodebytes
except ImportError:
    from base64 import encodestring as encodebytes


class crm_visit_plan_report(models.TransientModel):
    _name='droga.crm.reports.visit.log'

    visit=fields.Many2one('droga.customer.visit.header')
    week_num=fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')],string='Week number')

    fileout = fields.Binary('File', readonly=True)
    #fileout_filename = fields.Char('Filename', readonly=True)

    def action_get_xls(self):
        if not self.visit:
            raise UserError("Visit must be selected.")

        #This generates our excel file
        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)
        self.generate_xlsx_report(workbook)
        workbook.close()

        #The file to download will be stored under fileout field
        self.fileout = encodebytes(file_io.getvalue())
        file_io.close()

        #The file name is stored under filename
        datetime_string = self.env.cr.now().strftime("%Y%m%d_%H%M%S")
        filename = '%s%s_%s' % ('Visit plan for ',self.visit.descr, datetime_string)
        filename += '%2Exlsx'

        #This downloads file. The file is fileout and the name if filename
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + filename,
        }

    def generate_xlsx_report(self, workbook):
        sheet = workbook.add_worksheet('Visit plan')

        sheet.set_column('A:A', 15)
        sheet.set_column('B:B', 25)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 18)
        sheet.set_column('E:E', 17)
        sheet.set_column('F:F', 25)

        row_start=0
        date_format = workbook.add_format({'num_format': 'd mmm yyyy', 'border': 7})
        num_format = workbook.add_format({'num_format': 43, 'border': 7})
        cent_format = workbook.add_format({'num_format': 41, 'border': 7})
        border = workbook.add_format({'border': 7,'align': 'left'})
        center_middle_aligned_bold = workbook.add_format({'border': 7,'fg_color': '#F6F5F5','bold':1,'align': 'center',
            'valign': 'vcenter','text_wrap': True})
        center_middle_aligned = workbook.add_format(
            {'border': 7, 'align': 'left',
             'valign': 'vcenter', 'text_wrap': True})
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#d5d5dd',
            'font_size': 22})
        main_title_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 14})
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
        title_format_num= workbook.add_format({
            'bold': 1,
            'border': 1,
            'num_format': 43,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})

        if self.env.company.logo_web:
            company_image=io.BytesIO(base64.b64decode(self.env.company.logo_web))
            sheet.insert_image(0,5,"test_image.png",{'image_data':company_image,'y_scale':0.3})

        sheet.merge_range('A' + str(row_start + 1) + ':F' + str(row_start + 1), 'Droga Pharma P.L.C - CRM Activity plan', header_format)
        sheet.merge_range('B' + str(row_start + 2) + ':D' + str(row_start + 2), (str(self.visit.pr_sales.p_name) + ' : ' + self.visit.city_name.city_descr) if self.visit.city_name else str(self.visit.pr_sales.p_name),main_title_format)
        #sheet.merge_range('C' + str(row_start + 3) + ':C' + str(row_start + 3), 'Role...... ',main_title_format)

        descr=''
        childs=None
        if self.week_num:
            if self.week_num=='1':
                descr='Week 1: '+calendar.month_name[int(self.visit.month)]+' '+self.visit.wk1_from.strftime("%d")+'-'+self.visit.wk1_to.strftime("%d")+' / '+self.visit.wk1_to.strftime("%Y")
                childs=self.visit.week_1_domain
            elif self.week_num=='2':
                descr='Week 2: '+calendar.month_name[int(self.visit.month)]+' '+self.visit.wk2_from.strftime("%d")+'-'+self.visit.wk2_to.strftime("%d")+' / '+self.visit.wk2_to.strftime("%Y")
                childs = self.visit.week_2_domain
            elif self.week_num=='3':
                descr='Week 3: '+calendar.month_name[int(self.visit.month)]+' '+self.visit.wk3_from.strftime("%d")+'-'+self.visit.wk3_to.strftime("%d")+' / '+self.visit.wk3_to.strftime("%Y")
                childs = self.visit.week_3_domain
            elif self.week_num=='4':
                descr='Week 4: '+calendar.month_name[int(self.visit.month)]+' '+self.visit.wk4_from.strftime("%d")+'-'+self.visit.wk4_to.strftime("%d")+' / '+self.visit.wk4_to.strftime("%Y")
                childs = self.visit.week_4_domain
            elif self.week_num=='5' and not self.visit.wk5_from:
                descr='Week 5: '+calendar.month_name[int(self.visit.month)]+' '+self.visit.wk5_from.strftime("%d")+'-'+self.visit.wk5_to.strftime("%d")+' / '+self.visit.wk5_to.strftime("%Y")
                childs = self.visit.week_5_domain
            else:
                descr = 'There is no week 5.'
                childs = self.visit.week_5_domain
        else:
            descr='Month: '+calendar.month_name[int(self.visit.month)]+', '+self.visit.year
            childs = self.visit.plan_detail

        sheet.merge_range('B' + str(row_start + 3) + ':D' + str(row_start + 3), descr,main_title_format)

        sheet.write(row_start + 3, 0, 'Day',title_format)
        sheet.write(row_start + 3, 1, 'Customer', title_format)
        sheet.write(row_start + 3, 2, 'Session - area', title_format)
        sheet.write(row_start + 3, 3, 'Contact - products', title_format)
        sheet.write(row_start + 3, 4, 'Co-travel', title_format)
        sheet.write(row_start + 3, 5, 'Remark', title_format)
        row_start = 4

        dates=set(childs.filtered(lambda x: (x.visit_client or x.remark)).mapped('visit_date'))
        cur_date=None

        for rec in childs.filtered(lambda x: (x.visit_client or x.remark)).sorted(key=lambda r: r.visit_date):
            if not rec.visit_client and not rec.remark:
                continue

            if cur_date!=rec.visit_date:
                cur_date=rec.visit_date
                count=0
                for c in childs.filtered(lambda x: (x.visit_client or x.remark) and x.visit_date == rec.visit_date):
                    if len(c.contacts_schedule)==0:
                        count+=1
                    else:
                        count=count+len(c.contacts_schedule)
                if count>1:
                    sheet.merge_range('A' + str(row_start + 1) + ':A' + str(row_start + count),
                                      rec.day_and_date, center_middle_aligned_bold)
                else:
                    sheet.write(row_start, 0, rec.day_and_date, center_middle_aligned_bold)

            if len(rec.contacts_schedule)>1:
                sheet.merge_range('B' + str(row_start + 1) + ':B' + str(row_start + (len(rec.contacts_schedule) if len(rec.contacts_schedule)>0 else 1)),
                                  (rec.visit_client.name if rec.visit_client.name else '')+(' - '+rec.visit_client.area.area_name if rec.visit_client.area else ''), center_middle_aligned)
                sheet.merge_range('C' + str(row_start + 1) + ':C' + str(
                    row_start + (len(rec.contacts_schedule) if len(rec.contacts_schedule) > 0 else 1)),
                                  rec.planned_visit_selection, center_middle_aligned)
                sheet.merge_range('F' + str(row_start + 1) + ':F' + str(
                    row_start + (len(rec.contacts_schedule) if len(rec.contacts_schedule) > 0 else 1)),
                                  rec.remark if rec.remark else ' ', center_middle_aligned)
            else:
                sheet.write(row_start, 1, (rec.visit_client.name if rec.visit_client.name else '')+(' - '+rec.visit_client.area.area_name if rec.visit_client.area else ''), border)
                sheet.write(row_start, 2, rec.planned_visit_selection, border)
                sheet.write(row_start, 5, rec.remark if rec.remark else ' ', border)


            for cont in rec.contacts_schedule:
                sheet.write(row_start, 3, cont.contact_custom.descr if cont.contact_custom else '', border)
                if len(cont.co_travel_crm)>1:
                    name=''
                    for con in cont.co_travel_crm:
                        name=name+', '+con.name

                    sheet.write(row_start, 4, name[2:], num_format)
                else:
                    sheet.write(row_start, 4, cont.co_travel_crm.p_name if cont.co_travel_crm else '', num_format)
                row_start += 1
            if len(rec.contacts_schedule)==0:
                row_start += 1