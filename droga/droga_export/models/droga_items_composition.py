from odoo import models, fields, api
from odoo.exceptions import UserError


class droga_items_composition(models.Model):
    _name='droga.export.items.composition'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', default='New')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company, required=True)
    raw_item=fields.Many2one('product.template',string='Raw material',required=True)
    def_code=fields.Char('Item code',related='raw_item.default_code')
    item_desc = fields.Char('Description', related='raw_item.name')
    items_detail=fields.One2many('droga.export.items.composition.fin.goods', 'items_header')

    @api.model
    def create(self, vals_list):
        if vals_list.get('name', 'New') == 'New':
            if len(vals_list['items_detail']) == 0:
                raise UserError("At least one product must be registered to save record.")

            prod_to_update=[]

            pct_sum=0
            for item in vals_list['items_detail']:
                pct_sum+=item[2]['rate_in_pct']
                if item[2]['type']=='finish':
                    prod_to_update.append(item[2]['item'])

            if pct_sum != 100:
                raise UserError("The summation of percentage should equal 100%.")

            _name = self.env['ir.sequence'].next_by_code('droga.export.items.composition.sequence')
            if not _name:
                raise UserError("Order sequence not found.")
            vals_list['name'] = _name

            for item in prod_to_update:
                self.env['product.template'].search([('id', '=', item)])[0].bought_locally=True

        return super(droga_items_composition, self).create(vals_list)

    def write(self, vals):
        for val in vals:
            res = super(droga_items_composition, self).write(vals)

        detail_items = self.env['droga.export.items.composition.fin.goods'].search(
            [('items_header', '=', self.id)])

        pct_sum = 0
        for item in detail_items:
            pct_sum += item['rate_in_pct']

        if pct_sum != 100:
            raise UserError("The summation of percentage should equal 100%.")

        return res

class droga_items_composition_finished_goods(models.Model):
    _name = 'droga.export.items.composition.fin.goods'
    company_id=fields.Many2one('res.company',related='items_header.company_id')
    item = fields.Many2one('product.template', string='Item',required=True)
    type = fields.Selection(
        [('finish', 'Finished good'), ('byproduct', 'By-Product'), ('waste', 'Wastage')],required=True)
    rate_in_pct=fields.Float(string='Percentage (out of 100)',required=True)
    items_header = fields.Many2one('droga.export.items.composition', required=True)
    