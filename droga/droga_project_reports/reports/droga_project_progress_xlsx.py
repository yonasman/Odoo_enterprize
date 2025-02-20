from odoo import models
from odoo.addons.report_xlsx.report.report_abstract_xlsx import ReportXlsxAbstract
from odoo.exceptions import UserError


class DrogaProjectXlsxReport(ReportXlsxAbstract):
    _name = 'report.droga_project_reports.project_report_xlsx'

    def generate_xlsx_report(self, workbook, data, objs):
        """Generate XLSX Report for the selected project"""

        # Fetch the selected project
        project_id = data.get('project_id')
        if not project_id:
            raise UserError("No project ID provided.")

        project = self.env['project.project'].browse(project_id)

        if not project.exists():
            raise UserError(f"Project with ID {project_id} not found.")

        # Create XLSX Sheet
        sheet = workbook.add_worksheet('Project Progress')

        # Formatting for headers and sheet content
        top_header_format = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 25})
        sec_header_format = workbook.add_format({'bold': True, 'font_size': 16})
        third_header_format = workbook.add_format({'font_size': 12, 'bold': True})

        # Set row and column dimensions
        sheet.set_row(0, 80)
        sheet.set_column(0, 7, 18)

        # Define Column Headers
        headers = ['Parent Task', 'Task', 'Task Progress', 'Date From', 'Date To', 'Number of Days', 'Predecessor Task',
                   'Responsible']
        for col, header in enumerate(headers):
            sheet.write(2, col, header, third_header_format)

        # Write project name as top header
        sheet.merge_range(0, 0, 0, 7, project.name, top_header_format)

        # Check if the project has tasks
        if not project.task_ids:
            raise UserError(f"No tasks found for project {project.name}")

        row = 3
        for task in project.task_ids[::-1]:
            print(f"Processing Task: {task.name}")

            # Write task information
            sheet.merge_range(1, 0, 1, 7, f'{task.stage_name} - {task.task_progress} % completed', sec_header_format)
            sheet.write(row, 0, task.parent_id.name if task.parent_id else 'N/A')
            sheet.write(row, 1, task.name)
            sheet.write(row, 2, f'{task.task_progress}%' or '0%')
            sheet.write(row, 3, str(task.planned_date_begin) if task.planned_date_begin else 'N/A')
            sheet.write(row, 4, str(task.planned_date_end) if task.planned_date_end else 'N/A')
            sheet.write(row, 5, task.task_duration if task.task_duration else 0)
            sheet.write(row, 6, ', '.join(task.predecessors.mapped('name')) if task.predecessors else 'N/A')
            sheet.write(row, 7, ', '.join(task.user_ids.mapped('name')) if task.user_ids else 'N/A')
            row += 1
