from datetime import datetime

from odoo import models, fields, api

class droga_project_version_extension(models.Model):
    _inherit = 'project.project'
    version=fields.One2many('project.scope.version','project')

    def project_versions(self):
        return {
            'name': 'Project scopes',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'project.scope.version',
            'views': [[self.env.ref('droga_project.view_project_project_tree').id, 'tree'],
                      [self.env.ref('droga_project.view_project_project_form').id, 'form']],
            'type': 'ir.actions.act_window',
            'context': {
                'default_project': self.id,
            },
            'domain': [('project', '=', self.id)],
        }
class droga_project_introduction(models.Model):
    _name = 'project.scope.version'
    _rec_name = 'version_no'

    version_date=fields.Date('Version date',default=datetime.today())
    version_no=fields.Char('Version no')

    project = fields.Many2one('project.project')
    name=fields.Char(related='project.name')
    objectives_data = fields.One2many('project.objectives', 'project_obj')
    deliverables_data = fields.One2many('project.deliverables', 'project_del')
    constraints_data = fields.One2many('project.constraints', 'project_constraints')
    task_data = fields.One2many('project.tasks.scope', 'project_tasks')
    out_of_scope_data = fields.One2many('project.out.of.scope', 'project_out_of_scope')
    assumption_data = fields.One2many('project.assumption', 'project_assumption')
    approval_data = fields.One2many('project.approval', 'project_approvals')

    intro_text = fields.Html(string='Introduction')

    @api.model
    def create(self, vals):
        res = super(droga_project_introduction, self).create(vals)
        vals.update({'version_no': 'Version : '+str(res.id)})
        res.version_no='Version : '+str(len(res.project.version.ids))
        return res

class objectives_data(models.Model):
    _name = 'project.objectives'

    obj = fields.Char(string='Project Objectives')
    project_obj = fields.Many2one('project.scope.version')

class deliverables_data(models.Model):
    _name = 'project.deliverables'

    capacity = fields.Char(string='Production Capacity')
    remark = fields.Char(string='Remark')
    deliverables = fields.Char(string='Project Deliverables')
    project_del = fields.Many2one('project.scope.version')

class constraints_data(models.Model):
    _name = 'project.constraints'

    type=fields.Selection([('Time', 'Time'), ('Cost', 'Cost'),('Scope','Scope')],required=True)
    descr=fields.Html('Description')
    project_start_date = fields.Date(string='Project Start Date')
    launch = fields.Date(string='Launch/ Go Live Date')
    project_end_date = fields.Date(string='Project End Date')
    project_constraints = fields.Many2one('project.scope.version')

class task_data(models.Model):
    _name = 'project.tasks.scope'

    tasks = fields.Char(string='Project Tasks')
    project_tasks = fields.Many2one('project.scope.version')

class out_of_scope_data(models.Model):
    _name = 'project.out.of.scope'

    out_of_scope = fields.Char(string='Out Of Scope')
    descr = fields.Html(string='Description')
    project_out_of_scope = fields.Many2one('project.scope.version')

class assumption_data(models.Model):
    _name = 'project.assumption'

    desc = fields.Html(string='Description')
    assumption = fields.Html(string='Project Assumptions')
    project_assumption = fields.Many2one('project.scope.version')

class approval_data(models.Model):
    _name = 'project.approval'

    stake_holder = fields.Char(string='StakeHolder Name and Title')
    role = fields.Html(string='Role of The StakeHolder')
    date_submitted = fields.Date(string='Date Submitted For Approval')
    date_received = fields.Date(string='Date Approval Received')
    project_approvals = fields.Many2one('project.scope.version')

