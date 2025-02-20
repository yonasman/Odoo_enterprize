from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    asset_number = fields.Char("Asset Code")
    asset_sub_category = fields.Many2one("account.asset.subcat", domain="[('asset_cat', '=', model_id)]")

    @api.model
    def create(self, vals):
        # get sequence number for each company
        self_comp = self.with_company(self.company_id)

        if 'asset_sub_category' in vals:
            # generate asset cod automatically
            # get sequence code
            asset_sub_category = self.env["account.asset.subcat"].search([('id', '=', vals['asset_sub_category'])])
            if asset_sub_category.sequence:
                vals['asset_number'] = asset_sub_category.sequence.next_by_id()

        res = super(AccountAsset, self_comp).create(vals)

        return res

    def generate_asset_id(self):

        for record in self:
            if record.asset_number == "" or not record.asset_number:
                if record.asset_sub_category.id:
                    asset_sub_category = self.env["account.asset.subcat"].search(
                        [('id', '=', record.asset_sub_category.id)])
                    if asset_sub_category.sequence:
                        record.asset_number = asset_sub_category.sequence.next_by_id()
                else:
                    raise ValidationError("Please select sub category")
            else:
                raise ValidationError("Asset code is already generated")

    @api.constrains('asset_number')
    def _check_asset_no_unique(self):
        counts = self.search_count(
            [('asset_number', '=', self.asset_number)])

        if counts > 1 and self.asset_type not in ('sale', 'expense'):
            raise ValidationError("Asset code must be unique")


class AssetSubCategory(models.Model):
    _name = 'account.asset.subcat'

    name = fields.Char("Name", required=True)
    code = fields.Char("Code", required=True)
    asset_cat = fields.Many2one("account.asset", domain=[('state', '=', 'model')])

    sequence = fields.Many2one("ir.sequence", required=True)

    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 index=True, default=lambda self: self.env.company.id)

    @api.constrains('asset_number')
    def _check_asset_subcat_unique(self):
        counts = self.search_count(
            [('code', '=', self.code)])

        if counts > 1:
            raise ValidationError("Asset code must be unique")
