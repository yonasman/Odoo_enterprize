from odoo import models, fields


class purchase_request_link(models.Model):
    _inherit = 'droga.purhcase.request.line'
    market_analysis = fields.One2many(
        'droga.purhcase.request.market.analysis', 'pr_line')
    suppliers_list = fields.One2many(
        'droga.purhcase.order.foreign.suppliers.list', 'po_line')
    competitors_comparative = fields.One2many(
        'droga.purchase.order.foreign.competitors.comparative', 'po_line')

    expected_costs = fields.One2many(
        'droga.purhcase.request.expected.cost', 'pr_line')

    def open_market_analysis(self):
        return {
            'name': 'Market analysis',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'droga.purhcase.request.line',
            'view_id': self.env.ref('droga_procurement.droga_procurement_purchase_request_market_analysis').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }

    def open_suppliers_list(self):
        return {
            'name': 'Suppliers list',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'droga.purhcase.request.line',
            'view_id': self.env.ref('droga_procurement.droga_procurement_purchase_request_supp_list').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }

    def open_competitors_comparative_list(self):
        return {
            'name': 'Comparative analysis list',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'droga.purhcase.request.line',
            'view_id': self.env.ref('droga_procurement.droga_procurement_purchase_request_comp_comparative').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }

    def open_expected_cost(self):
        return {
            'name': 'Expected Cost',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'droga.purhcase.request.line',
            'view_id': self.env.ref('droga_procurement.droga_procurement_purchase_request_expected_cost_form').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }


# Market analysis class for purchase request
class purchase_request_market_analysis(models.Model):
    _name = 'droga.purhcase.request.market.analysis'
    pr_line = fields.Many2one('droga.purhcase.request.line')
    purhcase_request_id = fields.Many2one(
        related='pr_line.purhcase_request_id', store=True)
    importer_name = fields.Char('Name of importer')
    manufacturer = fields.Many2one('res.partner', domain="[('supplier_rank','!=', 0)]", string="Manufacturer")
    unit = fields.Many2one('uom.uom')
    avail_stock = fields.Float('Available stock')
    sell_up = fields.Float('Selling unit price')
    epss_volume = fields.Float('EPSS stock volume')
    local_man_status = fields.Char('Local manufacturers stock and RM status')
    remark = fields.Char('Remark')


# Our foreign suppliers list for each purchase order line
class purchase_order_foreign_droga_suppliers_list(models.Model):
    _name = 'droga.purhcase.order.foreign.suppliers.list'
    po_line = fields.Many2one('droga.purhcase.request.line')
    purhcase_request_id = fields.Many2one(
        related='po_line.purhcase_request_id', store=True)
    manufacturer = fields.Many2one('res.partner', domain="[('supplier_rank','!=', 0)]")
    unit_price = fields.Float('Unit price')
    shelf_life = fields.Float('Shelf life')
    is_sup_regsitered = fields.Boolean('Is supplier registered?', default=True)


# Our foreign suppliers competitors list for each purchase order line
class purhcase_order_foreign_competitors_comparative(models.Model):
    _name = 'droga.purchase.order.foreign.competitors.comparative'
    po_line = fields.Many2one('droga.purhcase.request.line')
    purhcase_request_id = fields.Many2one(
        related='po_line.purhcase_request_id', store=True)
    # Make from settings page if not highly variant
    importer = fields.Char('Importer')
    manufacturer = fields.Many2one('res.partner', domain="[('supplier_rank','!=', 0)]", string="Manufacturer")
    unit = fields.Many2one('uom.uom')
    p_up = fields.Float('Private unit price')
    p_qty = fields.Float('Private quantity')
    p_date = fields.Float('Private ordered date')
    e_u_p = fields.Float('EPSS Unit price')
    EPSA_winner = fields.Char('EPSS Winner manufacturer')


class purchase_request_expected_costs(models.Model):
    _name = 'droga.purhcase.request.expected.cost'

    pr_line = fields.Many2one('droga.purhcase.request.line')
    purhcase_request_id = fields.Many2one(
        related='pr_line.purhcase_request_id', store=True)

    tax_amount = fields.Float("Tax Amount based on Invoice value (Birr)")
    demurrage_cost = fields.Float("Demurrage Cost")
    estimated_arriving_cost = fields.Float("Estimated Arriving Cost")
    expected_selling_price = fields.Float(
        "Expected selling price by 50% margin")
    port_of_loading = fields.Float("Port of loading")
    less_container = fields.Selection(
        [('Yes', 'Yes'), ('No', 'No')], string="Less Container if by sea")
    estimated_arrival_date = fields.Date("Estimated Warehouse arival dat")
    unassembled_form = fields.Boolean(
        "Can the product imported in unassembled form")


# new class the replaced the above classes
class purchase_request_analysis_line(models.Model):
    _inherit = 'droga.purhcase.request.line'

    # market analysis
    importer_name = fields.Char(string="Importer")
    manufacturer = fields.Many2one('res.partner', domain="[('supplier_rank','!=', 0)]", string="Manufacturer")
    unit = fields.Many2one('uom.uom', string='UoM')
    avail_stock = fields.Float('Available Stock')
    sell_up = fields.Float('Selling Unit Price')
    epss_volume = fields.Float('EPSS Stock Volume')
    local_man_status = fields.Char('Local Manufacturers Stock and RM Status')
    market_analysis_remark = fields.Char('Remark')

    # foregin supplier list
    foregin_manufacturer = fields.Many2one('res.partner', domain="[('supplier_rank','!=', 0)]", string="Manufacturer")
    foregin_unit_price = fields.Float('Unit Price')
    foregin_shelf_life = fields.Float('Shelf Life')
    foregin_is_sup_regsitered = fields.Boolean('Registered?', default=True)

    # competitors
    comp_importer = fields.Char('Importer')
    comp_manufacturer = fields.Many2one('res.partner', domain="[('supplier_rank','!=', 0)]", string="Manufacturer")
    comp_unit = fields.Many2one('uom.uom', string="UoM")
    comp_p_up = fields.Float('Private Unit Price')
    comp_p_qty = fields.Float('Private Quantity')
    comp_p_date = fields.Date('Private Ordered Date')
    comp_e_u_p = fields.Float('EPSS Unit Price')
    comp_EPSA_winner = fields.Char('EPSS Winner Manufacturer')
