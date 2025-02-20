from odoo import models, fields


class Employee(models.Model):
    _inherit = 'hr.employee'

    pos_device_ip_address = fields.Char("POS IP Address")
    pos_xml_folder = fields.Char("XML Folder Path", help="Folder path for XML")


class EmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    pos_device_ip_address = fields.Char("POS IP Address")
    pos_xml_folder = fields.Char("XML Folder Path", help="Folder path for XML")
