from odoo import _, api, fields, models


class TransactionType(models.Model):
    _name = "account.transaction.type"
    _description = "Transaction Type"

    name = fields.Char("Short Code", required=True)
    transaction_type = fields.Selection(
        [('Payment', 'Payment'), ('Receipt', 'Receipt'), ('Miscellaneous', 'Miscellaneous')])
    payment_method = fields.Selection(
        [('Cash', 'Cash'), ('Bank', 'Bank'), ('Miscellaneous', 'Miscellaneous')])
    assignment = fields.Selection(
        [('Automatic', 'Automatic'), ('Manual', 'Manual')], required=True, default="Automatic")
    description = fields.Char("Description", required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 index=True, default=lambda self: self.env.company.id)

    posting_cycles = fields.One2many(
        "account.transaction.posting.cycle", "posting_cycle_id")

    trans_no_from = fields.Integer("Transaction From")
    trans_no_to = fields.Integer("Transaction To")

    @api.model
    def create(self, vals):
        return super(TransactionType, self).create(vals)

    def write(self, vals):
        return super(TransactionType, self).write(vals)

    def name_get(self):
        result = []

        for record in self:
            result.append((record.id, '%s - %s' %
                          (record.name, record.description)))
        return result


class TransactionPostingCycle(models.Model):
    _name = "account.transaction.posting.cycle"
    _description = "Posting Cycle"

    posting_cycle_id = fields.Many2one("account.transaction.type")
    fiscal_year = fields.Many2one(
        "account.fiscal.year", string="Fiscal Year", required=True)
    sequence = fields.Many2one("ir.sequence", required=True)
