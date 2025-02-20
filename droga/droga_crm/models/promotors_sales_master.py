from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo import http
from odoo.http import request


class droga_promotors_sales_master(models.Model):
    _name = 'droga.pro.sales.master'

    _rec_name = 'p_name'
    p_name = fields.Char('Promotor/Sales full name', required=True)
    s_name = fields.Char('Promotor/Sales short name')
    p_id = fields.Char('Promotor/Sales ID',default='12345', required=True,tracking=True)
    p_regions =fields.Many2many('droga.crm.settings.city', required=True)
    p_groups=fields.Many2many('droga.crm.settings.prod_group',required=True)
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')],
                            required=True,default='Active')
    is_pm=fields.Boolean('Is PM',default=False)
    employee_access_users=fields.Many2one('res.users',string='Login user',required=True)
    res_user_name=fields.Char(related=employee_access_users.name)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    def change_id(self):
        self.ensure_one()
        self.write({'p_id': '12345'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'ID has been changed to 12345 successfully.',
                'type': 'success',
                'sticky': True
            }
        }

class droga_promotors_sales_detail_visit(models.Model):
    _name = 'droga.pro.sales.master.visit'
    pro_id = fields.Many2one('droga.pro.sales.master', string='Promotor/Sales full name')
    s_id = fields.Char('Session ID')


class droga_promotors_sales_detail_entry_visit(models.TransientModel):
    _name = 'droga.pro.sales.master.entry.visit'

    def _get_un(self):
        if len(self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])) > 0:
            return self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])[0].pro_id.id
        else:
            return False

    pro_id = fields.Many2one('droga.pro.sales.master',default=_get_un, string='Promotor/Sales full name',required=True)
    def _get_pw(self):
        if len(self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])) > 0:
            return self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])[0].pro_id.p_id
        else:
            return False

    p_id = fields.Char('Promotor/Sales ID',default=_get_pw)
    new_id=fields.Char('New ID')
    conf_new = fields.Char('New ID')

    def action_enter(self):
        if len(self.env['droga.pro.sales.master'].search([('id', '=', self.pro_id.id), ('p_id', '=', self.p_id)])) > 0 and self.p_id=='12345':
            return {
                'name': "Reset Password",
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'context': {'default_pro_id': self.pro_id.id,'default_pre_pass':self.p_id},
                'res_model': 'droga.pro.sales.master.entry.visit',
                'view_id': self.env.ref('droga_crm.droga_pro_sales_master_entry_visit_form_pop_pup').id,
                'target': 'new'
            }
        elif len(self.env['droga.pro.sales.master'].search([('id', '=', self.pro_id.id), ('p_id', '=', self.p_id)])) > 0:
            if len(self.env['droga.pro.sales.master.visit'].search([('s_id','=',request.session.sid)]))>0:
                if self.env['droga.pro.sales.master.visit'].search([('s_id','=',request.session.sid)])[0].pro_id.id == self.pro_id.id:
                    return {'type': 'ir.actions.act_window_close'}
                else:
                    raise UserError("Session already occupied. Please exit and enter again.")
            vals = {
                's_id': request.session.sid,
                'pro_id': self.pro_id.id
            }
            self.env['droga.pro.sales.master.visit'].create(vals)
        else:
            raise UserError("Please check promotor/sales name and id.")


    pre_pass = fields.Char()
    new_pass = fields.Char()
    confirm_pass = fields.Char()

    def action_change(self):
        return {
            'name': "Reset Password",
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'context': {'default_pro_id': self.pro_id.id},
            'res_model': 'droga.pro.sales.master.entry.visit',
            'view_id': self.env.ref('droga_crm.droga_pro_sales_master_entry_visit_form_pop_pup').id,
            'target': 'new'
        }

    def action_reset(self):
        if not self.pro_id:
            raise UserError("Please enter user name.")
        if not self.new_pass:
            raise UserError("Please enter new ID.")
        if self.new_pass!=self.confirm_pass:
            raise UserError("Please make sure new ID and confirm new ID are similar.")

        uname = self.env['droga.pro.sales.master'].search([('id', '=', self.pro_id.id)])
        if self.pre_pass == uname.p_id:
            valus = {
                'p_id': self.new_pass,
            }
            uname.sudo().write(valus)
        else:
            raise UserError("Please check your previous ID!.")

        return {
            'name': 'Promotor/sales entry',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'context': {'default_pro_id': self.pro_id.id},
            'res_model': 'droga.pro.sales.master.entry.visit',
            'view_id': self.env.ref('droga_crm.droga_pro_sales_master_entry_visit_form').id,
            'target': 'new'
        }


    def action_cancel_reset(self):
        return {
            'name': 'Promotor/sales entry',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'droga.pro.sales.master.entry.visit',
            'context': {'default_pro_id': self.pro_id.id},
            'view_id': self.env.ref('droga_crm.droga_pro_sales_master_entry_visit_form').id,
            'target': 'new'
        }


