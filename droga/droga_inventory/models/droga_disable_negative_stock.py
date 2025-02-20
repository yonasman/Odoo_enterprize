from odoo import _, api, models,fields
from odoo.exceptions import ValidationError
from odoo.tools import config, float_compare
from datetime import datetime

class StockQuant(models.Model):
    _inherit = "stock.quant"
    has_access=fields.Boolean(related='warehouse_id.has_access')
    has_read_access = fields.Boolean(related='location_id.has_read_access')
    import_quant=fields.Float('On Hand Quantity',compute='_get_on_hand',store=True)
    import_counted_view = fields.Float('Import counted', compute='_get_import_counted', store=True)
    import_diff = fields.Float('Import difference', compute='_get_import_counted', store=True)
    import_counted=fields.Float('Import counted')
    import_uom = fields.Many2one('uom.uom', related='product_id.import_uom_new')
    difference_custom=fields.Float('Difference_Custom')
    diff_date=fields.Date('Diff_Date')

    def write(self, vals):
        if 'diff_date' in vals or 'difference_custom' in vals:
            for res in self:
                if res.company_id.id == 1 and res.product_id.import_uom_new.factor != 0 and (res.wh_type=='IM' or res.wh_type=='WS'):
                #Import transactions
                    res.inventory_quantity=((vals["difference_custom"]) * (res.product_id.uom_id.factor / res.product_id.import_uom_new.factor))+ res.quantity
                else:
                    res.inventory_quantity=vals["difference_custom"] + res.quantity
                res.product_id.product_tmpl_id.adj_date = vals["diff_date"]
                res.action_apply_inventory()
                res.product_id.product_tmpl_id.adj_date=False

        if 'import_counted' in vals:
            for res in self:
                if res.company_id.id == 1 and res.product_id.import_uom_new.factor != 0:
                    res.inventory_quantity = vals["import_counted"] * (
                                res.product_id.uom_id.factor / res.product_id.import_uom_new.factor)
                else:
                    res.inventory_quantity = vals["import_counted"]
        return super(StockQuant, self).write(vals)

    @api.onchange('import_counted')
    def _import_count_update(self):
        for rec in self:
            if rec.company_id.id == 1 and rec.product_id.import_uom_new.factor != 0:
                rec.inventory_quantity=rec.import_counted*(rec.product_id.uom_id.factor/rec.product_id.import_uom_new.factor)
            else:
                rec.inventory_quantity=rec.import_counted

    @api.model
    def _unlink_zero_quants(self):
        pass

    @api.depends('quantity','product_id.import_uom_new')
    def _get_on_hand(self):
        for rec in self:
            if rec.company_id.id==1 and rec.product_id.import_uom_new.factor!=0:
                rec.import_quant=rec.quantity/(rec.product_id.uom_id.factor/rec.product_id.import_uom_new.factor)
            else:
                rec.import_quant=rec.quantity

    @api.depends('inventory_quantity','product_id.import_uom_new')
    def _get_import_counted(self):
        for rec in self:
            if rec.company_id.id == 1 and rec.product_id.import_uom_new.factor != 0:
                rec.import_counted_view=rec.inventory_quantity/(rec.product_id.uom_id.factor/rec.product_id.import_uom_new.factor)
                rec.import_diff=rec.import_quant-rec.import_counted_view
            else:
                rec.import_counted_view=rec.inventory_quantity

    @api.constrains("product_id", "quantity")
    def check_negative_qty(self):
        p = self.env["decimal.precision"].precision_get("Product Unit of Measure")

        for quant in self:

            if (
                float_compare(quant.quantity, 0, precision_digits=p) == -1
                and quant.product_id.type == "product"
                and quant.location_id.usage in ["internal", "transit"]
            ):
                msg_add = ""
                if quant.lot_id:
                    msg_add = _(" lot '%s'") % quant.lot_id.name_get()[0][1]
                raise ValidationError(
                    _(
                        "You cannot validate this stock operation because the "
                        "stock level of the product '%(name)s'%(name_lot)s would "
                        "become negative "
                        "(%(q_quantity)s) on the stock location '%(complete_name)s' "
                        "and negative stock is "
                        "not allowed for this product and/or location."
                    )
                    % {
                        "name": quant.product_id.display_name,
                        "name_lot": msg_add,
                        "q_quantity": quant.quantity,
                        "complete_name": quant.location_id.complete_name,
                    }
                )
            #Pharmacy stock out tracker
            if quant.location_id.usage=="internal":
                stock_hist=self.env['product.availability.pharmacy'].search([('prod','=',quant.product_id.id),('batch_id','=',quant.lot_id.id),('warehouse','=',quant.location_id.warehouse_id.id)])
                if len(stock_hist)==0:
                    stock_tracker_vals = {
                        'prod': quant.product_id.id,
                        'warehouse': quant.location_id.warehouse_id.id,
                        'stock_quantity_total': quant.quantity,
                        'batch_id':quant.lot_id.id
                    }
                    self.env['product.availability.pharmacy'].create(stock_tracker_vals)
                else:
                    prod_sum_phar = sum(self.env['stock.quant'].search(
                        [('product_id', '=', quant.product_id.id), ('location_id.warehouse_id', '=', quant.warehouse_id.id)]).mapped(
                        'quantity'))
                    stock_hist[0].write({'stock_quantity_total': prod_sum_phar})

            prod_sum =  sum(self.env['stock.quant'].search(
                [('product_id', '=', quant.product_id.id), ('location_id.usage', '=', 'internal')]).mapped('quantity'))
            self.env['product.template'].search([('id','=',quant.product_id.product_tmpl_id.id),'|', ('active', '=', True), ('active', '=', False)])[0].write({
                'most_recent_trans_date': datetime.now().date(),
                'stock_quantity_total':prod_sum
            })
            if prod_sum==0:
                vals = {
                    'product': quant.product_id.product_tmpl_id.id,
                    'date_from': datetime.now().date(),
                }
                self.env['stock.out.history'].create(vals)
            else:
                recs=self.env['stock.out.history'].search([('date_to','=',False)])
                for rc in recs:
                    rc.write({'date_to':datetime.now().date()})


    @api.model
    def _get_quants_action(self, domain=None, extend=False):
        """ Returns an action to open (non-inventory adjustment) quant view.
        Depending of the context (user have right to be inventory mode or not),
        the list view will be editable or readonly.

        :param domain: List for the domain, empty by default.
        :param extend: If True, enables form, graph and pivot views. False by default.
        """
        if not self.env['ir.config_parameter'].sudo().get_param('stock.skip_quant_tasks'):
            self._quant_tasks()
        domain=[('has_access','=',True)]
        ctx = dict(self.env.context or {})
        ctx['inventory_report_mode'] = True
        ctx.pop('group_by', None)
        action = {
            'name': _('Locations'),
            'view_type': 'tree',
            'view_mode': 'list,form',
            'res_model': 'stock.quant',
            'type': 'ir.actions.act_window',
            'context': ctx,
            'domain': domain or [],
            'help': """
                    <p class="o_view_nocontent_empty_folder">{}</p>
                    <p>{}</p>
                    """.format(_('No Stock On Hand'),
                               _('This analysis gives you an overview of the current stock level of your products.')),
        }

        target_action = self.env.ref('stock.dashboard_open_quants', False)
        if target_action:
            action['id'] = target_action.id

        form_view = self.env.ref('stock.view_stock_quant_form_editable').id
        if self.env.context.get('inventory_mode') and self.user_has_groups('stock.group_stock_manager'):
            action['view_id'] = self.env.ref('stock.view_stock_quant_tree_editable').id
        else:
            action['view_id'] = self.env.ref('stock.view_stock_quant_tree').id
        action.update({
            'views': [
                (action['view_id'], 'list'),
                (form_view, 'form'),
            ],
        })
        if extend:
            action.update({
                'view_mode': 'tree,form,pivot,graph',
                'views': [
                    (action['view_id'], 'list'),
                    (form_view, 'form'),
                    (self.env.ref('stock.view_stock_quant_pivot').id, 'pivot'),
                    (self.env.ref('stock.stock_quant_view_graph').id, 'graph'),
                ],
            })
        return action