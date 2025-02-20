from odoo import models, fields, api
from odoo.exceptions import UserError
import uuid


class droga_prod_analysis(models.Model):
    _name = "droga.bdr.product.analysis"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    analysis_no = fields.Char('Analysis number', readonly=True)
    product_descr=fields.Char('Product description')
    product_grade=fields.Char('Product Grade')
    criterias = fields.One2many('droga.bdr.product.analysis.criterias','product_analysis')
    score_out_of_hundred=fields.Float('Score /100')
    config_name = fields.Many2one('droga.bdr.analysis.criteria.header', string="Product Configuration",
    domain=[('type', '=', 'product')])
    grade_name = fields.Many2one('droga.grading.model.header', string="Grading model Name")
    req = fields.Many2many('droga.bdr.requests.header')
    exb_num = fields.Many2many('droga.reg.company.info')
    sup = fields.Many2many('supplier.analysis')
    sup_config_name = fields.Many2one('droga.bdr.analysis.criteria.header', string="Supplier Configration",
    domain=[('type', '=', 'supplier')])

    def generate_unique_sequence(self):
        id_exists = True
        while id_exists:
            new_id = uuid.uuid4()
            new_id = str(new_id).replace('-', '')
            existing_record = self.env['supplier.comparison'].search([('unique_id', '=', new_id)])
            if not existing_record:
                id_exists = False
        return new_id

    criteria_ids = fields.Many2many(
        comodel_name='droga.bdr.analysis.criteria',
        relation='product_criteria_rel',
        column1='product_id',
        column2='criteria_id',
        default=lambda self: self._default_criteria_ids(),

    )
    sup_criteria_ids = fields.Many2many(
        comodel_name='supplier.comparison',
        relation='supplier_criteria_rel',
        column1='product_id',
        column2='criteria_id',
        default=lambda self: self._sup_default_criteria_ids(),

    )
    def _sup_default_criteria_ids(self):
        criteria_model = self.env['droga.bdr.analysis.criteria']
        criteria = criteria_model.search([('header', '=', self.sup_config_name.header)])

        id = self.generate_unique_sequence()

        merge =[]
        if self.product_descr:
            merge.append(str(self.product_descr))

        for request in self.req:
            merge.append(str(request.request_no))
        for exb in self.exb_num:
            merge.append(str(exb.reg_num))
        result = ', '.join(merge)
        result = str(result)

        for supplier in self.sup:
            for cri in criteria:
                comparison = self.env['supplier.comparison'].create({
                                    'supplier': supplier.name,
                                    'criteria': cri.criteria,
                                    'min_val':cri.minimum_score,
                                    'prod_list':result,
                                    'score':cri.minimum_score,
                                    'max_val': cri.maximum_score,
                                    'weight': cri.weight,
                                    'unique_id': id,
                                 })

        criteria_model = self.env['supplier.comparison']
        self.sup_criteria_ids = criteria_model.search([('unique_id', '=', id)])

    def _default_criteria_ids(self):
        criteria_model = self.env['droga.bdr.analysis.criteria']
        self.criteria_ids = criteria_model.search([('header', '=', self.config_name.header)])

    grade_ids = fields.Many2many(
        comodel_name='droga.grading.model.detail',
        relation='grade_model_rel',
        column1='product_id',
        column2='grade_id',
        default=lambda self: self._default_grade_ids(),

    )



    def _default_grade_ids(self):
        grade_model = self.env['droga.grading.model.detail']
        self.grade_ids = grade_model.search([('header', '=', self.grade_name.header)])

    def _change_color(self, score):
        if self.grade_ids:
            for grade in self.grade_ids:
                if score >= grade.from_score and score <= grade.to_score:
                    self.product_grade = grade.label
                    self.write({'product_grade': self.product_grade})
                    break

    @api.onchange("config_name")
    def _onchange_config(self):
        self._default_criteria_ids()

    @api.onchange("sup")
    def _onchange_supplier(self):
        self._sup_default_criteria_ids()

    @api.onchange("sup_config_name")
    def _onchange_supplier_2(self):
        self._sup_default_criteria_ids()

    @api.onchange("grade_name")
    def _onchange_grade(self):
        self._default_grade_ids()

    # @api.model
    # def create(self, vals_list):
    #     vals_list['analysis_no'] = self.env['ir.sequence'].next_by_code(
    #         'droga.reg.prod.analysis.custom.sequence')
    #     if not vals_list['analysis_no']:
    #         raise UserError("Sequence not found.")
    #
    #     #add criterias
    #     return super().create(vals_list)

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('droga.reg.prod.analysis.custom.sequence')

        vals['analysis_no'] = sequence
        return super(droga_prod_analysis, self).create(vals)

    def calculate_score(self):
        if self.criteria_ids:
            score = 0

            for criteria in self.criteria_ids:
                if criteria.score < criteria.minimum_score or criteria.score > criteria.maximum_score:
                    raise UserError('Invalid Range!')
                else:
                    normalized_score = (criteria.score - criteria.minimum_score) / (criteria.maximum_score - criteria.minimum_score)
                    score += (criteria.weight * normalized_score)
            self.score_out_of_hundred = score
            self.write({'score_out_of_hundred': self.score_out_of_hundred})
        else:
            self.score_out_of_hundred = 0
            self.write({'score_out_of_hundred': self.score_out_of_hundred})

    def supplier_score(self):
        if self.sup_criteria_ids:
            current_name_group = None
            score_dict = {}

            for supplier in self.sup_criteria_ids:
                if current_name_group is None or supplier.supplier != current_name_group:
                    current_name_group = supplier.supplier
                    score_dict[current_name_group] = 0

                if supplier.score >= supplier.min_val and supplier.score <= supplier.max_val:
                    normalized_score = (supplier.score - supplier.min_val) / (
                            supplier.max_val - supplier.min_val)
                    score_dict[current_name_group] += (supplier.weight * normalized_score)
                else:
                    raise UserError('Invalid Range')

            for supplier in self.sup_criteria_ids:
                supplier.total_score = score_dict[supplier.supplier]

    @api.constrains('req', 'exb_num', 'sup', 'grade_name', 'criteria_ids')
    def fin_analysis(self):
        req_no = []
        exb_num = []
        sup_name=[]

        for request in self.req:
            req_no.append(str(request.request_no))
        for exb in self.exb_num:
            exb_num.append(str(exb.reg_num))
        for supp in self.sup:
            sup_name.append(str(supp.name))


        for req in req_no:
            self.env['droga.bdr.requests.header'].update_request_status(req)

        for supplier in sup_name:
            for config in self.sup_config_name:
                for req in req_no:
                    pass

                for exbh in exb_num:
                    pass



        for exbh in exb_num:
            self.env['droga.reg.company.info'].update_status(exbh)

        self.calculate_score()
        self.supplier_score()
        if (self.grade_name):
            self._default_grade_ids()
            self._change_color(self.score_out_of_hundred)
        if self.criteria_ids:
            for criteria in self.criteria_ids:
                criteria.score = criteria.minimum_score

class droga_criteria_product(models.Model):
    _name="droga.bdr.product.analysis.criterias"

    product_analysis=fields.Many2one('droga.bdr.product.analysis')
    criteria=fields.Char('Criteria')
    score=fields.Integer('Score')
    pct_out_of_hundred=fields.Float('Score out of 100',compute='_compute_pct',store=True)
    total_score_out_of_hundred=fields.Float('Total score per weight',compute='_compute_pct',store=True)

    @api.depends('score')
    def _compute_pct(self):
        for rec in self:
            rec.pct_out_of_hundred=(rec.score/(rec.max_score-rec.min_score))*100
            rec.total_score_out_of_hundred=(rec.pct_out_of_hundred*rec.weight)/100

    #Hidden fields, used for calculation
    min_score=fields.Integer('Minimum score')
    max_score = fields.Integer('Maximum score')
    weight=fields.Float('Weight')


class SupplierComparison(models.Model):
    _name = 'supplier.comparison'
    _description = 'Supplier Comparison'

    supplier = fields.Char(string='Supplier')
    criteria = fields.Char(string='Criteria')
    min_val = fields.Float(string='Min Val')
    max_val = fields.Float(string='Max Val')
    weight = fields.Float(string='Weight')
    total_score = fields.Float(string='Total Score/ 100')
    prod_list = fields.Text(string='List of requests/products')

    unique_id = fields.Char('ID')

    score = fields.Float(string='Score', default=lambda self: self.min_val)

