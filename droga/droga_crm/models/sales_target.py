import datetime
from datetime import timedelta,date
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api


class sales_target_header(models.Model):
    _name='droga.crm.sales.target.header'
    _rec_name='header_description'

    target_detail=fields.One2many('droga.crm.sales.target.detail','target_header')
    sales_team = fields.Many2many('droga.crm.settings.city')
    type=fields.Selection([('Daily','Daily'),('Weekly','Weekly'),('Monthly','Monthly'),('Quarterly','Quarterly')],default='Weekly',required=True)
    date_from=fields.Date('Date from',required=True)
    date_to=fields.Date('Date to',compute='_get_date_to',inverse='_inverse_date_to',store=True,required=True)
    status=fields.Selection([('Active','Active'),('Closed','Closed')],required=True,store=True,default='Active')
    detail_count=fields.Float(compute='_get_detail_count',string='Detail count')
    rate=fields.Float(default=1)
    date_from_rep=fields.Date('Date from')
    date_to_rep = fields.Date('Date to')
    header_description=fields.Char(compute='_get_descr')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    def _get_descr(self):
        for rec in self:
            cities=''
            for cit in rec.sales_team:
                cities=cities+cit.city_descr+', '
            rec.header_description=cities+rec.type+' target, '+rec.date_from.strftime('%d-%b-%Y').upper()+' - '+rec.date_to.strftime('%d-%b-%Y').upper()
    def get_reports_all(self):
        for rec in self:
            rec.date_from_rep=rec.date_from
            rec.date_to_rep = rec.date_to
            return {
                'name': 'Target report '+str(rec.date_from)+' to '+ str(rec.date_to),
                'view_mode': 'tree',
                'view_type': 'tree',
                'res_model': 'droga.crm.sales.target.report',
                'view_id': self.env.ref('droga_crm.droga_crm_saels_target_report').id,
                'type': 'ir.actions.act_window',
                'context': {'search_default_group_sales_team': 1,'search_default_group_header_id': 1},
                'domain':
                    ([('target_detail.target_header', 'in', self.ids)])
            }

    def get_reports_prod(self):
        for rec in self:
            rec.date_from_rep=rec.date_from
            rec.date_to_rep = rec.date_to
            return {
                'name': 'Target report '+str(rec.date_from)+' to '+ str(rec.date_to),
                'view_mode': 'tree',
                'view_type': 'tree',
                'res_model': 'droga.crm.sales.target.report',
                'view_id': self.env.ref('droga_crm.droga_crm_saels_target_report').id,
                'type': 'ir.actions.act_window',
                'context': {'search_default_group_prod_grp': 1},
                'domain':
                    ([('target_detail.target_header', 'in', self.ids)])
            }

    def _get_detail_count(self):
        for rec in self:
            rec.detail_count=0
            for det in rec.target_detail:
                if det.target_qty+det.target_amt!=0:
                    rec.detail_count=rec.detail_count+1

    def _inverse_date_to(self):
        pass
    _sql_constraints = [
        ('target_team_type_datefrom', 'unique (sales_team,type,date_from)', 'The combination sales team,type and date already exists!')
    ]
    @api.depends('date_from','type')
    def _get_date_to(self):
        for rec in self:
            if rec.date_from:
                if rec.type=='Weekly':
                    rec.date_to=rec.date_from+ timedelta(days=6)
                elif rec.type=='Monthly':
                    rec.date_to = rec.date_from + relativedelta(months=1) - timedelta(days=1)
                elif rec.type == 'Daily':
                    rec.date_to = rec.date_from
                else:
                    rec.date_to = rec.date_from + relativedelta(months=3) - timedelta(days=1)
            else:
                rec.date_to=rec.date_from

    def target_detail_open(self):
        return {
            'name': 'Target detail',
            # 'view_type': 'form',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'droga.crm.sales.target.header',
            'view_id': self.env.ref('droga_crm.droga_crm_saels_target_form').id,
            'type': 'ir.actions.act_window',
            #'target': 'new',
            'res_id': self.id,
        }
    def get_report(self):
        return {
            'name': 'Target report '+str(self.date_from_rep)+' to '+ str(self.date_to_rep),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'droga.crm.sales.target.detail.prompt',
            'view_id': self.env.ref('droga_crm.droga_crm_sales_target_detail_prompt_form').id,
            'type': 'ir.actions.act_window',
            'context': {
                'default_target_header': self.id,
                'default_date_from':self.date_from_rep,
                'default_date_to': self.date_to_rep,
            },
            'target':'new'
        }

    def duplicate_entry(self):
        for rec in self:
            vals = {
                'type': rec.type,
                'date_from': rec.date_from,
                'date_to': rec.date_to,
            }

            new_id=self.env['droga.crm.sales.target.header'].create(vals)

            targ_details=[]
            for det in rec.target_detail:
                new_line_vals = det.copy_data(default={'target_header': new_id.id})[0]
                targ_details.append((0, 0, new_line_vals))  # Create a new record with correct format

            new_id.update({'target_detail': targ_details})

class inventory_stock_card_xls(models.TransientModel):
    _name='droga.crm.sales.target.detail.prompt'

    date_from=fields.Date('Date from', default=fields.Date.today(),required=True)
    date_to = fields.Date('Date to',default=fields.Date.today(),required=True)
    type = fields.Selection(
        [("Quantity", "Quantity"), ("Amount", "Amount"), ("Quantity and Amount", "Quantity and Amount")], default="Quantity and Amount",required=True)
    target_header=fields.Many2one('droga.crm.sales.target.header')

    def action_get_det_report(self):
        for rec in self.target_header:
            rec.date_from_rep=self.date_from
            rec.date_to_rep = self.date_to
        qty=False
        amt=False

        if self.type=='Quantity':
            amt=True
        if self.type=='Amount':
            qty=True

        return {
            'name': 'Target report '+str(self.date_from)+' to '+ str(self.date_to),
            'view_mode': 'tree',
            'view_type': 'tree',
            'res_model': 'droga.crm.sales.target.report',
            'view_id': self.env.ref('droga_crm.droga_crm_saels_target_report').id,
            'type': 'ir.actions.act_window',
            'context': {'search_default_group_sales_team': 1,'amt':amt,'qty':qty},
            'domain':
                ([('target_detail', 'in', self.target_header.target_detail.ids)])
        }

class sales_target_detail(models.Model):
    _name='droga.crm.sales.target.detail'
    target_header=fields.Many2one('droga.crm.sales.target.header',required=True)
    indicator=fields.Many2many('product.product')
    target_qty=fields.Integer('Target qty')
    #me_too = fields.Boolean('MeToo')
    me_too_core = fields.Selection([('MeToo', 'MeToo'), ('Core', 'Core')],store=True,string='Core / Me Too')
    target_amt = fields.Integer('Target amt')
    remark=fields.Char('Remark')
    prod_group = fields.Many2one('droga.crm.settings.prod_group')
    type=fields.Selection([('By Indicator', 'By Indicator'), ('By Prod. Group', 'By Prod. Group'), ('Core / Me Too','Core / Me Too')],store=True,required=True)

class sales_target_report(models.Model):
    _name='droga.crm.sales.target.report'
    _auto = False
    target_detail=fields.Many2one('droga.crm.sales.target.detail',required=True)
    header_id = fields.Many2one('droga.crm.sales.target.header')

    indicator=fields.Many2many('product.product',related='target_detail.indicator')
    remark = fields.Char('Remark', related='target_detail.remark')
    prod_group = fields.Many2one('droga.crm.settings.prod_group')

    sales_team = fields.Many2one('droga.crm.settings.city')
    target_qty=fields.Float('Target qty')
    ach_qty = fields.Float('Acheived qty')
    ach_qty_pct = fields.Float('Acheived qty pct')
    me_too_core = fields.Selection([('MeToo', 'MeToo'), ('Core', 'Core')],store=True,required=True)
    target_amt = fields.Float('Target amt')
    ach_amt = fields.Float('Acheived amount')
    ach_amt_pct = fields.Float('Acheived amt pct')
    def read_group(self, domain, fields, groupby, **kwargs):
        grouped_data = super(sales_target_report, self).read_group(domain, fields, groupby)
        for group in grouped_data:
            group['ach_qty_pct'] = (group['ach_qty'] / group['target_qty']) * 100 if group['target_qty'] != 0 else 0
            group['ach_amt_pct'] = (group['ach_amt'] / group['target_amt']) * 100 if group['target_amt'] != 0 else 0

        return grouped_data

    def init(self):
        self._cr.execute(""" 
           create or replace view droga_crm_sales_target_report as 
           (
                select row_number() over () as id,
                
                 t.target_detail,t.type,t.sales_team,t.target_qty,t.ach_qty,t.me_too_core,t.target_amt,t.ach_amt,t.ach_qty_pct,t.ach_amt_pct,t.prod_group,t.header_id from (select (case when g.target_qty=0 then 0 else (g.ach_qty/g.target_qty)*100 end) as ach_qty_pct,(case when g.target_amt=0 then 0 else (g.ach_amt/g.target_amt)*100 end) as ach_amt_pct,g.* from (
                
    select b.id as target_detail,b.type,c.droga_crm_settings_city_id as sales_team,b.target_qty*a.rate*(cast((a.date_to_rep-a.date_from_rep)as decimal(7,2))/cast((a.date_to-a.date_from)as decimal(7,2))) as target_qty,
	case b.type when 'By Indicator' then (select sum(i.import_quant_invoiced) from sale_order_line i where i.order_from_det in ('IM-WS','IM-IM') and i.product_id in 
		(select g.product_product_id from droga_crm_sales_target_detail_product_product_rel g where g.droga_crm_sales_target_detail_id=b.id) and i.cust_location=c.droga_crm_settings_city_id 
	    and i.invoice_date<=a.date_to_rep and i.invoice_date>=date_from_rep) when 
		'By Prod. Group' then (select sum(i.import_quant_invoiced) from sale_order_line i where i.order_from_det in ('IM-WS','IM-IM') and (select y.categ_id from product_template y where y.id=(select u.product_tmpl_id from product_product u where u.id=i.product_id)) =b.prod_group
	    and i.cust_location=c.droga_crm_settings_city_id 
	    and i.invoice_date<=a.date_to_rep and i.invoice_date>=date_from_rep)
	when 'Core / Me Too' then (select sum(i.import_quant_invoiced) from sale_order_line i where i.order_from_det in ('IM-WS','IM-IM') and (select case when y.is_core_product=true then 'Core' else 'MeToo' end from product_template y where y.id=(select u.product_tmpl_id from product_product u where u.id=i.product_id)) =b.me_too_core
	    and i.cust_location=c.droga_crm_settings_city_id 
	    and i.invoice_date<=a.date_to_rep and i.invoice_date>=date_from_rep) else 0 end as ach_qty,cast(b.me_too_core as TEXT),b.target_amt*a.rate*(cast((a.date_to_rep-a.date_from_rep)as decimal(7,2))/cast((a.date_to-a.date_from)as decimal(7,2))) as target_amt,
	case b.type when 'By Indicator' then (select sum(i.invoiced_amt)*1.0 from sale_order_line i where i.order_from_det in ('IM-WS','IM-IM') and i.product_id in 
		(select g.product_product_id from droga_crm_sales_target_detail_product_product_rel g where g.droga_crm_sales_target_detail_id=b.id) and i.cust_location=c.droga_crm_settings_city_id 
	    and i.invoice_date<=a.date_to_rep and i.invoice_date>=date_from_rep) when 
		'By Prod. Group' then (select sum(i.invoiced_amt)*1.0 from sale_order_line i where i.order_from_det in ('IM-WS','IM-IM') and (select y.categ_id from product_template y where y.id=(select u.product_tmpl_id from product_product u where u.id=i.product_id)) =b.prod_group
	    and i.cust_location=c.droga_crm_settings_city_id 
	    and i.invoice_date<=a.date_to_rep and i.invoice_date>=date_from_rep)
	when 'Core / Me Too' then (select sum(i.invoiced_amt)*1.0 from sale_order_line i where i.order_from_det in ('IM-WS','IM-IM') and (select case when y.is_core_product=true then 'Core' else 'MeToo' end from product_template y where y.id=(select u.product_tmpl_id from product_product u where u.id=i.product_id)) =b.me_too_core
	    and i.cust_location=c.droga_crm_settings_city_id 
	    and i.invoice_date<=a.date_to_rep and i.invoice_date>=date_from_rep) else 0 end as ach_amt,b.prod_group as prod_group,a.id as header_id from droga_crm_sales_target_header a join droga_crm_sales_target_detail b on a.id=b.target_header
	join droga_crm_sales_target_header_droga_crm_settings_city_rel c on a.id=c.droga_crm_sales_target_header_id where (b.target_qty+b.target_amt)!=0
	
               ) g )t
           ) 
         """)
