from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountLoanRepayment(models.Model):
    
    _name='account.loan.repayment'
    
    is_paiedinterest= fields.Boolean(string='inte_cal')
    is_paied= fields.Boolean(string="Paied ?", default=False,compute="_compute_paied")
    expected_payment_date = fields.Date(string="expected payment date",readonly=True)
    value_date = fields.Date(string="Value Date")
    
    principal_repayment=fields.Float('Principal Repayment')
    cumulative_interest  =fields.Float('Cumulative Interest',related='acount_loan_id.cumulative_interest')
    is_interest= fields.Float(string='Interest',)
    is_penality= fields.Float(string='Penalty',)
    total_payment= fields.Float(string='Total Payment')
    payment_term=fields.Char(string='Payment Period',readonly=True)
    acount_loan_id = fields.Many2one(comodel_name='account.loan', string="Parent ID", index=True, ondelete='cascade', required=True)
    is_compound=fields.Boolean( string='compound', related='acount_loan_id.isinterest')
    posted=fields.Boolean(string="Posted?")
    with_out=fields.Boolean(string="with out Penalty?")
    reference=fields.Char(string='Reference',)
    desc=fields.Char(string='Description')
    num=fields.Integer("num",compute="_thisistest" )
    loan_repayment_detail_ids = fields.One2many(
        'account.loan.repayment.detail', 'acount_loan_id', string="Repayment Detail")
    
   
    

    @api.constrains('value_date')
    def _check_date(self):
        for payment in self:
            #if isinstance(record.id, models.NewId):
            cu_payment = self.env['account.loan.repayment'].search([('value_date', '>', payment.value_date),('acount_loan_id','=',payment.acount_loan_id.id)])
            current_date=datetime.today()
            cday = current_date.date()
            # if cu_payment:
            #     raise ValidationError("The Value Date cannot be set in the past of The Previous recod Value Date")
            if payment.value_date:  
                if payment.value_date>cday:
                    raise ValidationError("The Value Date cannot be set in the Furure")
              
    @api.onchange('loan_repayment_detail_ids','num')
    def _thisistest(self):
        for record in self:
            kk=record.num
            penality=0.0000000000000000000000000
            if record.loan_repayment_detail_ids:
                
                intestt=0.000000000000000000000000000
                total_payment=0.00000000000000000000000
                pincipal=0.0000000000000000000000000000
                for detail in record.loan_repayment_detail_ids:
                    penality+=detail.is_penality
                    intestt+=detail.is_interest
                    total_payment+=detail.total_payment
                    pincipal+=detail.principal_repayment
                record.total_payment =total_payment
                record.is_interest =intestt
                record.is_penality =penality
                record.principal_repayment =pincipal
            record.num=penality 
            
    
    @api.onchange("value_date","loan_repayment_detail_ids","num")
    def _compute_paied(self):
        for record in self:
            intest =0.000000000000000000000000000
            paiedint=0.00000000000000000000000000000
                #record.is_interest=0
            theinte=0
            penality=0.00000000000000000000000
            paiedpenality=0.0000000000000000000
            idsids=0
            current_date=datetime.today()
            cday = current_date.date()
            if cday:    
                if record.value_date:
                    
                    
                    if not record.is_paied:
                        if record.is_compound:
                            theinte=0
                            
                            record.principal_repayment=record.total_payment
                        
                        elif not record.is_compound:
                            if isinstance(record.id, models.NewId):
                                idsids=record.acount_loan_id.id.origin
                                cu_interest = self.env['account.loan.int'].search([('value_date', '<', record.value_date),('acount_loan_id','=',record.acount_loan_id.id.origin)])
                            
                                repa_interest=self.env['account.loan.repayment'].search([('value_date', '<', record.value_date),('is_paied','=','True')
                                                                ,('acount_loan_id','=',record.acount_loan_id.id.origin)  ])
                                for cuinte in cu_interest:      
                                    intest+=cuinte.daily_interest_amount
                                    penality+=cuinte.daily_penality_amount
                                for pint in repa_interest:      
                                    paiedint+=pint.is_interest
                                    paiedpenality=pint.is_penality
                            
                                intest=intest-paiedint
                                record.is_penality=penality-paiedpenality
                                
                                if intest>record.total_payment:
                                    theinte=record.total_payment
                                    record.principal_repayment=0
                                elif intest<record.total_payment:
                                    record.principal_repayment=record.total_payment-intest
                                    theinte=intest
                    
                        if (record.value_date<cday):
                            if record.acount_loan_id.payment_month:
                                month=record.acount_loan_id.payment_month
                                dt=record.expected_payment_date+ relativedelta(months=month)
                            inte = self.env['account.loan.int'].search([('value_date','>',record.value_date),('value_date','<=',dt),('acount_loan_id','=',idsids)], 
                            )
                            for interest in inte:
                                if interest.daily_penality_amount:
                                    a= interest.daily_penality_amount
                                    daa=interest.value_date
                                    interest.daily_penality_amount=0
                        
                        
                        record.is_paied = True
                        idddd=0
                        if isinstance(record.id, models.NewId):
                            idddd=record.acount_loan_id.id.origin
                        else:
                            idddd=record.acount_loan_id.id
                        datepaied= record.expected_payment_date+relativedelta(months= record.acount_loan_id.payment_month)
                        acount_payment = self.env['account.loan.repayment'].search(
                                [('expected_payment_date', '=', datepaied), ('acount_loan_id', '=', idddd)])
                        acount_schedulee = self.env['account.loan.schedule'].search(
                                [('payment_date', '=', datepaied), ('acount_loan_id', '=', idddd)])
                        
                        racount_schedule = self.env['account.loan.renew.schedule'].search(
                                [('payment_date', '=', datepaied), ('acount_loan_id', '=', idddd)])
                        amount=0.00000000
                        payment_term='1'
                        payment_term=acount_schedulee.name
                        if racount_schedule:
                            payment_term=racount_schedule.name

                        if acount_schedulee:
                            
                            for schedule in acount_schedulee:
                                amount=schedule.payment_amount
                                payment_term=schedule.name
                                break
                        if racount_schedule:
                            payment_term=schedule.name
                            for schedule in racount_schedule:
                                amount=schedule.payment_amount
                                payment_term=schedule.name
                                break
                        

                        if not acount_payment:
                            payments = self.env['account.loan.repayment'].create({'acount_loan_id': idddd,
                                                                         'expected_payment_date':datepaied, 'total_payment': amount,
                                                                         'payment_term':payment_term})
                            record.acount_loan_id.next_payment_date=datepaied
                            
                        else :
                            acount_payment.payment_term=payment_term
                        if theinte>0:
                            record.is_interest= theinte
                            break
                        ecu_interest = self.env['account.loan.int'].search([('value_date', '<', record.value_date),('acount_loan_id','=',idsids)])
                        for interest in ecu_interest:
                            interest.payied=True
                    record.total_payment =record.is_penality+record.is_interest+record.principal_repayment
                    
                    if (record.value_date<cday):
                        if record.acount_loan_id.payment_month:
                            month=record.acount_loan_id.payment_month
                            dt=record.expected_payment_date+ relativedelta(months=month)
                        inte = self.env['account.loan.int'].search([('value_date','>',record.value_date),('value_date','<=',dt),('acount_loan_id','=',record.acount_loan_id.id)], 
                        )
                        for interest in inte:
                            if interest.daily_penality_amount:
                                a= interest.daily_penality_amount
                                daa=interest.value_date
                                interest.daily_penality_amount=0
                                interest.calculate=False
                    
           
                else: record.is_paied = False
            if record.loan_repayment_detail_ids:
                penality=0.0000000000000000000000000
                intestt=0.000000000000000000000000000
                total_payment=0.00000000000000000000000
                pincipal=0.0000000000000000000000000000
                for detail in record.loan_repayment_detail_ids:
                    penality+=detail.is_penality
                    intestt+=detail.is_interest
                    total_payment+=detail.total_payment
                    pincipal+=detail.principal_repayment
                record.total_payment =intestt+penality+pincipal
                record.is_interest =intestt
                record.is_penality =penality
                record.principal_repayment =pincipal

    

   #penlity calculation and total payment
    # @api.onchange('is_penality')
    # def _compute_penality(self):
    #     for penality in self:
    #        penality.total_payment =penality.is_penality+penality.is_interest+penality.principal_repayment
    @api.depends("value_date")
    def compute_inte(self):
        for record in self:
            
            intest =0.000000000000000000000000000
            paiedint=0.00000000000000000000000000000
            #record.is_interest=0
            theinte=0
            penality=0.00000000000000000000000
            paiedpenality=0.0000000000000000000
            idsids=0
            if not record.loan_repayment_detail_ids:
                if record.value_date:
                    
                    current_date=datetime.today()
                    cday = current_date.date()
                
                    if record.is_compound:
                        theinte=0
                        
                        record.principal_repayment=record.total_payment
                    
                    elif not record.is_compound:
                        if isinstance(record.id, models.NewId):
                            idsids=record.acount_loan_id.id.origin
                            cu_interest = self.env['account.loan.int'].search([('value_date', '<', record.value_date),('acount_loan_id','=',record.acount_loan_id.id.origin)])
                        
                            repa_interest=self.env['account.loan.repayment'].search([('value_date', '<', record.value_date),('is_paied','=','True')
                                                            ,('acount_loan_id','=',record.acount_loan_id.id.origin)  ])
                            for cuinte in cu_interest:      
                                intest+=cuinte.daily_interest_amount
                                penality+=cuinte.daily_penality_amount
                            for pint in repa_interest:      
                                paiedint+=pint.is_interest
                                paiedpenality=pint.is_penality
                        
                            intest=intest-paiedint
                            record.is_penality=penality-paiedpenality
                            
                            if intest>record.total_payment:
                                theinte=record.total_payment
                                record.principal_repayment=0
                            elif intest<record.total_payment:
                                record.principal_repayment=record.total_payment-intest
                                theinte=intest
                
                    if (record.value_date<cday):
                        if record.acount_loan_id.payment_month:
                            month=record.acount_loan_id.payment_month
                            dt=record.expected_payment_date+ relativedelta(months=month)
                        inte = self.env['account.loan.int'].search([('value_date','>',record.value_date),('value_date','<=',dt),('acount_loan_id','=',record.acount_loan_id.id)], 
                        )
                        for interest in inte:
                            if interest.daily_penality_amount:
                                a= interest.daily_penality_amount
                                daa=interest.value_date
                                interest.daily_penality_amount=0
                                interest.calculate=False
                    
                    
                    record.is_paied = True
                    if theinte>0:
                        record.is_interest= theinte
                        break
                    ecu_interest = self.env['account.loan.int'].search([('value_date', '<', record.value_date),('acount_loan_id','=',idsids)])
                    for interest in ecu_interest:
                        interest.payied=True
                record.total_payment =record.is_penality+record.is_interest+record.principal_repayment
                
    @api.onchange('with_out')
    def _compute_penality(self):
        for penality in self:
            if penality.with_out:
                month=penality.acount_loan_id.payment_month
                dt=penality.expected_payment_date+ relativedelta(months=month)
                penality.is_penality=0
                idsids=0
                if isinstance(penality.id, models.NewId):
                    idsids=penality.acount_loan_id.id.origin
                inte = self.env['account.loan.int'].search([('value_date','>',penality.expected_payment_date),
                ('value_date','<=',dt),('acount_loan_id','=',idsids)],)
                for interest in inte:
                    if interest.daily_penality_amount:
                        interest.daily_penality_amount= 0
                        
    
    def open_detail(self):
        view = self.env.ref(
            'droga_treasury.account_loan_payment_detail_tree')
        return {
            'name': 'Payment Detail',
            'view_mode': 'tree',
            'res_model': 'account.loan.repayment.detail',
            'view_id': view.id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
             'context':{'default_acount_loan_id':self.id},
             'domain': [('acount_loan_id', '=', self.id)],
              'target': 'new',
        }

class AccountLoanRepaymentDetail(models.Model):
    
    _name='account.loan.repayment.detail'
    
    value_date = fields.Date(string="Value Date")
    principal_repayment=fields.Float('Principal Repayment')
    is_interest= fields.Float(string='Interest',)
    is_penality= fields.Float(string='Penalty',)
    total_payment= fields.Float(string='Total Payment',compute="_compute_penality")
    acount_loan_id = fields.Many2one(comodel_name='account.loan.repayment', string="Parent ID", index=True, ondelete='cascade', required=True)
    is_compound=fields.Boolean( string='compound', related='acount_loan_id.is_compound')
    reference=fields.Char(string='Reference',)
    desc=fields.Char(string='Description',)
    post=fields.Many2one(string='Account Move',comodel_name='account.move')
   
    @api.depends('is_interest','is_penality','principal_repayment')
    def _compute_penality(self):
        for penality in self:
           penality.total_payment =penality.is_penality+penality.is_interest+penality.principal_repayment
           penality.acount_loan_id.num+=1
                        
    @api.constrains('value_date')
    def _check_date(self):
        for payment in self:
            #if isinstance(record.id, models.NewId):
            cu_payment = self.env['account.loan.repayment.detail'].search([('value_date', '>', payment.value_date),('acount_loan_id','=',payment.acount_loan_id.acount_loan_id.id)])
            current_date=datetime.today()
            cday = current_date.date()
            # if cu_payment:
            #     raise ValidationError("The Value Date cannot be set in the past of The Previous recod Value Date")
            if payment.value_date:  
                if payment.value_date>cday:
                    raise ValidationError("The Value Date cannot be set in the Furure")
    def compute_postt(self):
        for record in self:
            current_date = datetime.today()
            t=0
            cday = current_date.date()
            pday=cday
            acount_recipt = self.env['account.loan'].search([('id', '=', record.acount_loan_id.id)])
              
            journal=record.acount_loan_id.acount_loan_id.account_jornal.id
            account_bank=record.acount_loan_id.acount_loan_id.account_bank.id
            account_disbursement=record.acount_loan_id.acount_loan_id.disbursement.id
            accrued_interest_payable=record.acount_loan_id.acount_loan_id.accrued_interest_payable.id
            lines_vals_list = []

            if  record.value_date:
                pday=record.value_date
            payment = self.env['account.move'].create(
                                    {'date':pday,'journal_id':journal
                                    ,'ref':record.reference,
                                     })                                    
            if payment and not record.post:
                t=payment.id
                lines_vals_list.append({
                    'move_id': t,                   
                    'credit':record.total_payment,
                    'account_id': account_bank                   
                 })
                
                lines_vals_list.append({  
                    'move_id': t,
                    'debit':record.principal_repayment,
                    'account_id': account_disbursement 
                 })
                lines_vals_list.append({  
                    'move_id': t,
                    'debit':record.is_penality+record.is_interest,
                    'account_id': accrued_interest_payable 
                 })
                self.env['account.move.line'].create(lines_vals_list)
                record.post=t