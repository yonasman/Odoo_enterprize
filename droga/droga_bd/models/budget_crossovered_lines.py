from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CrossoveredBudget(models.Model):
    _inherit = "crossovered.budget"

    fiscal_year = fields.Many2one("account.fiscal.year")

    @api.model
    def create(self, vals):
        return super(CrossoveredBudget, self).create(vals)

    def write(self, vals):
        return super(CrossoveredBudget, self).write(vals)

    def unlink(self):
        non_zero_lines = 0
        for record in self:
            for line in record.crossovered_budget_line:
                if line.planned_amount != 0 or line.reallaocation_addition != 0 or line.addition != 0:
                    non_zero_lines += 1

        if non_zero_lines == 0 or self.state == 'cancel':
            return super(CrossoveredBudget, self).unlink()
        else:
            raise ValidationError(
                "You can't delete budget record, it conatins budget data")

    @api.onchange("fiscal_year")
    def _on_change_fiscal_year(self):
        for record in self:
            # set date from to date to
            record.date_from = record.fiscal_year.date_from
            record.date_to = record.fiscal_year.date_to


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    fiscal_year = fields.Many2one(related="crossovered_budget_id.fiscal_year")
    period = fields.Many2one("account.fiscal.year.period",
                             required=True, domain="[('fiscal_year_id', '=', fiscal_year)]")
    commitment_budget = fields.Float('Commitment')
    remaining_balance = fields.Float('Remaining')
    reallaocation_addition = fields.Float('Reallocation +')
    reallaocation_deduction = fields.Float('Reallocation -')
    addition = fields.Float('Addition')
    revised_budget = fields.Float('Revised')
    budget_line_details = fields.One2many(
        'crossovered.budget.lines.detail', 'budgetary_position_id')

    @api.model
    def create(self, vals):
        if vals:
            # validate
            if 'budget_line_details' in vals:
                self.validate_budget_lines(vals)

            res = super(CrossoveredBudgetLines, self).create(vals)

            # get account linked with budgetary position

            accounts = self.env['account.budget.post'].search(
                [('id', '=', vals['general_budget_id'])])

            # when data imported from excel
            if 'budget_line_details' in vals:
                for line in vals['budget_line_details']:
                    if line[2]['account'] not in accounts.account_ids.ids:
                        x = {
                            'budgetary_position_id': res.id,
                            'account': line[2]['account'],
                            'budget_amount': line[2]['budget_amount']
                        }
                        self.env['crossovered.budget.lines.detail'].create(x)

                # call remaining budget calculator
                #self.env['crossovered.budget.lines.detail'].calculate_remaining_budget_detail()

            else:
                for account in accounts.account_ids:
                    x = {
                        'budgetary_position_id': res.id,
                        'account': account.id,
                        'budget_amount': 0
                    }

                    self.env['crossovered.budget.lines.detail'].create(x)

        return res

    def open_detail_budget(self):
        view = self.env.ref(
            'droga_bd.crossovered_budget_lines_view_form')

        return {
            'name': 'Budget Detail',
            'view_mode': 'form',
            'res_model': 'crossovered.budget.lines',
            'view_id': view.id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',

        }

    def unlink(self):
        non_zero_lines = 0
        for record in self:
            if record.planned_amount != 0 or record.reallaocation_addition != 0 or record.addition != 0:
                non_zero_lines += 1

        if non_zero_lines == 0:
            return super(CrossoveredBudgetLines, self).unlink()
        else:
            raise ValidationError(
                "You can't delete budget record, it conatins budget data")

    def validate_budget_lines(self, vals):
        accounts = self.env['account.budget.post'].search(
            [('id', '=', vals['general_budget_id'])])

        for line in vals['budget_line_details']:
            if line[2]['account'] not in accounts.account_ids.ids:
                raise ValidationError(
                    "Budget line not found in budget category defination")

    @api.onchange("period")
    def _on_change_fiscal_year(self):
        for record in self:
            # set date from to date to
            record.date_from = record.period.date_from
            record.date_to = record.period.date_to

    def update_budget_period(self):
        budget_lines = self.env['crossovered.budget.lines'].search([])
        for record in budget_lines:
            record.date_from = record.period.date_from
            record.date_to = record.period.date_to


class CrossoveredBudgetLinesDetail(models.Model):
    _name = 'crossovered.budget.lines.detail'

    _order = 'account asc'

    budgetary_position_id = fields.Many2one('crossovered.budget.lines')

    crossovered_budget_id = fields.Many2one(
        related='budgetary_position_id.crossovered_budget_id', store=True)
    general_budget_id = fields.Many2one(
        related='budgetary_position_id.general_budget_id', store=True)
    date_from = fields.Date(
        related="crossovered_budget_id.date_from", store=True)
    date_to = fields.Date(related="crossovered_budget_id.date_to", store=True)

    company_id = fields.Many2one(
        related="crossovered_budget_id.company_id", store=True)

    account = fields.Many2one('account.account')
    budget_amount = fields.Float("Budget Amount")

    commitment_budget = fields.Float('Commitment')
    reallaocation = fields.Float('Reallocation +/-')
    addition = fields.Float('Addition')
    revised_budget = fields.Float(
        'Revised', compute="calculate_budget", store=True)
    actual = fields.Float(
        'Actual', compute="calculate_budget", store=True)
    remaining_balance = fields.Float(
        'Remaining', compute="calculate_budget", store=True)

    @api.model_create_multi
    def write(self, vals):
        for val in vals:
            res = super(CrossoveredBudgetLinesDetail, self).write(val)
        # get the sum of detail budget and update planned amount
        detail_budgets = self.env['crossovered.budget.lines.detail'].search(
            [('budgetary_position_id', '=', self.budgetary_position_id.id)])

        planned_budget = 0
        commitment_budget = 0
        reallocation = 0
        addition = 0
        revised_budget = 0
        for line in detail_budgets:
            planned_budget += line.budget_amount
            commitment_budget += line.commitment_budget
            reallocation += line.reallaocation
            addition += line.addition
            revised_budget += line.revised_budget

        # update the planned amount
        budget_line = self.env['crossovered.budget.lines'].search(
            [('id', '=', self.budgetary_position_id.id)])
        if budget_line:
            budget_line.write({'planned_amount': planned_budget})
            budget_line.write({'commitment_budget': commitment_budget})
            budget_line.write({'reallaocation_addition': reallocation})
            budget_line.write({'addition': addition})
            budget_line.write({'revised_budget': revised_budget})

        # self.load_commitment_budget()
        # self.calculate_remaining_budget()

        return res

    def unlink(self):
        non_zero_lines = 0
        for record in self:
            if record.budget_amount != 0 or record.reallaocation != 0 or record.addition != 0:
                non_zero_lines += 1

        if non_zero_lines == 0:
            return super(CrossoveredBudgetLinesDetail, self).unlink()
        else:
            raise ValidationError(
                "You can't delete budget record, it conatins budget data")

    def load_commitment_budget(self):
        budget_lines = self.env['crossovered.budget.lines'].search(
            [('crossovered_budget_state', '!=', 'cancel')])

        # load commitement budgets
        for budget in budget_lines:
            for line in budget.budget_line_details:
                # get commitement budget from commitment table
                commitment_budgets = self.env['droga.budget.commitment.budget'].search(
                    [('state', '=', 'Active'), ('budgetary_position', '=', budget.general_budget_id.id),
                     ('budget_date', '>=',
                      budget.crossovered_budget_id.date_from),
                     ('budget_date', '<=', budget.crossovered_budget_id.date_to),
                     ('expense_account', '=', line.account.id),
                     ('analytic_account_id', '=', budget.analytic_account_id.id)])

                account_commitment_budget = 0
                for commitment_budget in commitment_budgets:
                    if commitment_budget.document_type == 'PR':
                        account_commitment_budget += commitment_budget.purchase_request_total_amount
                    else:
                        account_commitment_budget += commitment_budget.purchase_order_total_amount

                if account_commitment_budget != 0:
                    account_commitment_budget *= -1
                    line.write(
                        {'commitment_budget': account_commitment_budget})

    # to calculate crossovered.budget.lines

    def calculate_remaining_budget(self):

        # load commitement budget
        # self.load_commitment_budget()

        # get active budgets
        budgets = self.env['crossovered.budget'].search(
            [('state', '!=', 'cancel')])

        for budget in budgets:
            for line in budget.crossovered_budget_line:
                # search commitment budget
                total_commitment = 0
                remaining_balance = 0
                revised_budget = 0

                # calculate revised budget
                # revised_budget = line.planned_amount+line.reallaocation_addition+line.addition

                if line.planned_amount > 0:
                    remaining_balance = line.revised_budget + \
                                        line.practical_amount
                else:
                    remaining_balance = line.revised_budget + \
                                        line.practical_amount

                line.write({'remaining_balance': remaining_balance})

    # to calculate crossovered.budget.lines.detail
    def calculate_remaining_budget_detail(self):
        # get active budgets
        budgets = self.env['crossovered.budget.lines'].search(
            [('crossovered_budget_state', '!=', 'cancel')])

        # budget calculation for the detail
        revised_budget = 0
        remaining_balalnce = 0
        for record in budgets.budget_line_details:
            # calculate revised budget
            if record.budget_amount > 0:
                revised_budget = record.budget_amount + \
                                 record.commitment_budget + record.reallaocation + record.addition
            else:
                revised_budget = record.budget_amount + \
                                 record.commitment_budget + record.reallaocation + record.addition
            # update revised budget
            record.revised_budget = revised_budget

            # get actual expense
            actual_expense = self.env['account.move.line'].search(
                [('company_id', '=', record.company_id.id),
                 ('account_id', '=', record.account.id), ('date', '>=',
                                                          record.date_from), ('date', '<=', record.date_to),
                 ('parent_state', '=', 'posted')])

            analytic_account_id = record.budgetary_position_id.analytic_account_id.id

            actual = 0
            for line in actual_expense:
                for line1 in line.analytic_line_ids:
                    if analytic_account_id == line1.account_id.id:
                        actual += line.balance

            # update remaining balance
            # record.actual = actual * -1

            # calcualte remaining balance
            if record.budget_amount > 0:
                remaining_balalnce = record.revised_budget - record.actual
            else:
                remaining_balalnce = record.revised_budget - record.actual

            record.write({'revised_budget': revised_budget,
                          'actual': actual, 'remaining_balance': remaining_balalnce})

    @api.depends('budget_amount', 'commitment_budget', 'reallaocation', 'addition')
    def calculate_budget(self):
        revised_budget = 0
        remaining_balalnce = 0
        for record in self:
            # calculate revised budget
            if record.budget_amount > 0:
                revised_budget = record.budget_amount + \
                                 record.commitment_budget + record.reallaocation + record.addition
            else:
                revised_budget = record.budget_amount + \
                                 record.commitment_budget + record.reallaocation + record.addition
            # update revised budget
            record.revised_budget = revised_budget

            analytic_account_id = record.budgetary_position_id.analytic_account_id.id
            # get actual expense
            actual_expense = self.env['account.move.line'].search(
                [('company_id', '=', record.company_id.id),
                 ('account_id', '=', record.account.id), ('date', '>=',
                                                          record.date_from), ('date', '<=', record.date_to),
                 ('parent_state', '=', 'posted')])

            actual = 0
            for line in actual_expense:
                for line1 in line.analytic_line_ids:
                    if analytic_account_id == line1.account_id.id:
                        actual += line.balance

            # update remaining balance
            # record.actual = actual * -1
            record.actual = actual

            # calcualte remaining balance
            if record.budget_amount > 0:
                record.remaining_balance = record.revised_budget - record.actual
            else:
                record.remaining_balance = record.revised_budget - record.actual

    @api.onchange('account')
    def on_account_change(self):
        for record in self:
            accounts = record.general_budget_id.account_ids.ids
            return {'domain': {'account': [('id', 'in', (accounts))]}}
