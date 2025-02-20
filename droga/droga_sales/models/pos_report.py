from odoo import models, fields, api


class PosReport(models.TransientModel):
    _name = 'droga.sales.pos.reports'

    report = fields.Selection([('printzdailysales', 'Prints a fiscal daily sales report (Z-Report)'),
                               ('printdailyclosing', 'Prints a fiscal daily closing report and clears the fiscal printer memory'),
                               ('printclerkreport', 'Prints a fiscal clerk report.'),
                               ('printxdailysales', 'Prints non fiscal x-daily sales report.'),
                               ('printzaccumulatedreport', 'Prints accumulated Z-Report'),
                               ('printxaccumulatedreport', 'Prints accumulated X-Report.'),
                               ('printfullfiscalreportbyz', 'Prints a full fiscal report for the specified Z range.'),
                               ('printfullfiscalreportbydate', 'Prints a full fiscal report for the specified date range.'),
                               ('printsummaryfiscalreportbyz', 'Prints a summary of fiscal report for the specified Z range.'),
                               ('printsummaryfiscalreportbydate', 'Prints a summary of fiscal report for the specified date range.'),
                               ])

    date_from = fields.Date("Date From")
    date_to = fields.Date("Date To")
    z_no_start = fields.Char("Z Number Start")
    z_no_end = fields.Char("Z Number End")
