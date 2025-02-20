from odoo import models, fields, api
from odoo.exceptions import UserError


class ProjectProgressWizard(models.TransientModel):
    _name = 'droga.project.progress.wizard'
    _description = 'Droga Project Progress Report Wizard'

    project_id = fields.Many2one('project.project', string="Project", required=True)

    def action_generate_xlsx_report(self):
        """Trigger the XLSX report generation for the selected project"""

        if not self.project_id:
            raise UserError("Please select a project before generating the report.")

        return self.env.ref('droga_project_reports.action_droga_project_progress_xlsx').report_action(self, data={
            'project_id': self.project_id.id})
