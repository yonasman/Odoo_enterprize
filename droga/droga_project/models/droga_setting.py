from odoo import models, fields


class DrogaSetting(models.TransientModel):
    _inherit = "res.config.settings"
    task_weight = fields.Boolean("Task Weight", default=True)
    stage_weight = fields.Boolean("Stage Weight", default=True)

    def set_stage_weight(self):
        return {
            'name': 'Set Stage Weight',
            'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'project.task.type',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }
