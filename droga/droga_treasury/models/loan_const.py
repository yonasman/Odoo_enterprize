from datetime import datetime, date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, models
from odoo.exceptions import ValidationError


class AccountLoanConst(models.Model):
    _inherit = 'account.loan'
    
    def compute_daily_cron(self):

        interst_amount = 0.0000000000000000000
        penality_amount = 0.00000000000000000000
        daily_interest_total = 0.0000000000000000
        penal=0.00000000000000000000000000
        current_date = datetime.today()
        cday = current_date.date()-relativedelta(days=1)
        curentday=current_date.date()
        num=0
        nyear = cday.year
        tern=0
        acount_loan = self.env['account.loan'].search(
            [('isactive', '=', True)])

        for predone in acount_loan:
            if predone.next_payment_date:
                predone.remaining_days = (
                    predone.next_payment_date-curentday)/timedelta(days=1)
                if predone.remaining_days <0:
                    predone.overdue_days=0-predone.remaining_days
                    
                    if predone.overdue_days>0 and predone.isactive and predone.interest_start_date:
                        predone.state="overdue"
                else:
                     predone.overdue_days=0
                # if not predone.isactive and predone.interest_start_date and predone.overdue_days>0:
                #     predone.state="overdue"
                if predone.overdue_days==0 and predone.isactive and predone.interest_start_date:
                    predone.state="active"
                elif not predone.interest_start_date:
                    predone.state="draft"



            if predone.cumulative_balance>0:
                acount_sc = self.env['account.loan.renew.schedule'].search(
                    [('id', '>', 0), ('acount_loan_id', '=', predone.id)])
                acount_renew = self.env['account.loan.renew'].search(
                    [('id', '>', 0), ('acount_loan_id', '=', predone.id)])
                for data in acount_renew:
                    if data.id > num:
                        num = data.id
                if cday>= predone.interest_start_date:
                    interst_amount=predone.cumulative_balance*predone.anual_interest_rate/36500
                if predone.isinterest:
                    amount=predone.cumulative_balance+predone.cumulative_interest+predone.cumulative_penality
                    interst_amount=amount*predone.anual_interest_rate/36500
                                
                    if num:
                        renew = self.env['account.loan.renew'].search(
                        [('id', '=', num),('acount_loan_id','=',predone.id)])
                        if renew.renew_start_date:
                            if cday >= renew.renew_start_date:
                                interst_amount=predone.cumulative_balance*renew.anual_interest_rate/36500
                                rstatdate = renew.renew_start_date
                            if predone.isinterest:
                                amount=predone.cumulative_balance+predone.cumulative_interest+predone.cumulative_penality
                                interst_amount=amount*renew.anual_interest_rate/36500
                           
                penality_amount=0 
                penality_range = self.env['account.loan.penality.range'].search(
                                    [('id', '>', 0), ('acount_loan_penality_id', '=', predone.id)], order='id')
                for penality in predone.loan_repayment_ids:
                    ndate = penality.expected_payment_date
                    A=predone.id
                    B=penality.acount_loan_id.id
                    if predone.cumulative_balance<1111:
                        A=predone.id
                        penal
                    if ndate:
                        cdate = ndate
                        rdate = ndate
                        for prange in penality_range:

                            if prange.name == 'upto':
                                
                                if (ndate < cday):
                                    cdate += relativedelta(days=prange.num_days)

                                    if (cday < cdate):
                                            penal = prange.anual_penality_rate/365
                                            break

                            elif prange.name == 'morethan':
                                if (cday > rdate):
                                    penal = prange.anual_penality_rate/365
                                    break
                            rdate = cdate
                        if ndate<cday:
                            penality_amount = penal*predone.cumulative_balance/100
                            break
                # if not penality_range_ids:
                #         penality_amount=0                
                acount_int = self.env['account.loan.int'].search(
                        [('value_date', '=', cday), ('acount_loan_id', '=', predone.id)]) 
                if not acount_int: 
                    daily_int = self.env['account.loan.int'].create(
                                            {'acount_loan_id': predone.id, 'value_date': cday,
                                            'daily_penality_rate': penal, 'daily_interest_rate': predone.daily_interest_rate,
                                            'daily_interest_amount': interst_amount, 'daily_penality_amount': penality_amount,
                                            'daily_interest_total': interst_amount+penality_amount})
                
                starting_days = [[7, 8, 'Hamile'], [8, 7, 'Nehasie'], [9, 11, 'Meskerem'], [10, 11, 'Tikemt'],
                            [11, 10, 'Hidar'], [12, 10, 'Tahesas'], [1, 9, 'Tir'], [2, 8, 'Yekatit'],
                            [3, 10, 'Megabit'], [4, 9, 'Mizia'], [5, 9, 'Ginbot'], [6, 8, 'Senie']]
        # payment generating fpr calculation if payment day = current day
                # if predone.loan_schedule_ids:
                #     if predone.next_payment_date:
                #          if schedule.payment_date < cday:
                #             predone.next_payment_date+

                        
                #         predone.remaining_days = (
                #             predone.next_payment_date-cday)/timedelta(days=1)
                # while predone.next_payment_date < cday:
                #     predone.next_payment_date += relativedelta(
                #         months=predone.payment_month)
                # acount_payment = self.env['account.loan.repayment'].search(
                #     [('expected_payment_date', '=', predone.next_payment_date), ('acount_loan_id', '=', predone.id)])
                # if not acount_payment:
                #     if predone.loan_schedule_ids:
                #         for schedule in predone.loan_schedule_ids:
                #             if schedule.payment_date == predone.next_payment_date:
                #                 payments = self.env['account.loan.repayment'].create({'acount_loan_id': predone.id,
                #                                                                     'expected_payment_date': predone.next_payment_date, 'total_payment': predone.payment,
                #                                                                     'payment_term': schedule.name})
        #converting to habesha day and calculating monthly
                et_years = 0
                add_day = 30
                ayear = 0
                for start_day in starting_days:
                        add_day = 30
                        if cday.month==1 and start_day==[12, 10, 'Tahesas']:
                            nyear = cday.year-1
                        ayear = nyear

                        stday = date(ayear, start_day[0], start_day[1])

                        if tern == 1:
                            add_day = 35
                        closing_day = stday+relativedelta(days=add_day)
                        if ayear % 4 == 3:
                            if tern == 1:
                                closing_day = stday+relativedelta(days=1)
                            elif tern > 1 & tern < 8:
                                closing_day = closing_day+relativedelta(days=1)
                                stday = stday+relativedelta(days=1)
                        if  cday == closing_day:
                            
                            break
                        tern += 1                 
                et_years = ayear-8
                if stday.month > 8:
                    et_years = ayear-7
                if closing_day >= predone.interest_start_date:
                    if cday >= stday:
                        month_acount_recipt = self.env['account.loan.receipt'].search([('value_date', '>=', stday),
                                                                                    ('value_date', '<', closing_day), ('acount_loan_id', '=', predone.id)])
                        monthrecipt = 0
                        for mrecipt in month_acount_recipt:
                            monthrecipt += mrecipt.receipt
                            mrecipt.posted = True
                        monthrepaymentprincipal = 0
                        monthrepaymentinte = 0
                        for apaymente in predone.loan_repayment_ids:
                            
                            month_acount_repayment = self.env['account.loan.repayment.detail'].search([('value_date', '>=', stday),
                                                                                            ('value_date', '<', closing_day),  ('acount_loan_id', '=',apaymente.id)])
                                    
                            for mrepayment in month_acount_repayment:
                                monthrepaymentprincipal += mrepayment.principal_repayment
                                monthrepaymentinte += mrepayment.is_interest
                                    
                            #acount_pint = self.env['account.loan.int'].search([('value_date', '<', da)])
                        month_acount_inte = self.env['account.loan.int'].search([('value_date', '>=', stday),
                                                                                    ('value_date', '<', closing_day), ('acount_loan_id', '=', predone.id)])
                        monthinterest = 0
                        monthpenality = 0
                        i = 0
                        for minterest in month_acount_inte:
                            monthinterest += minterest.daily_interest_amount
                            monthpenality += minterest.daily_penality_amount
                            i += 1
                            minterest.posted = True
                        month_financials = self.env['droga.monthly.close'].search([('closing_day', '=', closing_day),
                                                                                    ('name', '=', start_day[2]), (
                                                                                        'starting_day', '=', stday),
                                                                                    ('acount_monthly_closing_id', '=', predone.id)])
                        if not month_financials:
                            if  stday:
                                month_financial = self.env['droga.monthly.close'].create(
                                        {'acount_monthly_closing_id': predone.id, 'name': start_day[2],
                                        'recipt': monthrecipt, 'penality': monthpenality,
                                        'interest': monthinterest, 'Interest_payment': monthrepaymentinte,
                                        'Principal_payment': monthrepaymentprincipal, 'et_year': et_years,
                                        'starting_day': stday,
                                        'closing_day': closing_day})
                        else:
                            month_financials.recipt= monthrecipt
                            month_financials.penality= monthpenality
                            month_financials.interest= monthinterest
                            month_financials.Interest_payment= monthrepaymentinte
                            month_financials.Principal_payment= monthrepaymentprincipal

    # @api.model
    # def write(self, values):
    #     result = super(AccountLoanConst, self).write(values)
    #     self.env['account.loan']._compute_all_sa()
    #     return result
    # @api.model
    # def write(self, values):
       
    #     res = super(AccountLoanConst, self).write(values)
    #     self.env['account.loan']._compute_all_sa()
        
    #     #call method here
    #     #res=self.compute_all_sa()

    #     return res
    def open_monthly(self):
        view = self.env.ref(
            'droga_treasury.droga_monthly_closeview_tree')
        domain =[('id', 'in', self.monthly_closing_ids)] 
        x= self.monthly_closing_ids.ids
        return {
            'name': 'Payment Detail',
            'view_mode': 'tree,form',
            'res_model': 'droga.monthly.close',
            #'view_id': view.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            # 'filter_domain': {'acount_monthly_closing_id':[('id', '=', self.id)]},
            #'domain':{'acount_monthly_closing_id':[('id', 'in', self.id)]},
            'domain': [('acount_monthly_closing_id', '=', self.id)],
            #'context':{'default_acount_monthly_closing_id':self.id,'search_default__acount_monthly_closing_id': [self.id],}
        }

    @api.constrains('interest_start_date', 'contract_date', 'payment_start_date',
                    'loan_repayment_ids', 'loan_receipt_ids', 'payment', 'loan_amount')
    def _check_date(self):
        for loans in self:
            current_date = datetime.today()
            cday = current_date.date()
            recipts=0
            for recipt in loans.loan_receipt_ids:
                recipts+=recipt.receipt
            if recipts>loans.loan_amount:
                raise ValidationError(
                    "The receipts cannot be greater than the Loan amount")

            

            if loans.payment_start_date:
                if loans.contract_date > loans.payment_start_date:
                    raise ValidationError(
                        "The Payment start date cannot be set in the past of the contract date")

            # if not loans.interest_start_date:
                #raise ValidationError("Please insert the first receipt")
            if loans.current_cumlative_balace>0:
                if not loans.opening_date :
                     raise ValidationError(
                        "Please enter The Opening Date")
                # if loans.opening_date and not loans.opening_payment_date:
                #      raise ValidationError(
                #         "Please enter The Opening Payment start Date")
              
            if loans.interest_start_date:
                if loans.contract_date > loans.interest_start_date:
                    raise ValidationError(
                        "The Interest Start Date cannot be set in the past of The Contract Date")
                # if loans.interest_start_date > loans.payment_start_date:
                #     raise ValidationError(
                #         "The Payment start date cannot be set in the past the first receipt date")
            if loans.contract_date > cday:
                raise ValidationError(
                    "The Contract Date cannot be set in the Future")

            if loans.loan_amount <= 0:
                raise ValidationError("Please enter the proper Loan Amount")
            if loans.anual_interest_rate <= 0 or loans.anual_interest_rate >100:
                raise ValidationError(
                    "Please enter the proper amount of Anual Interst Rate %(1-100)")
            if loans.payment_month <= 0:
                raise ValidationError(
                    "Please enter the proper amount of Payment Ranage in Month ")

            if loans.payment <= 0:
                raise ValidationError(
                    "Please enter the proper amount of Payment Amount per Period ")

            if loans.loan_period_year <= 0:
                raise ValidationError(
                    "Please enter the proper Period in years ")
            for payments in loans.loan_repayment_ids:
                if payments.value_date:
                    if payments.value_date < loans.contract_date:
                        raise ValidationError(
                            "The payment Date can not be in the past of Contract Date ")
                    if payments.value_date < loans.interest_start_date:
                        raise ValidationError(
                            "The payment Date can not be in the past of The first recipt")
                # if payments.value_date<loans.anual_interest_rate:
                #     raise ValidationError("The First recipt Date can not be in the past of payment Date")

            for payments in loans.loan_receipt_ids:
                if payments.value_date:
                    if payments.value_date < loans.contract_date:
                        raise ValidationError(
                            "The Contract Date can not be in the past of Recipt Date")

            # if loans.contract_date>loans.loan_repayment_ids.value_date:
            #     raise ValidationError("The Value Date cannot be set in the past of The Contract Date ")
            # if loans.contract_date>loans.loan_receipt_ids.value_date:
            #     raise ValidationError("The Value Date cannot be set in the past of TheContract Date")
   
   # @api.onchange('loan_type', 'loan_repayment_ids', 'anual_interest_rate')
   
    # def _compute_all_sa(self):

    #     interst_amount = 0.000000000000000000000000000000000000000000000000000
    #     penality_amount = 0.00000000000000000000000000000000000000000000000000000
    #     daily_interest_total = 0.00000000000000000000000000000000000000000000000000000
    #     current_date = datetime.today()
    #     num = 0
    #     rint = 0.000000000000000000000000000000000000000000000000000000000000
    #     rpint = 0.00000000000000000000000000000000000000000000000000000000000000
    #     penal = 0.00000000000000000000000000000000000000000000000000000000000000
    #     cday = current_date.date()
    #     rstatdate = cday
    #     daq = 0
    #     idddd=0
    #     if isinstance(self.id, models.NewId):
    #         idddd=self.id.origin
    #     else:
    #         idddd=self.id
    #     acount_loan = self.env['account.loan'].search(
    #         [('id', '=', idddd)])
    #     if acount_loan:
    #         for predone in acount_loan:
    #             predone.calculatess=True
    #             acount_sc = self.env['account.loan.renew.schedule'].search(
    #                 [('id', '>', 0), ('acount_loan_id', '=', idddd)])
    #             day_int = predone.daily_interest_rate
                
                
    #             acount_renew = self.env['account.loan.renew'].search(
    #                 [('id', '>', 0), ('acount_loan_id', '=', idddd)])
    #             for data in acount_renew:
    #                 if data.id > num:
    #                     num = data.id

    #             da = predone.interest_start_date
    #             while cday >= da:
    #                 closing_day = cday
    #                 stday = cday
    #                 tern = 0
    #                 add_day = 0
    #                 ayear = 0
    #                 nyear = da.year
    #                 et_years = 0

    #                 if num:
    #                     renew = self.env['account.loan.renew'].search(
    #                         [('id', '=', num)])
    #                     if renew.renew_start_date:
    #                         if da >= renew.renew_start_date:
    #                             rint = renew.anual_interest_rate/365
    #                             rpint = renew.anual_penality_rate/365
    #                             rstatdate = renew.renew_start_date
    #                 if rstatdate > da:
    #                     day_int = predone.daily_interest_rate
    #                     day_pint = predone.daily_penalit_rate

    #                 else:
    #                     if rint > 0:
    #                         day_int = rint
    #                         day_pint = rpint
    #                 acount_recipt = self.env['account.loan.receipt'].search([('value_date', '<=', da),
    #                                                                         ('acount_loan_id', '=', idddd)])
    #                 crecipt = 0
    #                 for recipt in acount_recipt:
    #                     crecipt += recipt.receipt
    #                 acount_repay = self.env['account.loan.repayment.detail'].search(
    #                     [('value_date', '<=', da),  ('acount_loan_id', '=', idddd)])
    #                 crepay = 0
    #                 for apayment in acount_repay:
    #                     crepay += apayment.principal_repayment

    #         # repayment schedule
                
    #         # penality calculation
    #                 penal = 0
    #                 cumulative_balance = predone.current_cumlative_balace+crecipt-crepay
    #                 interst_amount = day_int*cumulative_balance/100
    #                 acount_int = self.env['account.loan.int'].search(
    #                     [('value_date', '=', da), ('acount_loan_id', '=', idddd)])
                   
    #                 if acount_int:
    #                     for penality in predone.loan_repayment_ids:
    #                         ndate = penality.expected_payment_date
    #                         if ndate:
    #                             cdate = ndate
    #                             rdate = ndate

    #                             penality_range = self.env['account.loan.penality.range'].search(
    #                                 [('id', '>', 0), ('acount_loan_penality_id', '=', idddd)], order='id')
    #                             for prange in predone.penality_range_ids:

    #                                 if prange.name == 'upto':
    #                                     cdate += relativedelta(days=prange.num_days)
    #                                     if (ndate < da):

    #                                         if (da < cdate):
    #                                             penal = prange.anual_penality_rate/365
    #                                             break

    #                                 elif prange.name == 'morethan':
    #                                     if (da > rdate):
    #                                         penal = prange.anual_penality_rate/365
    #                                         break
    #                                 else: 
    #                                     penal=0
    #                                 # if da>cdate:
    #                                 #     cdate+=relativedelta(days=prange.num_days)
    #                                     rdate = cdate

    #                             if ndate:
    #                                 if (ndate < da):

                                    

    #                                     # penal=0
    #                                     penality_amount = penal*cumulative_balance/100
                                       
    #         # INTEREST UPDATING

    #         # itnerest creating
    #                       # INTEREST UPDATING
                    
    #                             acount_int.daily_penality_rate = day_pint
    #                             acount_int.daily_interest_rate = day_int
    #                             acount_int.daily_interest_amount = interst_amount
    #                             if penality_amount>0:
    #                                 acount_int.daily_penality_amount = penality_amount
    #                             #acount_int.daily_interest_total = interst_amount+penality_amount
    #                 da = da + relativedelta(days=1)

            