from odoo import api, fields, models
from odoo.exceptions import Warning


class DrugInformationQuery(models.Model):
    _name = 'drug.information.query'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Drug Information Query'
    state = fields.Selection([
        ('enquiry', 'Enquiry'),
        ('response', 'Response'),
        ('feedback', 'Feedback'),
        ('completed', 'Completed')
    ], string='State', default='enquiry', readonly=True, copy=False)

    date = fields.Datetime(string='Date', required=True)
    requestor_name = fields.Char(string='Requestor\'s Full Name', required=True)
    physical_address = fields.Char(string='Physical Address', required=True)
    tel_no = fields.Char(string='Tel No.', required=True)
    email = fields.Char(string='Email', required=True)
    qualification = fields.Selection([
        ('gp', 'GP'),
        ('specialist', 'Specialist'),
        ('health_officer', 'Health Officer'),
        ('patient', 'Patient'),
        ('nurse', 'Nurse'),
        ('pharmacist', 'Pharmacist'),
        ('druggist', 'Druggist'),
        ('student', 'Student'),
        ('other', 'Other')
    ], string='Qualification/Profession', required=True)

    contact_methods = fields.Selection([
        ('walk_in', 'Walk-in'),
        ('phone', 'Phone'),
        ('written_form', 'Written Form'),
        ('email', 'E-mail'),
        ('fax', 'Fax'),
        ('letter', 'Letter'),
        ('other', 'Other')
    ], string='Methods of Contact', required=True)

    request_type = fields.Selection([
        ('patient_specific', 'Patient Specific'),
        ('academic', 'Academic'),
        ('other', 'Other')
    ], string='Request Type', required=True)

    other_qualification = fields.Char(string='Other Qualification/Profession', compute='_compute_other_qualification',
                                      inverse='_inverse_other_qualification')
    other_contact_method = fields.Char(string='Other Method of Contact', compute='_compute_other_contact_method',
                                       inverse='_inverse_other_contact_method')
    other_request_type = fields.Char(string='Other Request Type', compute='_compute_other_request_type',
                                     inverse='_inverse_other_request_type')

    @api.depends('qualification')
    def _compute_other_qualification(self):
        for record in self:
            if record.qualification == 'other':
                record.other_qualification = record.qualification
            else:
                record.other_qualification = False

    def _inverse_other_qualification(self):
        for record in self:
            if record.other_qualification:
                record.qualification = 'other'
            else:
                record.qualification = False

    @api.depends('contact_methods')
    def _compute_other_contact_method(self):
        for record in self:
            if record.contact_methods == 'other':
                record.other_contact_method = record.contact_methods
            else:
                record.other_contact_method = False

    def _inverse_other_contact_method(self):
        for record in self:
            if record.other_contact_method:
                record.contact_methods = 'other'
            else:
                record.contact_methods = False

    @api.depends('request_type')
    def _compute_other_request_type(self):
        for record in self:
            if record.request_type == 'other':
                record.other_request_type = record.request_type
            else:
                record.other_request_type = False

    def _inverse_other_request_type(self):
        for record in self:
            if record.other_request_type:
                record.request_type = 'other'
            else:
                record.request_type = False

    patient_age = fields.Integer(string='Patient Age')
    patient_sex = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], string='Patient Sex')
    patient_weight = fields.Float(string='Patient Weight')
    diagnosis = fields.Char(string='Diagnosis')
    current_medications = fields.Text(string='Current Medications')
    concurrent_medications = fields.Text(string='Concurrent Medications')
    allergies = fields.Text(string='Allergies')
    other_information = fields.Text(string='Other Relevant Information')
    request_question = fields.Text(string='Request/Question', required=True)
    preferred_response_method = fields.Selection([
        ('verbal', 'Verbal'),
        ('phone', 'Phone'),
        ('written', 'Written'),
        ('fax', 'Fax'),
        ('email', 'E-mail')
    ], string='Preferred Method of Response', required=True)
    response_time = fields.Selection([
        ('prompt', 'Prompt'),
        ('30_60_min', '30-60 min'),
        ('end_of_day', 'End of Day'),
        ('when_time_permits', 'When Time Permits')
    ], string='Response Needed In', required=True)
    referral_required = fields.Boolean(string='Referral Required', required=True)
    additional_information = fields.Text(string='Additional Information', required=True)

    # DIS RESPONSE FORM
    disclaimer = fields.Text(string='.',
                             default=''' Disclaimer: 
                                    The DIS is designed to assist health care providers and other users to provide accurate, up-to-date, reliable and complete. We hope we have served you with this information and in case you need further information/materials, please feel free to contact us.''')
    reference_no_reponce = fields.Char(string='Enquiry Reference No.')
    date_reponce = fields.Datetime(string='Date')
    inquirer_name_reponce = fields.Char(string='To (Name of Inquirer)')
    phone_no_reponce = fields.Char(string='Phone No.')
    email_reponce = fields.Char(string='Email')
    message_reponce = fields.Text(string='Dear')
    question_reponce = fields.Text(string='Question/Query')
    answer_reponce = fields.Text(string='Answer/Response')
    references_reponce = fields.Text(string='References')
    add_info_reponce = fields.Text(string='Additional Information and Recommendations Provided')
    completed_by_reponce = fields.Char(string="Response Completed By")

    # DIS INFORMATION FEEDBACK
    intro = fields.Text(string='.',
                        default='''Droga Pharmacies DIC is seeking your feedback on the information we have provided in response to your enquiry under _________________ Dated. ________ We ... value your feedback because this helps us to stay in touch with your needs and for the continuous quality improvements of 
    our drug information services 
    We invite you to use this form to submit feedback or complaint. Provision of the information requested: 
    ''')
    reference_no_feedback = fields.Char(string='Enquiry Reference No.')
    enquiry_date_feedback = fields.Date(string='Date of Enquiry')
    message_feedback = fields.Text(string='Dear Enquirer')
    provision_of_information_feedback = fields.Text(string='Provision of the information requested')
    information_received_in_time_feedback = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Was the information received in time?')
    presentation_of_information_feedback = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Was the presentation of the information satisfactory?')
    information_meet_expectation_feedback = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Did the information provided meet your expectation?')
    information_used_feedback = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Was the information used?')
    email_feedback = fields.Char(string='Email')
    thanks = fields.Text(string='.', default='We thank you for your time and response ')
    create_user=fields.Many2one('res.users', default=lambda self: self.env.user.id)
    def open_enquire_form(self):
        self.state = "response"

    def open_respond_form(self):
        self.state = "feedback"
        #if self.reference_no_reponce and self.date_reponce and self.inquirer_name_reponce and self.phone_no_reponce and self.email_reponce and self.message_reponce and self.question_reponce and self.answer_reponce and self.references_reponce and self.add_info_reponce and self.completed_by_reponce:
        #    self.state = "feedback"
        #else:
        #    raise Warning('Please fill in all the required fields.')

    def open_feedback_form(self):
        self.state = "completed"
        #if self.reference_no_feedback and self.enquiry_date_feedback and self.message_feedback and self.provision_of_information_feedback and self.information_received_in_time_feedback and self.presentation_of_information_feedback and self.information_meet_expectation_feedback and self.information_used_feedback and self.email_feedback:
        #    self.state = "completed"
        #else:
        #    raise Warning('Please fill in all the required fields.')

    def set_activity_done(self):

        activity = self.env["mail.activity"].search(
            [('res_name', '=', self.name)])
        for act in activity:
            act.sudo().action_done()