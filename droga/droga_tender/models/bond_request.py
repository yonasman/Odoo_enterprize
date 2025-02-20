from odoo import models, fields, api
from io import BytesIO
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

class droga_bond_requests(models.Model):
    _name = "droga.bond.requests"
    _rec_name='letter_number'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('req', 'Requested'),
        ('pro', 'Processed')
    ], string='Status', default="draft", readonly=True, tracking=True)

    bank = fields.Many2one('res.bank', string='Bank')
    client = fields.Many2one('res.partner', string='Client/Organization')

    security_type = fields.Selection([('Bid Security', 'Bid Security'), ('Performance Security', 'Performance Security'),('Advance Security','Advance Security')],string='Security Type')
    security_form = fields.Many2one('droga.tender.settings.sec.type','Security Form')
    purpose = fields.Char(string='Purpose')
    tender = fields.Many2one('droga.tender.master','Tender')
    po_number = fields.Char(string='Po Number')
    starting_date = fields.Date(string='Starting Date')
    validity_period = fields.Integer(string='Validity Period')
    amount = fields.Float(string='Amount')
    letter_number = fields.Char(string='Letter Number')
    request_type = fields.Selection([('f', 'Foreign'), ('l', 'Local'), ('F+L', 'F+L')])
    on_behalf_of = fields.Char(string='On Behalf Of') #For international tenders only
    bond_approver=fields.Many2one('res.users', compute='_get_approvers',store=True)
    is_extension=fields.Boolean('Is extension')
    to_be_extended_bond=fields.Many2one('droga.bond.requests',string='To be extended bond')
    bank_number=fields.Char('Bank Number')
    dead_line_date = fields.Date('Deadline date')
    def _get_approvers(self):
        for rec in self:
            rec.bond_approver = self.env.ref("droga_tender.bond_recepient").users.filtered(
                lambda m: self.env.company.id in m.company_ids.ids).ids[0] if len(
                self.env.ref("droga_tender.bond_recepient").users.filtered(
                lambda m: self.env.company.id in m.company_ids.ids).ids) > 0 else None

    @api.model
    def create(self, vals_list):
        vals_list['letter_number'] = self.env['ir.sequence'].next_by_code(
            'droga.bond.requests.sequence')

        return super(droga_bond_requests,self).create(vals_list)

    def get_bond_letter(self):
        buffer = BytesIO()

        p = canvas.Canvas(buffer, pagesize=letter)
        if self.security_type == 'Bid Security':
            security_type = 'Unconditional Bid Bond Guarantee'
            body = 'Bid Bond Guarantee'
        else:
            security_type = 'Performance Bond'
            body = 'Performance Bond'
        if self.tender.bid_type == 'l':
            on_account = ""
        else:
            on_account = "On Account of " + str(self.on_behalf_of)
        if self.po_number:
            tender_no = ", as per Tender No: " + self.po_number
        else:
            tender_no = ""
        products = set()
        for product in self.tender.detail_submissions_fin.type_item:
            products.add(product.type_or_item_name)
        products = ", ".join(list(products))
        index = products.rfind(',')
        if index != -1:
            products = list(products)
            products[index] = ' and '
            products = ''.join(products)
        if self.is_extension:
            message = """TO:- {bank_name}
        
        Addis Ababa 
            
    Subject: Requesting an extension for {security_type} 
            
It is known that our company Droga Pharma PLC is working in cooperation with the branch bank. Although we had previously signed a {body} for the supplies of {products} of {amount} birr for {validity_period} days starting from {starting_date} to {client_name} {tender_no}, the company has asked us to extend the service period again, so we humbly request that the bank look into the matter and extend the service period until {end_date}.
        
Thank you in advance for your kind cooperation. 
        
Bidder: M/s Droga Pharma Plc. {on_behalf_of}
                
                
                                                                        With best regards
            """.format(
            bank_name=self.bank.name,
            security_type=security_type,
            client_name=self.client.name,
            starting_date=self.starting_date,
            validity_period=self.validity_period,
            amount=self.amount,
            tender_no=tender_no,
            on_behalf_of=on_account,
            end_date=self.dead_line_date,
            body=body,
            products=products,
        )
        else:
            message = """TO:- {bank_name}
        
        Addis Ababa 
            
    Subject: Asking for {security_type} 
            
It is known that our company Droga Pharma PLC is working in cooperation with the branch bank. Therefore, We humbly ask you to make {security_type} for the supply of {products}, by deducted from the guarantee, for {client_name} on behalf of the company as per tender No. {tender_no}  in the amount of {amount} birr to {validity_period} days from {starting_date}.
        
Thank you in advance for your kind cooperation. 
        
Bidder: M/s Droga Pharma Plc. {on_behalf_of}
                
                
                                                                        With best regards
            """.format(
            bank_name=self.bank.name,
            security_type=security_type,
            client_name=self.client.name,
            starting_date=self.starting_date,
            validity_period=self.validity_period,
            amount=self.amount,
            tender_no=self.po_number,
            on_behalf_of=on_account,
            products=products,
        )

        printed_text = message

        lines = printed_text.split("\n")
        y = 700
        line_height = 20
        max_width = 400

        for line in lines:
            words = line.split(" ")
            line = ""
            for word in words:
                if p.stringWidth(line + " " + word) < max_width:
                    line += " " + word
                else:
                    if line.startswith("Subject:") or line.startswith("TO:-") or "With best regards" in line:
                        p.setFont("Helvetica-Bold", 12)
                    p.drawString(100, y, line)
                    y -= line_height
                    line = word

            if line:
                if line.startswith("Subject:") or line.startswith("TO:-") or "With best regards" in line:
                    p.setFont("Helvetica-Bold", 12)
                p.drawString(100, y, line)
                y -= line_height

        p.showPage()
        p.save()

        pdf_content = buffer.getvalue()
        buffer.close()

        filename = "Bond Request Letter.pdf"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': self._name,
            'res_id': self.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % (attachment.id),
            'target': 'self',
        }

    def request(self):
        self.set_activity_done()
        self.ensure_one()
        self._get_approvers()
        self.state = 'req'

    def bond_approve(self):
        self.set_activity_done()
        self.ensure_one()
        self.state = 'pro'

    def amend(self):
        self.set_activity_done()
        self.ensure_one()
        self.state = 'draft'

    def action_cancel(self):
        self.set_activity_done()
        self.ensure_one()
        self.state = 'cancel'

    def set_activity_done(self):
        activity = self.env["mail.activity"].search(
            [('res_name', '=', self.letter_number)])
        for act in activity:
            act.sudo().action_done()