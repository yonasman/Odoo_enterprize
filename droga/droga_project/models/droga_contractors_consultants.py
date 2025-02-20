from odoo import models, fields, api


class droga_project_contractor(models.Model):
    _name = 'droga.project.contractors'

    _rec_name = "contractor_name"
    contractor_name = fields.Char("Contractor Name",required=True)
    contractor_descr = fields.Char("Contractor Description",required=True)
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')],required=True,default='Active')
    #company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    project_contracting = fields.Many2many('project.project', string='Projects')

class droga_project_consultant(models.Model):
    _name = 'droga.project.consultant'

    _rec_name = "consultant_name"
    consultant_name = fields.Char("Consultant Name",required=True)
    consultant_descr = fields.Char("Consultant Description",required=True)
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')],required=True,default='Active')
    #company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    project_consulting=fields.Many2many('project.project',string='Projects')

