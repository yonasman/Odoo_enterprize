from odoo import models, fields

class droga_grading_header(models.Model):
    _name = "droga.grading.model.header"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _rec_name = 'header'

    header = fields.Char(string='Grading model')
    grading_detail = fields.One2many('droga.grading.model.detail', 'grading_header')

    def delete_record(self):
        self.unlink()


class droga_grading_detail(models.Model):
    _name = "droga.grading.model.detail"

    grading_header=fields.Many2one('droga.grading.model.header')
    header = fields.Char(related='grading_header.header', required=True)

    from_score = fields.Float("From Score")
    to_score = fields.Float("To Score")
    label = fields.Selection(selection=[('green', 'Green'), ('blue', 'Blue'), ('yellow', 'Yellow'), ('red', 'Red')])


    def delete_record(self):
        self.unlink()

class droga_grading_detail(models.Model):
    _name = "droga.grading.model"



