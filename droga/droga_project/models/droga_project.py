from odoo import fields, models, api
from odoo.exceptions import UserError

class drogaProject(models.Model):
    _inherit = 'project.project'

    parent_project = fields.Many2one('project.project')
    project_progress = fields.Float(compute="_project_progress")
    stages_sum=fields.Char('Stages sum',compute='_project_progress')
    warehouses=fields.Many2many('stock.warehouse',tracking=True, domain=[
        ('wh_type', '=', 'PR')])
    project_forman = fields.Many2one('res.users',tracking=True)
    project_engineer = fields.Many2one('res.users',tracking=True)
    contractors=fields.Many2many('droga.project.contractors',string='Contractors')
    consultants = fields.Many2many('droga.project.consultant',string='Consultants')

    def _project_progress(self):
        for record in self:
            record.ensure_one()
            record.project_progress =0
            record.stages_sum=''
            sta_sum=0
            task_list = record.env['project.task.type'].search([('project_ids', '=', record.id)])
            for rec in task_list:
                record.project_progress += (rec.task_stage_progress * rec.task_stage_weight) / 100
                sta_sum += rec.task_stage_weight
            record.stages_sum=str(sta_sum)

    @api.model
    def create(self, vals):
        res=super(drogaProject, self).create(vals)
        self.env['project.task.type'].create({
            'name': 'Initiation',
            'sequence': 1,
            'from_project_auto':True,
            'project_ids': [res.id],
            'fold': False,
        })
        self.env['project.task.type'].create({
            'name': 'Planning',
            'sequence': 2,
            'from_project_auto': True,
            'project_ids': [res.id],
            'fold': False,
        })
        self.env['project.task.type'].create({
            'name': 'Execution',
            'sequence': 3,
            'from_project_auto': True,
            'project_ids': [res.id],
            'fold': False,
        })
        self.env['project.task.type'].create({
            'name': 'Closing',
            'sequence': 4,
            'from_project_auto': True,
            'project_ids': [res.id],
            'fold': False,
        })
        return res

    def write(self, vals):
        res= super(drogaProject, self).write(vals)
        if 'type_ids' in vals:
            sum=0
            count=0
            for type_id in self.type_ids:
                count+=1
                sum+=type_id.task_stage_weight

            if count!=4:
                raise UserError("You can not delete a stage manually.")
            if sum!=100:
                raise UserError("Sum of stages weight should equal 100.")

        return res

    def proj_tasks(self):
        return {
            'name': 'Tasks',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'project.task',
            'view_id': self.env.ref('droga_project.droga_report_tasks_list_tree').id,
            'type': 'ir.actions.act_window',
            #'target': 'new',
            'res_id': self.id,
            'context': {
                'default_project_id': self.id,
            }
        }

    def proj_scopes(self):
        return {
            'name': 'Scopes',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'project.scope.version',
            'view_id': self.env.ref('droga_project.view_project_project_tree').id,
            'type': 'ir.actions.act_window',
            # 'target': 'new',
            'res_id': self.id,
            'context': {
                'default_project': self.id,
            }
        }