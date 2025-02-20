from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Utility(models.TransientModel):
    _name = 'droga.finance.utility'

    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 index=True, default=lambda self: self.env.company.id)

    def get_transaction_no(self, code, trans_date, company_id):

        fiscal_year = self.env['account.fiscal.year'].search(
            [('date_from', '<=', trans_date), ('date_to', '>=', trans_date),
             ('company_id', '=', company_id)])

        sequence = None
        if fiscal_year:
            # get transaction type
            transaction_types = self.env["account.transaction.type"].search(
                [('name', '=', code), ('company_id', '=', company_id)])
            for record in transaction_types.posting_cycles:
                if record.fiscal_year.id == fiscal_year.id:
                    # get sequence
                    sequence = record.sequence

            for rec in transaction_types:
                transaction_type = rec

            if sequence:
                # generate new sequence
                # get sequence number for each company
                # transaction_no = self.env['ir.sequence'].next_by_code(sequence.code) or '/'
                transaction_no = sequence.next_by_id()
                # update transaction
                return transaction_no
            else:
                raise ValidationError(
                    "Sequence is not defined for the transaction type")
