from odoo import fields, models, api
from datetime import datetime, timedelta, date
#from playwright.sync_api import sync_playwright


class update_cost(models.Model):
    _name = "update.cost"

    def in1(self,trans_type_in):
        Product = self.env['product.product']

        #For local purchase GRN
        move_vals_list = []
        in_stock_valuation_layers=self.env['stock.valuation.layer'].search([('stock_move_id', '!=', False), ('trans_type_detail', 'like', trans_type_in)])
        move_vals_list += Product._svl_replenish_stock_am(in_stock_valuation_layers)
        if move_vals_list:
            account_moves = self.env['account.move'].sudo().create(move_vals_list)
            account_moves._post()

    def in2(self):
        Product = self.env['product.product']

        #For local purchase COR
        move_vals_list = []
        in_stock_valuation_layers=self.env['stock.valuation.layer'].search([('stock_move_id', '!=', False), ('description', 'like', 'COR/%')])
        move_vals_list += Product._svl_replenish_stock_am(in_stock_valuation_layers)
        if move_vals_list:
            account_moves = self.env['account.move'].sudo().create(move_vals_list)
            account_moves._post()

    def in3(self):
        Product = self.env['product.product']

        #For foreign purchase GRN
        move_vals_list=[]
        in_stock_valuation_layers=self.env['stock.valuation.layer'].search([('stock_move_id', '!=', False), ('description', 'like', 'GRN%'),  ('description', 'like', '%/FP/%')])
        move_vals_list += Product._svl_replenish_stock_am(in_stock_valuation_layers)
        if move_vals_list:
            account_moves = self.env['account.move'].sudo().create(move_vals_list)
            account_moves._post()

    def in4(self):
        Product = self.env['product.product']
        # For customer to store return
        move_vals_list = []
        in_stock_valuation_layers = self.env['stock.valuation.layer'].search([('stock_move_id', '!=', False), ('stock_move_id.location_dest_id.usage', '=', 'internal'),  ('stock_move_id.location_id.name', '=', 'Customers')])
        move_vals_list += Product._svl_replenish_stock_am(in_stock_valuation_layers)
        if move_vals_list:
            account_moves = self.env['account.move'].sudo().create(move_vals_list)
            account_moves._post()

    def out1(self,trans_type_out,month):
        Product = self.env['product.product']
        # For sales issue
        move_vals_list = []
        in_stock_valuation_layers = self.env['stock.valuation.layer'].search([('stock_move_id', '!=', False),('create_date','<',datetime(2023,11,1)),('date_month','=',month),('trans_type_detail', 'like', trans_type_out)])
        move_vals_list += Product._svl_empty_stock_am(in_stock_valuation_layers)
        if move_vals_list:
            account_moves = self.env['account.move'].sudo().create(move_vals_list)
            account_moves._post()

    def out2(self):
        Product = self.env['product.product']

        # For store to supplier
        move_vals_list = []
        in_stock_valuation_layers = self.env['stock.valuation.layer'].search([('stock_move_id', '!=', False), ('stock_move_id.location_id.usage', '=', 'internal'),  ('stock_move_id.location_dest_id.name', '=', 'Vendors')])
        move_vals_list += Product._svl_empty_stock_am(in_stock_valuation_layers)
        if move_vals_list:
            account_moves = self.env['account.move'].sudo().create(move_vals_list)
            account_moves._post()

    def out3(self):
        Product = self.env['product.product']

        # For store to supplier
        move_vals_list = []
        in_stock_valuation_layers = self.env['stock.valuation.layer'].search([('stock_move_id', '!=', False), ('description', 'like', 'COI/LI/22/00002%')])
        move_vals_list += Product._svl_empty_stock_am(in_stock_valuation_layers)
        if move_vals_list:
            account_moves = self.env['account.move'].sudo().create(move_vals_list)
            account_moves._post()


    def out4(self):
        Product = self.env['product.product']

        # For store to supplier
        move_vals_list = []
        in_stock_valuation_layers = self.env['stock.valuation.layer'].search([('stock_move_id', '!=', False), ('description', 'like', 'COI/LI/22/00006%')])
        move_vals_list += Product._svl_empty_stock_am(in_stock_valuation_layers)
        if move_vals_list:
            account_moves = self.env['account.move'].sudo().create(move_vals_list)
            account_moves._post()


    def out5(self):
        Product = self.env['product.product']

        # For store to supplier
        move_vals_list = []
        in_stock_valuation_layers = self.env['stock.valuation.layer'].search([('stock_move_id', '!=', False), ('description', 'like', 'COI/LI/22/00007%')])
        move_vals_list += Product._svl_empty_stock_am(in_stock_valuation_layers)
        if move_vals_list:
            account_moves = self.env['account.move'].sudo().create(move_vals_list)
            account_moves._post()


    def update_temp_loc_to_suspense(self):
        prod=self.env['product.template'].search(
                [('company_id', '=', 1)]
            )
        for rec in prod:
            rec.property_stock_inventory=315

    def update_temp_loc_to_normal(self):
        prod=self.env['product.template'].search(
                [('company_id', '=', 1)]
            )
        for rec in prod:
            rec.property_stock_inventory=14