from odoo import models, fields, api


class droga_job_position(models.Model):
    _name='droga.cust.job.position'
    _rec_name = "job_position"
    job_position=fields.Char('Job Position')
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')], required=True,default='Active')
