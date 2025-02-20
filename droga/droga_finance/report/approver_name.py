from odoo import models, fields, api
from odoo.tools import drop_view_if_exists


class ApproverName(models.Model):
    _name = 'droga.approver.name'
    _auto = True

    res_id = fields.Integer("res_id")
    create_uid = fields.Many2one("res.users")
    model = fields.Char("Model")
    state = fields.Char("State")

    def get_approver(self, res_id, model, state):
        name = ''

        self.env.cr.execute(
            """select * from droga_approver_name_view where  res_id=%s and model=%s and state=%s """, (res_id, model, state))
        results = self.env.cr.dictfetchall()

        if results:
            user = self.env['res.users'].search([('id', '=', results[0]['create_uid'])])
            return user.name
        else:
            return ''

    def init(self):
        drop_view_if_exists(self.env.cr, 'droga_approver_name_view')
        self._cr.execute(""" 
              create or replace view droga_approver_name_view as 
              (
                   select distinct res_id,max(a.create_uid) as create_uid,a.model,new_value_char as state from mail_message a inner join mail_tracking_value b on a.id=b.mail_message_id
                    group by res_id,a.model,new_value_char
              )
           """)
