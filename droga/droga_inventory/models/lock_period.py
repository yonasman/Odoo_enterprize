# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import Warning, UserError
from datetime import datetime


class LockPeriod(models.Model):
    """."""

    _inherit = 'mail.thread'
    _name = 'droga.inv.lock_period'

    name = fields.Char(
        string='Name',
        help="Give a name to the lock")

    date_start = fields.Date(
        string='Date start',
        default=fields.Date.today(),
        required=True,tracking=True,
        help="Lock the operation from this date")

    date_end = fields.Date(
        string='Date end',
        default=fields.Date.today(),
        required=True,tracking=True,
        help="Lock the operation to this date")

    excluded_users = fields.Many2many(
        string='Excluded users',
        help="Rules won't be apply to these users",
        comodel_name='res.users',
        relation='lockperiod_to_resusers_rel')

    message_to_show = fields.Text(
        string='Message to show',
        help="This message will be show on move in this period",
        translate=True)

    def unlink_(self):
        raise UserError(
            "You can't delete lock period entries, change the date range instead.")

class StockMove(models.Model):
    """."""

    _inherit = 'stock.move'

    #@api.constrains('date_expected', 'state')
    def check_date_expected(self):
        lock_period_obj = self.env[
            'droga.inv.lock_period']
        uid = self.env.user.id
        for rec in self:
            date_expected = rec.mapped('date')[0]
            all_lock_period = lock_period_obj.search([
                ('date_start', '<=', date_expected),
                ('date_end', '>=', date_expected)])

            for lock_period in all_lock_period:

                if uid in lock_period.excluded_users.mapped('id'):
                    continue

                raise UserError('Inventory transaction is closed for the period between %s and %s.'%
                              (lock_period.date_start, lock_period.date_end))

class SalesOrder(models.Model):
    _inherit = 'sale.order'

    @api.constrains('date_order', 'state')
    def check_date_expected(self):
        lock_period_obj = self.env[
            'droga.inv.lock_period']
        uid = self.env.user.id
        for rec in self:
            date_expected = rec.mapped('date_order')[0]
            all_lock_period = lock_period_obj.search([
                ('date_start', '<=', date_expected),
                ('date_end', '>=', date_expected)])

            for lock_period in all_lock_period:

                if uid in lock_period.excluded_users.mapped('id'):
                    continue

                raise UserError('Sales transaction is closed for the period between %s and %s.' %
                              (lock_period.date_start, lock_period.date_end))

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.constrains('date_order', 'state')
    def check_date_expected(self):
        lock_period_obj = self.env[
            'droga.inv.lock_period']
        uid = self.env.user.id
        for rec in self:
            date_expected = rec.mapped('date_order')[0]
            all_lock_period = lock_period_obj.search([
                ('date_start', '<=', date_expected),
                ('date_end', '>=', date_expected)])

            for lock_period in all_lock_period:

                if uid in lock_period.excluded_users.mapped('id'):
                    continue

                raise UserError('Purchase transaction is closed for the period between %s and %s.' %
                              (lock_period.date_start, lock_period.date_end))
