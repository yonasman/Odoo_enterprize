from odoo import _, api, fields, models
from datetime import datetime
from odoo.exceptions import UserError, ValidationError


class BudgetReallocation(models.Model):
    _name = 'droga.budget.reallocation'

    _order = "name desc"

    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']

    name = fields.Char('Request Reference', required=True,
                       index=True, copy=False, default='New')
    budget_id = fields.Many2one('crossovered.budget', required=True)
    request_by = fields.Many2one('hr.employee', string="Requested By")
    request_date = fields.Date("Request Date", default=datetime.today())
    analytic_account = fields.Many2one("account.analytic.account")
    purpose = fields.Char("Purpose")
    budget_reallocations = fields.One2many(
        'droga.budget.reallocation.line', 'budget_reallocation_id')
    budget_additions = fields.One2many(
        'droga.budget.addition.line', 'budget_addition_id')
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 index=True, default=lambda self: self.env.company.id)
    state = fields.Selection([('Draft', 'Draft'), ("Submitted", "Submitted"), ('Verified', 'Verified'),
                             ('Approved', 'Approved'), ('Cancelled', 'Cancelled')], default='Draft', tracking=True)
    reallocation_status = fields.Selection(
        [('Draft', 'Draft'), ('Done', 'Done')], default="Draft")

    document_type = fields.Selection(
        [('Reallocation', 'Reallocation'), ('Addition', 'Addition')], default='Reallocation')

    # draft request
    def draft_request(self):
        self.write({'state': 'Draft'})
        return True

    def submit_request(self):
        self.write({'state': 'Submitted'})
        return True

    # verify request
    def verify_request(self):
        self.write({'state': 'Verified'})
        return True

    def approve_request(self):
        self.write({'state': 'Approved'})
        self.new_reallocation_addition()
        self.transfer_addition_reallocation()
        self.env['crossovered.budget.lines.detail'].calculate_remaining_budget()
        self.env['crossovered.budget.lines.detail'].calculate_remaining_budget_detail()
        return True

    def cancel_request(self):
        self.write({'state': 'Cancelled'})
        return True

    @ api.model
    def create(self, vals):
        # get sequence number for each company

        company_id = vals.get('company_id', self.default_get(
            ['company_id'])['company_id'])

        self_comp = self.with_company(company_id)
        vals['name'] = self_comp.env['ir.sequence'].next_by_code(
            'droga.budget.reallocation') or '/'
        res = super(BudgetReallocation, self_comp).create(vals)

        return res

    def calculate_reallocation_addition(self):
        # get reallocation not transfered
        reallocations = self.env['droga.budget.reallocation'].search([
            ('reallocation_status', '=', 'Draft'), ('state', '=', 'Approved')])
        for reallocation in reallocations:
            # budget reallocation
            for line in reallocation.budget_reallocations:
                # reallocation_amount += line.transfer_amount

                # update reallocation on both transfer and reciving ends
                # get transfer line and update transefer

                transfer_line_from = self.env['crossovered.budget.lines.detail'].search([('crossovered_budget_id', '=', reallocation.budget_id.id),
                                                                                         ('date_from', '>=', line.date_from), ('date_to', '<=', line.date_to), ('general_budget_id', '=', line.from_budgetary_position.id)])

                transfer_line_to = self.env['crossovered.budget.lines.detail'].search([('crossovered_budget_id', '=', reallocation.budget_id.id),
                                                                                       ('date_from', '>=', line.date_from), ('date_to', '<=', line.date_to), ('general_budget_id', '=', line.to_budgetary_position.id)])

                # update transfer from
                transfer_amount = 0
                for transfer in transfer_line_from:
                    if transfer.account.id == line.account_from.id:
                        transfer_amount += line.transfer_amount

                # update recive amount
                recive_amount = 0
                for recive in transfer_line_to:
                    if recive.account.id == line.account_to.id:
                        recive_amount += line.transfer_amount

            # search reallocation line and update

                if transfer_line_from and transfer_line_to:
                    for transfer in transfer_line_from:
                        if transfer.account.id == line.account_from.id:
                            # update reallocation deduction
                            amount = transfer_amount * -1
                            transfer.write(
                                {'reallaocation': amount})
                if transfer_line_to:
                    # update reallocation deduction
                    for recive in transfer_line_to:
                        if recive.account.id == line.account_to.id:
                            recive.write(
                                {'reallaocation': recive_amount})

            # additional budget
            for line1 in reallocation.budget_additions:

                addition_line_from = self.env['crossovered.budget.lines.detail'].search([('crossovered_budget_id', '=', reallocation.budget_id.id),
                                                                                         ('date_from', '>=', line1.date_from), (
                                                                                             'date_to', '<=', line1.date_to),
                                                                                         ('general_budget_id', '=', line1.bdugetary_position.id)])

                addition_amount = 0
                for addition in addition_line_from:
                    if addition.account.id == line1.account.id and addition.budgetary_position_id.analytic_account_id.id == line1.budget_addition_id.analytic_account.id:
                        addition_amount += line1.addition_amount

                if addition_line_from:
                    for addition in addition_line_from:
                        if addition.account.id == line1.account.id and addition.budgetary_position_id.analytic_account_id.id == line1.budget_addition_id.analytic_account.id:
                            addition.write(
                                {'addition': addition_amount})

            # change status transfered reallocation to done
            reallocation.write({'reallocation_status': 'Done'})

    def transfer_addition_reallocation(self):
        additions = self.env['droga.budget.reallocation'].search([
            ('reallocation_status', '=', 'Draft'), ('state', '=', 'Approved')])

        for addition in additions.budget_additions:
            # search addition line
            addition_lines = self.env['crossovered.budget.lines'].search([('crossovered_budget_id', '=', addition.budget_addition_id.budget_id.id),
                                                                          ('analytic_account_id', '=', addition.budget_addition_id.analytic_account.id),
                                                                         ('date_from', '>=',
                                                                          addition.date_from),
                                                                         ('date_to', '<=',
                                                                          addition.date_to),
                                                                         ('general_budget_id', '=',
                                                                          addition.bdugetary_position.id),
                                                                          ])
            for addition_line in addition_lines.budget_line_details:
                if addition.account.id == addition_line.account.id:
                    # get all adition amount linked to this specific account
                    self.env.cr.execute("""select coalesce(sum(addition_amount),0) as addition from droga_budget_reallocation a inner join droga_budget_addition_line b on a.id=b.budget_addition_id 
                                            where a.budget_id=%s and a.analytic_account=%s and date_from>=%s and date_to<=%s and bdugetary_position=%s and a.state='Approved'""",
                                        (addition.budget_addition_id.budget_id.id, addition.budget_addition_id.analytic_account.id, addition.date_from, addition.date_to, addition.bdugetary_position.id))
                    res = self.env.cr.dictfetchone()
                    # update addition field on budget line detail
                    addition_line.write({'addition': res['addition']})

        for reallocation in additions.budget_reallocations:
            # deduct from transfer from
            transfer_lines = self.env['crossovered.budget.lines'].search([('crossovered_budget_id', '=', reallocation.budget_reallocation_id.budget_id.id),
                                                                          ('analytic_account_id', '=', reallocation.budget_reallocation_id.analytic_account.id),
                                                                         ('date_from', '>=',
                                                                          reallocation.date_from),
                                                                         ('date_to', '<=',
                                                                          reallocation.date_to),
                                                                         ('general_budget_id', '=',
                                                                          reallocation.from_budgetary_position.id),
                                                                          ])
            for transfer_line in transfer_lines.budget_line_details:
                if reallocation.account_from.id == transfer_line.account.id:
                    self.env.cr.execute(""" select coalesce(sum(transfer_amount),0) as reallocation_amount from droga_budget_reallocation a inner join droga_budget_reallocation_line b on a.id=b.budget_reallocation_id
                                            where a.budget_id=%s and a.analytic_account=%s and b.date_from>=%s and b.date_to<=%s and b.from_budgetary_position=%s and a.state='Approved'""",
                                        (reallocation.budget_reallocation_id.budget_id.id, reallocation.budget_reallocation_id.analytic_account.id, reallocation.date_from, reallocation.date_to, reallocation.from_budgetary_position.id))

                    res = self.env.cr.dictfetchone()
                    reallocation_amount = res['reallocation_amount']*-1
                    # update
                    transfer_line.write({'reallaocation': reallocation_amount})

            recived_lines = self.env['crossovered.budget.lines'].search([('crossovered_budget_id', '=', reallocation.budget_reallocation_id.budget_id.id),
                                                                         ('analytic_account_id', '=', reallocation.budget_reallocation_id.analytic_account.id),
                                                                         ('date_from', '>=',
                                                                          reallocation.period_to_date_from),
                                                                         ('date_to', '<=',
                                                                          reallocation.period_to_date_to),
                                                                         ('general_budget_id', '=',
                                                                          reallocation.to_budgetary_position.id),
                                                                         ])
            for recived_line in recived_lines.budget_line_details:
                if reallocation.account_to.id == recived_line.account.id:
                    self.env.cr.execute(""" select coalesce(sum(transfer_amount),0) as reallocation_amount from droga_budget_reallocation a inner join droga_budget_reallocation_line b on a.id=b.budget_reallocation_id
                                            where a.budget_id=%s and a.analytic_account=%s and b.period_to_date_from>=%s and b.period_to_date_to<=%s and b.from_budgetary_position=%s and a.state='Approved'""",
                                        (reallocation.budget_reallocation_id.budget_id.id, reallocation.budget_reallocation_id.analytic_account.id, reallocation.period_to_date_from, reallocation.period_to_date_to, reallocation.from_budgetary_position.id))

                    res = self.env.cr.dictfetchone()
                    reallocation_amount = res['reallocation_amount']*1
                    # update
                    recived_line.write({'reallaocation': reallocation_amount})

        for record in additions:
            record.write({'reallocation_status': 'Done'})

    def new_reallocation_addition(self):
        for record in self:
            for line in record.budget_reallocations:
                # check if the budget reallocation line not found in the budget
                budget_line = self.env['crossovered.budget.lines'].search(
                    [('crossovered_budget_id', '=', record.budget_id.id),
                     ('general_budget_id', '=', line.to_budgetary_position.id),
                     ('analytic_account_id', '=', record.analytic_account.id),
                     ('date_from', '>=', line.period_to_date_from), ('date_to', '<=', line.period_to_date_to)])

                if not budget_line.ids:
                    # add new budget category line
                    vals = {
                        'crossovered_budget_id': record.budget_id.id,
                        'general_budget_id': line.to_budgetary_position.id,
                        'analytic_account_id': record.analytic_account.id,
                        'period': line.period_to.id,
                        'date_from': line.period_to_date_from,
                        'date_to': line.period_to_date_to,
                        'planned_amount': 0

                    }

                    res = self.env['crossovered.budget.lines'].create(vals)

            for line in record.budget_additions:
                # check if the budget reallocation line not found in the budget
                budget_line = self.env['crossovered.budget.lines'].search(
                    [('crossovered_budget_id', '=', record.budget_id.id),
                     ('general_budget_id', '=', line.bdugetary_position.id),
                     ('analytic_account_id', '=', record.analytic_account.id),
                     ('date_from', '>=', line.date_from), ('date_to', '<=', line.date_to)])

                if not budget_line.ids:
                    # add new budget category line
                    vals = {
                        'crossovered_budget_id': record.budget_id.id,
                        'general_budget_id': line.bdugetary_position.id,
                        'analytic_account_id': record.analytic_account.id,
                        'period': line.period.id,
                        'date_from': line.date_from,
                        'date_to': line.date_to,
                        'planned_amount': 0

                    }

                    res = self.env['crossovered.budget.lines'].create(vals)

                    for line1 in res.budget_line_details:
                        if line.account.id == line1.account.id:
                            # update the addition amount
                            line1.write(
                                {'addition': line.addition_amount})


class BudgetReallocationDetail(models.Model):
    _name = 'droga.budget.reallocation.line'

    budget_reallocation_id = fields.Many2one("droga.budget.reallocation")
    from_budgetary_position = fields.Many2one("account.budget.post")
    to_budgetary_position = fields.Many2one("account.budget.post")
    account_from = fields.Many2one("account.account")
    account_to = fields.Many2one("account.account")
    fiscal_year = fields.Many2one(
        related='budget_reallocation_id.budget_id.fiscal_year', store=True)
    period = fields.Many2one("account.fiscal.year.period",
                             domain="[('fiscal_year_id', '=', fiscal_year)]")
    date_from = fields.Date("Date From")
    date_to = fields.Date("Date To")

    period_to = fields.Many2one("account.fiscal.year.period",
                                domain="[('fiscal_year_id', '=', fiscal_year)]")
    period_to_date_from = fields.Date("Date From")
    period_to_date_to = fields.Date("Date To")

    remaining_amount = fields.Float(
        "Remaining Amount", compute="_calculate_remaining_amount", store=True)
    transfer_amount = fields.Float("Transfer Amount")
    is_enough_budget = fields.Boolean(
        compute="_is_enough_budget_left", default=True, store=True)

    @api.depends('from_budgetary_position', 'account_from', 'date_from', 'date_to')
    def _calculate_remaining_amount(self):
        if self.from_budgetary_position and self.date_from and self.date_to and self.budget_reallocation_id.analytic_account and self.account_from:
            # get remaining amount
            budgets = self.env['crossovered.budget'].search(
                [('id', '=', self.budget_reallocation_id.budget_id.id)])

            budget_lines = self.env['crossovered.budget.lines'].search(
                [('crossovered_budget_id', '=', self.budget_reallocation_id.budget_id.id),
                 ('general_budget_id', '=', self.from_budgetary_position.id),
                 ('analytic_account_id', '=',
                  self.budget_reallocation_id.analytic_account.id),
                 ('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to)])

            reamining_amount = 0
            if budget_lines:
                for line in budget_lines.budget_line_details:
                    # if line.date_from >= self.date_from and line.date_to <= self.date_to and line.general_budget_id.id == self.from_budgetary_position.id and line.analytic_account_id.id == self.budget_reallocation_id.analytic_account.id:
                    if line.account.id == self.account_from.id:
                        reamining_amount += line.remaining_balance

            self.remaining_amount = reamining_amount

    @api.model
    def create(self, vals):
        self.validate_reallocation_lines(vals)
        res = super(BudgetReallocationDetail, self).create(vals)

        return res

    def write(self, vals):
        self.validate_reallocation_lines(vals)
        res = super(BudgetReallocationDetail, self).write(vals)

        return res

    @api.onchange('from_budgetary_position')
    def _load_budgetary_position_accounts_from(self):
        from_accounts = self.from_budgetary_position.account_ids.ids
        return {'domain': {'account_from': [('id', 'in', (from_accounts))]}}

    @api.onchange('to_budgetary_position')
    def _load_budgetary_position_accounts_to(self):
        to_accounts = self.to_budgetary_position.account_ids.ids
        return {'domain': {'account_to': [('id', 'in', (to_accounts))]}}

    @api.constrains('remaining_amount', 'transfer_amount')
    def _is_enough_budget_left(self):
        for record in self:
            if record.remaining_amount < record.transfer_amount or record.remaining_amount <= 0:
                record.is_enough_budget = False
                raise ValidationError(
                    "There is no enough remaining budget to reallocate")
            else:
                record.is_enough_budget = True

    def validate_reallocation_lines(self, vals):
        if 'account_from' in vals and 'account_to' in vals:
            if vals['account_from'] == vals['account_to']:
                raise ValidationError(
                    "You can't reallocate budget to the same account")

            # get account types
            account_from = self.env['account.account'].search(
                [('id', '=', vals['account_from'])])

            account_to = self.env['account.account'].search(
                [('id', '=', vals['account_to'])])

            if account_from and account_to:
                if account_from.account_type != account_to.account_type:
                    raise ValidationError(
                        "You can't reallocate budget to diffrenet account categories")

    @api.onchange("period", "period_to")
    def _on_change_fiscal_year(self):
        for record in self:
            # set date from to date to
            record.date_from = record.period.date_from
            record.date_to = record.period.date_to
            record.period_to_date_from = record.period_to.date_from
            record.period_to_date_to = record.period_to.date_to


class BudgetAdditionDetail(models.Model):
    _name = 'droga.budget.addition.line'

    budget_addition_id = fields.Many2one("droga.budget.reallocation")
    bdugetary_position = fields.Many2one("account.budget.post")
    account = fields.Many2one(
        "account.account")
    fiscal_year = fields.Many2one(
        related='budget_addition_id.budget_id.fiscal_year', store=True)
    period = fields.Many2one("account.fiscal.year.period",
                             domain="[('fiscal_year_id', '=', fiscal_year)]")
    date_from = fields.Date("Date From")
    date_to = fields.Date("Date To")
    addition_amount = fields.Float("Addition Amount")

    @api.onchange('bdugetary_position')
    def _load_budgetary_position_accounts(self):
        accounts = self.bdugetary_position.account_ids.ids
        return {'domain': {'account': [('id', 'in', (accounts))]}}

    @api.onchange("period")
    def _on_change_fiscal_year(self):
        for record in self:
            # set date from to date to
            record.date_from = record.period.date_from
            record.date_to = record.period.date_to
