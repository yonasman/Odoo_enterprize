from datetime import datetime

from odoo import models, fields, api


class payment_request_extension(models.Model):
    _inherit = 'droga.account.payment.request'
    tender_origin_form=fields.Many2one('droga.tender.master',readonly=True)

class inventory_request_extension(models.Model):
    _inherit = 'droga.inventory.consignment.issue'
    tender_origin_form=fields.Many2one('droga.tender.master',readonly=True)

class sale_order_extension(models.Model):
    _inherit = 'sale.order'
    tender_origin_form_tender=fields.Many2one('droga.tender.master',readonly=True)
    po_tender=fields.Many2many('purchase.order',string='Purchase order')
    client_po_ref=fields.Char('Client PO ref')
class accoumt_move(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        res=super(accoumt_move, self).create(vals)
        if res.invoice_origin:
            if res.invoice_origin.startswith('SOD'):
                tenders=self.env['sale.order'].search([('name','=',res.invoice_origin)]).tender_origin_form_tender
                for tend in tenders:
                    tend.write({'latest_invoice_date': datetime.today()})

                    childs = self.env['droga.tender.submission.detail'].search([('parent_tender_submission', '=', tend.id)])
                    for ch in childs:
                        ch.write({'latest_invoice_date': datetime.today()})

                        det_childs = self.env['droga.tender.performance.evaluation'].search(
                            [('parent_tender_performance_detail', '=', ch.id)])
                        for chd in det_childs:
                            chd.write({'latest_invoice_date': datetime.today()})
        return res
class pur_request_extension(models.Model):
    _inherit = 'droga.purchase.request.local'
    tender_origin_form_tender = fields.Many2one('droga.tender.master', readonly=True)

class sale_order_line_extension(models.Model):
    _inherit = 'sale.order.line'
    tender_origin_form_tender=fields.Many2one('droga.tender.master',related='order_id.tender_origin_form_tender')

class tender_customer_extension(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals_list):
        new_cus=super().create(vals_list)
        if 'supplier_rank' in vals_list:
            if vals_list["supplier_rank"]==0 and vals_list["is_company"]:
                prev_rec=self.env['droga.tender.settings.customers'].sudo().search([('name','=',vals_list['name'])])
                if len(prev_rec)>0:
                    for rec in prev_rec:
                        rec['master_cust_id']=new_cus.id
                        rec['customer_type']=vals_list['cust_type_ext']
                else:
                    tender_cus={
                        'name':vals_list['name'],
                        'master_cust_id':new_cus.id,
                        'customer_type':vals_list['cust_type_ext']}
                    self.env['droga.tender.settings.customers'].sudo().create(tender_cus)

        return new_cus