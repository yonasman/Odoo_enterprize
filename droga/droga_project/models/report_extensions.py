from odoo import models,fields

class task_extension(models.Model):
    _inherit = 'project.task'
    project_name = fields.Char(related='project_id.name',store=True)
    stage_name=fields.Char(related='stage_id.name',store=True)
