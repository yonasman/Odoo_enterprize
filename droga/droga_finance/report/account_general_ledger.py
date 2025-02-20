from odoo import models,fields,api
from odoo.tools import get_lang


class GeneralLedgerReport(models.AbstractModel):

    _inherit = 'account.general.ledger.report.handler'

    def _get_query_amls(self, report, options, expanded_account_ids, offset=0, limit=None):
        """ Construct a query retrieving the account.move.lines when expanding a report line with or without the load
        more.
        :param options:               The report options.
        :param expanded_account_ids:  The account.account ids corresponding to consider. If None, match every account.
        :param offset:                The offset of the query (used by the load more).
        :param limit:                 The limit of the query (used by the load more).
        :return:                      (query, params)
        """
        additional_domain = [('account_id', 'in', expanded_account_ids)] if expanded_account_ids is not None else None
        queries = []
        all_params = []
        lang = self.env.user.lang or get_lang(self.env).code
        journal_name = f"COALESCE(journal.name->>'{lang}', journal.name->>'en_US')" if \
            self.pool['account.journal'].name.translate else 'journal.name'
        account_name = f"COALESCE(account.name->>'{lang}', account.name->>'en_US')" if \
            self.pool['account.account'].name.translate else 'account.name'
        for column_group_key, group_options in report._split_options_per_column_group(options).items():
            # Get sums for the account move lines.
            # period: [('date' <= options['date_to']), ('date', '>=', options['date_from'])]
            tables, where_clause, where_params = report._query_get(group_options, domain=additional_domain,
                                                                   date_scope='strict_range')
            ct_query = self.env['res.currency']._get_query_currency_table(group_options)
            query = f'''
                   (SELECT
                       account_move_line.id,
                       account_move_line.date,
                       account_move_line.date_maturity,
                       account_move_line.name,
                       account_move_line.ref,
                       account_move_line.company_id,
                       account_move_line.account_id,
                       account_move_line.payment_id,
                       account_move_line.partner_id,
                       account_move_line.currency_id,
                       account_move_line.amount_currency,
                       move.bank_payment_ref,
                       ROUND(account_move_line.debit * currency_table.rate, currency_table.precision)   AS debit,
                       ROUND(account_move_line.credit * currency_table.rate, currency_table.precision)  AS credit,
                       ROUND(account_move_line.balance * currency_table.rate, currency_table.precision) AS balance,
                       move.name                               AS move_name,
                       company.currency_id                     AS company_currency_id,
                       partner.name                            AS partner_name,
                       move.move_type                          AS move_type,
                       account.code                            AS account_code,
                       {account_name}                          AS account_name,
                       journal.code                            AS journal_code,
                       {journal_name}                          AS journal_name,
                       full_rec.name                           AS full_rec_name,
                       %s                                      AS column_group_key
                   FROM {tables}
                   JOIN account_move move                      ON move.id = account_move_line.move_id
                   LEFT JOIN {ct_query}                        ON currency_table.company_id = account_move_line.company_id
                   LEFT JOIN res_company company               ON company.id = account_move_line.company_id
                   LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
                   LEFT JOIN account_account account           ON account.id = account_move_line.account_id
                   LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
                   LEFT JOIN account_full_reconcile full_rec   ON full_rec.id = account_move_line.full_reconcile_id
                   WHERE {where_clause}
                   ORDER BY account_move_line.date, account_move_line.move_name, account_move_line.id)
               '''

            queries.append(query)
            all_params.append(column_group_key)
            all_params += where_params

        full_query = " UNION ALL ".join(queries)

        if offset:
            full_query += ' OFFSET %s '
            all_params.append(offset)
        if limit:
            full_query += ' LIMIT %s '
            all_params.append(limit)

        return (full_query, all_params)