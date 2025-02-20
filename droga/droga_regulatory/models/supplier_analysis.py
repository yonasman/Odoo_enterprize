from odoo import models, fields


class SupplierAnalysis(models.Model):
    _name = 'supplier.analysis'
    _description = 'Supplier Analysis'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string='Name', required=True)


    quality_rating = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('average', 'Average'),
        ('poor', 'Poor')
    ], string='Quality Rating', required=True)
    products = fields.Many2many('product.product', string='Products Offered')
    price_rating = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('average', 'Average'),
        ('poor', 'Poor')
    ], string='Price Rating', required=True)
    comments = fields.Text(string='Comments')

    grades = fields.One2many('droga.bdr.supplier.grade', 'supplier', string='Grades')

    sup_criteria_ids = fields.Many2many(
        comodel_name='supplier.comparison',
        relation='supplier_criteria_display',
        column1='new_rel',
        column2='new_rel2',
        compute='list_out'

    )
    def list_out(self):
        name = self.name
        criteria_model = self.env['supplier.comparison']
        self.sup_criteria_ids = criteria_model.search([('supplier', '=', name)])
        print('hello')



class SupplierGrade(models.Model):
    _name = 'droga.bdr.supplier.grade'
    _description = 'Supplier Grade'

    product = fields.Char(string='Products/Descriptions', required=True)
    criteria = fields.Char(string='Configration Name', required=True)
    score = fields.Float(string='Score')

    supplier = fields.Many2one('supplier.analysis')

    def update_score(self, sup, re):
        supplier = self.search([('request_no', '=', re)], limit=1)
        if supplier:
            supplier.status = 'reviewed'

