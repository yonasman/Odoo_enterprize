from odoo import fields, models, api
from datetime import datetime, timedelta

from odoo.exceptions import UserError

class ModelName(models.Model):
    _name = 'droga.tender.specs.detail'
    spec_requested=fields.Char('Specification requested')
    spec_offered = fields.Char('Specification offered')
    bidder_compliance_remark=fields.Char('Bidder compliance remark',default='Comply')
    remark=fields.Char('Remark')
    submission_detail=fields.Many2one('droga.tender.submission.detail')
    parent_tender_submission=fields.Many2one('droga.tender.master',related='submission_detail.parent_tender_submission')
    group=fields.Char('Spec group')

