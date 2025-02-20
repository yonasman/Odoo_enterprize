from odoo import fields, models, api


class ModelName(models.Model):
    _name = 'droga.tender.competitors'

    # Text fields
    lot_number = fields.Char("Lot number")
    item_des = fields.Char("Item description")
    remark = fields.Char("Remark")

    # decimal fields
    quantity = fields.Float("Quantity")
    unit_price = fields.Float("Unit price")
    amount = fields.Float("Amount sent",compute="compute_amount")
    @api.depends("unit_price", "quantity")
    def compute_amount(self):
        for rec in self:
            rec.amount = rec.unit_price * rec.quantity

    # relational fields
    unit_of_measure = fields.Many2one('uom.uom', string='UOM')
    type_item = fields.Many2one('droga.tender.settings.type.item', string='Type or items')
    competitor=fields.Many2one('droga.tender.settings.competitor',string='Competitor')
    currency=fields.Many2one('res.currency',string='Currency')
    submission_id = fields.Many2one('droga.tender.submission.detail')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)


    #selection fields
    tech_result = fields.Selection([('Pass', 'Pass'), ('Fail', 'Fail')])
    status = fields.Selection([('awarded', 'Awarded'),('lost', 'Lost')])
