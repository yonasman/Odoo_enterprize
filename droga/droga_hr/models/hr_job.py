from odoo import models, fields, api


class HrJob(models.Model):
    _inherit = 'hr.job'

    salary_structure = fields.One2many("hr.job.salary", "job_id")
    job_grade = fields.Many2one("hr.job.grade")
    currency = fields.Many2one("res.currency", string="Currency")

    # _sql_constraints = [('name_unique', 'unique(name)', 'Job position must be unique')]


class HrJobSalary(models.Model):
    _name = 'hr.job.salary'

    job_id = fields.Many2one("hr.job")
    contract_id = fields.Many2one("hr.contract")
    name = fields.Char("Description", required=True)
    date_from = fields.Date("Date From")
    date_to = fields.Date("Date To")
    state = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')], default="Active",
                             required=True)
    salary_detail = fields.One2many("hr.job.salary.detail", "job_detail_id")
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 index=True, default=lambda self: self.env.company.id)
    currency = fields.Many2one("res.currency", string="Currency")


class HrJobSalaryDetail(models.Model):
    _name = 'hr.job.salary.detail'

    job_detail_id = fields.Many2one("hr.job.salary")
    payment_type = fields.Many2one("hr.job.salary.payment", required=True)
    date_from = fields.Date("Date From")
    date_to = fields.Date("Date To")
    amount = fields.Float("Amount", required=True)
    state = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')], default="Active",
                             required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 index=True, default=lambda self: self.env.company.id)


class HrJobSalaryPayment(models.Model):
    _name = 'hr.job.salary.payment'

    code = fields.Char("Code", required=True)
    name = fields.Char("Name", required=True)
    state = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')], default="Active",
                             required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 index=True, default=lambda self: self.env.company.id)

    _sql_constraints = [('code_unique', 'unique(code)', 'Code must be unique')]


class HrJobCrade(models.Model):
    _name = "hr.job.grade"

    name = fields.Char("Code", required=True)
    description = fields.Char("Description", required=True)
    state = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')], required=True, default='Active')
