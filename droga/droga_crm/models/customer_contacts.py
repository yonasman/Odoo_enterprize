from odoo import models,fields

class droga_crm_contacts(models.Model):
    _name='droga.crm.contacts'
    _rec_name = 'descr'

    descr=fields.Char('descr',compute='_get_descr')
    parent_customer=fields.Many2one('res.partner',string='Customer Name')
    contact_area=fields.Many2one('droga.crm.settings.city',related='parent_customer.city_name',store=True)
    contact_type = fields.Many2one('droga.cust.type', related='parent_customer.cust_type_ext', store=True)
    parent_name=fields.Char( related='parent_customer.name', store=True)
    contact_name=fields.Char('Contact Name',required=True)
    mobile = fields.Char('Mobile')
    gender = fields.Selection(
        [('Male', 'Male'), ('Female', 'Female')],
        string='Gender')
    specialty=fields.Many2one('droga.cust.specialty',string='Specialty',required=True)
    job_position = fields.Many2one('droga.cust.job.position', string='Job position')

    contact_tobe_accessed_by = fields.Selection(
        [('Promotors', 'Promotors'), ('Sales reps', 'Sales reps'), ('Both', 'Both')], required=True,
        string='Contact used by',default='Both')

    cont_grade = fields.Many2one('droga.cust.grade', string='Contact grade')

    days=fields.Many2many('droga.crm.settings.day',string='Day')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    def _get_descr(self):
        for record in self:
            try:
                name = (record.job_position.job_position+ ' - ') if record.job_position else ''
                name=(name+record.specialty.specialty+ ' - ') if record.specialty.specialty else name

                record.descr= name+record.contact_name
            except:
                record.descr=record.contact_name if record.contact_name else ''
            