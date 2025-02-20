from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


# from dateutil.relativedelta import relativedelta


class AccountLoan(models.Model):
    _name = "account.loan"
    _description = "Loan"

    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']

    name = fields.Many2one('res.bank', string="Bank", required=True)

    loan_type = fields.Many2one(
        'account.loan.type', string="Loan Type", required=True)

    loan_statement_number = fields.Char('Loan Statment Number', required=True)
    state=fields.Selection([
        ('draft','Draft'),('active','Active'),
            ('overdue', 'Overdue'),
            ('done', 'Done')],
            string="Status",default='draft', required=True
    )

    @api.depends("payment_month", "loan_period_year", "payment_start_date")
    def _compute_yearr(self):
        for record in self:
            current_date = datetime.today()

            cday = current_date.date()
            pe = 0.000000000000000
            if record.payment_month:
                pe = 12/record.payment_month
            record.schedule_numberof_payment = pe

            record.total_number_of_payment = pe*record.loan_period_year
            if record.loan_period_year < 1:
                record.schedule_numberof_payment = record.total_number_of_payment
            if not record.next_payment_date:
                if record.payment_start_date:
                    record.next_payment_date = record.payment_start_date
                    record.remaining_days = (
                        record.next_payment_date-cday)/timedelta(days=1)

    # @api.depends("payment_month","total_number_of_payment","payment","payment_start_date")
    def compute_schedule(self):
        for record in self:
            nloop = 0.00000000000000
            inte = 0
            dayint = 0.000
            ipay = 0.00000
            rint = 0.0000
            ppay = 0.00000
            payments = 0.00000
            cpay = 0.00000
            mul = 0
            self.env["account.loan.schedule"].search(
                [('id', '>', 0), ('acount_loan_id', '=', record.id)]).unlink()

            payment = record.payment
            if record.payment_month:
                if record.payment:
                    if record.total_number_of_payment:
                        if record.payment_start_date and record.interest_start_date:
                            nloop = record.total_number_of_payment
                            i = 0
                            balance = record.loan_amount

                            while nloop > 0:
                                month = i*record.payment_month
                                dt = record.payment_start_date + \
                                    relativedelta(months=month)
                                if i == 0:
                                    if record.interest_start_date:
                                        inte = record.payment_start_date-record.interest_start_date
                                else:
                                    inte = dt-at
                                    
                                s=timedelta(days=1)    
                                mul = inte/s
                                if mul < 0:
                                    mul = -1*mul
                                dayint = record.daily_interest_rate*mul*balance/100

                                rint = +dayint
                                tot = balance+rint
                                if tot < record.payment:
                                    ipay = rint
                                    ppay = balance
                                    payment = tot
                                    cpay = 0
                                elif rint > record.payment:
                                    ipay = record.payment
                                    rint = rint-record.payment
                                    ppay = 0
                                    cpay = ppay+ipay
                                else:
                                    if record.payment > rint:
                                        ipay = dayint
                                        ppay = record.payment-ipay
                                        cpay = ppay+ipay

                                balance = balance-ppay

                                if not record.isinterest:
                                    schedule = self.env['account.loan.schedule'].create(
                                        {'acount_loan_id': record.id, 'payment_date': dt, 'payment_amount': payment,
                                            'name': i+1, 'prencipal': ppay, 'interest': ipay, 'balance': balance})
                                elif record.isinterest:
                                    schedule = self.env['account.loan.schedule'].create(
                                        {'acount_loan_id': record.id, 'payment_date': dt, 'payment_amount': payment,
                                            'name': i+1, 'prencipal': cpay, 'interest': 0, 'balance': balance+rint})
                                at = dt
                                nloop -= 1
                                i = i+1
                        else:
                             raise ValidationError(
                                "You shoud enter The receipts to run schedule")


# Date
    next_payment_date = fields.Date(string="Next Payment Date", readonly=True)
    payment_start_date = fields.Date("Payment Start Date",readonly=True)
    interest_renew_date = fields.Date(
        "Interst Renew Date", compute="compute_renew")
    interest_start_date = fields.Date("Interst Start Date", readonly=True)
    contract_date = fields.Date('Contract Date',required=True)
    opening_date = fields.Date('Opening Date')
    opening_payment_date = fields.Date('Payment Start Date')
# integer
    remaining_days = fields.Integer(string="Remaining Days", readonly=True)
    overdue_days = fields.Integer(string="Overdue", readonly=True)
    payment_month = fields.Integer('Repayment Interval',required=True)


# flaot
    payment = fields.Float('Repayment Amount', required=True)

    loan_period_year = fields.Float('Period in Years',required=True)
    loan_amount = fields.Float('Loan Amount', required=True)
    schedule_numberof_payment = fields.Float(
        'Payments Per Year', compute="_compute_yearr")
    total_number_of_payment = fields.Float(
        'Total Number Of Payments', compute="_compute_yearr")
    anual_interest_rate = fields.Float('Anual Interst Rate %', required=True,digits=(12, 15))
    daily_interest_rate = fields.Float(
        'Daily Interst Rate %', compute="_compute_interestdaily", digits=(12, 15))

    current_cumlative_balace = fields.Float('Start Outstanding Balance')
    current_cumlative_interest = fields.Float('Start Outstanding Interest')
    current_interest_total = fields.Float('Current Interest Total')
    anual_penalit_rate = fields.Float('Anual Penalty Rate %',digits=(12, 15))
    daily_penalit_rate = fields.Float(
        'Daily Penalty Rate %', compute="_compute_penalitydaily", digits=(12, 15))
    # schedule_payment_=fields.Float('Schedule Payment')
    grace_period = fields.Float('Grace Period')
    total_interest = fields.Float(
        'Total Interst', compute='_compute_total_interest')
    cumulative_interest = fields.Float(
        'Outstanding interest', compute='_compute_total_interest')
    cumulative_penality = fields.Float(
        'Outstanding Penalty', compute='_compute_total_interest')
    total_penality = fields.Float(
        'Total Penalty', compute='_compute_total_interest')
    cumulative_balance = fields.Float(
        compute='_compute_qty_amount', string="Outstanding Principal Balance")

# boolean
    isinterest = fields.Boolean(
        string="Compound Interest?", compute='_compute_isinterest')
    isactive = fields.Boolean(string="Active?", default=True)
    isdone = fields.Boolean(string="Done?")
    isposted = fields.Boolean(string="Posted?")
# one2many
    loan_repayment_ids = fields.One2many(
        'account.loan.repayment', 'acount_loan_id', string="Repayment")
    loan_receipt_ids = fields.One2many(
        'account.loan.receipt', 'acount_loan_id', string="Receipt")
    loan_schedule_ids = fields.One2many(
        'account.loan.schedule', 'acount_loan_id', string="Schedule")
    loan_interest_ids = fields.One2many(
        'account.loan.int', 'acount_loan_id', string="Interest")
    loan_renew_ids = fields.One2many(
        'account.loan.renew', 'acount_loan_id', string="Renew")
    loan_old_ids = fields.One2many(
        'account.loan.renew.schedule', 'acount_loan_id', string="Renewed Schedule")
    penality_range_ids = fields.One2many(
        'account.loan.penality.range', 'acount_loan_penality_id', string="Penalty Range")
    monthly_closing_ids = fields.One2many(
        'droga.monthly.close', 'acount_monthly_closing_id', )
    calculatess = fields.Boolean(
        string="Compound Interest?", compute='_compute_all_sa')
#company and financial
    company_id = fields.Many2one(
        'res.company', 'Company', index=True,
        default=lambda self: self.env.company)
    account_penality = fields.Many2one(
        'account.account', 'Penalty'
       ,required=True)
   
    account_interest = fields.Many2one(
        'account.account', 'Interest',required=True)
   
    account_bank = fields.Many2one(
        'account.account', 'Bank',required=True)
   
    disbursement = fields.Many2one(
        'account.account', 'Disbursement',required=True)
    accrued_interest_payable = fields.Many2one(
        'account.account', 'Accrued Interest payable',required=True)
   

    account_jornal = fields.Many2one(
        'account.journal', 'Journal',required=True)
    account_jornal_inte = fields.Many2one(
        'account.journal', 'Journal Interest',required=True)
   

     

    #loan_renews_ids = fields.One2many('account.loan.renews', 'acount_loan_id', string="Renews")

    @api.depends('loan_renew_ids')
    def compute_renew(self):
        for record in self:
            self.env["account.loan.renew.schedule"].search(
                [('id', '>', 0), ('acount_loan_id', '=', record.id)]).unlink()

            balance = 0.00000000000000000000
            tinte = 0.0000000000000000000000000000
            num = 0
            current_date = datetime.today()

            cday = current_date.date()
            tday = cday
            taddnum = 0
            ydate = record.next_payment_date
            zdate = record.payment_start_date
            mot = 0
            tadd = 0
            payment = 0.00000000000000000000000000000000000000000000000000
            aint = 0.0000000000000000000000000000000000000000000000000000000000
            total_len = self.env['account.loan.repayment'].search_count([('value_date', '<', ydate),
                                                                         ('acount_loan_id', '=', record.id)])

            acount_renew = self.env['account.loan.renew'].search(
                [('id', '>', 0)])
            for data in acount_renew:
                if data.id > num:

                    num = data.id
            if num:
                renew = self.env['account.loan.renew'].search(
                    [('id', '=', num)])

                if renew:
                    balance = renew.cumulative_balance
                    tinte = renew.cumulative_interest
                    tday = renew.renew_start_date
                    mot = renew.payment_month
                    tadd = renew.addtional_payment
                    payment = renew.payment_amount
                    aint = renew.anual_interest_rate/365

                    if ydate < tday:
                        while ydate < tday:
                            ydate = ydate+relativedelta(months=mot)

        for record in self:
            total_sch = self.env['account.loan.schedule'].search_count(
                [('payment_date', '>', tday), ('acount_loan_id', '=', record.id), ])

            tadd = tadd+total_sch
            inte = 0
            dayint = 0.0000000000000000000000000000000000000000
            ipay = 0.000000000000000000000000000000000000000000
            rint = tinte
            ppay = 0.00000000000000000000000000000000000000000000000

            cpay = 0.00000
            i = 0
            while tadd > 0:
                month = i*mot
                dt = ydate + relativedelta(months=month)
                if i == 0:
                    if tday:
                        inte = zdate-tday
                else:
                    inte = dt-at
                mul = inte/timedelta(days=1)
                if mul < 0:
                    mul = -1*mul
                dayint = aint*mul*balance/100

                rint = +dayint
                tot = balance+rint
                if tot < payment:
                    ipay = rint
                    ppay = balance
                    payment = tot
                    cpay = 0
                elif rint > payment:
                    ipay = payment
                    rint = rint-payment
                    ppay = 0
                    cpay = ppay+ipay
                else:
                    if payment > rint:
                        ipay = dayint
                        ppay = payment-ipay
                        cpay = ppay+ipay

                balance = balance-ppay

                if not record.isinterest:
                    schedule = self.env['account.loan.renew.schedule'].create(
                        {'acount_loan_id': record.id, 'payment_date': dt, 'payment_amount': payment,
                         'name': i+1, 'prencipal': ppay, 'interest': ipay, 'balance': balance})
                elif record.isinterest:
                    schedule = self.env['account.loan.renew.schedule'].create(
                        {'acount_loan_id': record.id, 'payment_date': dt, 'payment_amount': payment,
                         'name': i+1, 'prencipal': cpay, 'interest': 0, 'balance': balance+rint})
                at = dt
                tadd -= 1
                i = i+1

    payment_gene = fields.Boolean(string="Gen?")
    num = fields.Integer('term')
     
    def compute_daily_crons(self):

        interst_amount = 0.00000000000000000
        penality_amount = 0.0000000000000000
        daily_interest_total = 0.0000000000000000
        
        num = 0
        rint = 0.00000000000000000000000
        rpint = 0.000000000000000000000
        penal = 0.000000000000000000000
        current_date = datetime.today()
        cday = current_date.date()
        rstatdate = cday
        daq = 0
        tern=0
        starting_days = [[7, 8, 'Hamile'], [8, 7, 'Nehasie'], [9, 11, 'Meskerem'], [10, 11, 'Tikemt'],
                            [11, 10, 'Hidar'], [12, 10, 'Tahesas'], [
                                1, 9, 'Tir'], [2, 8, 'Yekatit'],
                            [3, 10, 'Megabit'], [4, 9, 'Mizia'], [5, 9, 'Ginbot'], [6, 8, 'Senie']]
   
        acount_loan = self.env['account.loan'].search(
            [('isactive', '=', True)])

        for predone in self:
            #if predone.
            acount_sc = self.env['account.loan.renew.schedule'].search(
                [('id', '>', 0), ('acount_loan_id', '=', predone.id)])
            day_int = predone.daily_interest_rate
            day_pint = predone.daily_penalit_rate

            if predone.next_payment_date:
                predone.remaining_days = (
                    predone.next_payment_date-cday)/timedelta(days=1)

            acount_renew = self.env['account.loan.renew'].search(
                [('id', '>', 0), ('acount_loan_id', '=', predone.id)])
            for data in acount_renew:
                if data.id > num:
                    num = data.id

            da = predone.interest_start_date
            if da:

                while cday >= da:
                    closing_day = cday
                    stday = cday
                    tern = 0
                    add_day = 0
                    ayear = 0
                    nyear = da.year
                    et_years = 0

                    if num:
                        renew = self.env['account.loan.renew'].search(
                            [('id', '=', num),('acount_loan_id','=',predone.id)])
                        if renew.renew_start_date:
                            if da >= renew.renew_start_date:
                                rint = renew.anual_interest_rate/365
                                rpint = renew.anual_penality_rate/365
                                rstatdate = renew.renew_start_date
                    if rstatdate > da:
                        day_int = predone.daily_interest_rate
                        day_pint = predone.daily_penalit_rate

                    else:
                        if rint > 0:
                            day_int = rint
                            day_pint = rpint
                    acount_recipt = self.env['account.loan.receipt'].search([('value_date', '<=', da),
                                                                             ('acount_loan_id', '=', predone.id)])
                    crecipt = 0
                    for recipt in acount_recipt:
                        crecipt += recipt.receipt
                    crepay = 0
                    for apaymente in predone.loan_repayment_ids:
                        acount_repay = self.env['account.loan.repayment.detail'].search(
                            [('value_date', '<=', da),  ('acount_loan_id', '=',apaymente.id)])

                        for apayment in acount_repay:
                            crepay += apayment.principal_repayment
                            if da==apayment.value_date:
                                break


            # repayment
                    
                    if predone.loan_schedule_ids:
                        for schedule in predone.loan_schedule_ids:
                            if schedule.payment_date < da:
                                acount_payment = self.env['account.loan.repayment'].search(
                                    [('expected_payment_date', '=', schedule.payment_date), ('acount_loan_id', '=', predone.id)])
                                # if not acount_payment:
                                #     payments = self.env['account.loan.repayment'].create({'acount_loan_id': predone.id,
                                #                                                           'expected_payment_date': schedule.payment_date, 'total_payment': predone.payment,
                                #                                                           'payment_term': schedule.name})

            # penality calculation
                        penal = 0
                        cumulative_balance = predone.current_cumlative_balace+crecipt-crepay
                        interst_amount = day_int*cumulative_balance/100
                        acount_int = self.env['account.loan.int'].search(
                            [('value_date', '=', da), ('acount_loan_id', '=', predone.id)])
                        acount_pint = self.env['account.loan.int'].search(
                            [('value_date', '<', da), ('acount_loan_id', '=', predone.id)])
                        penality_amount=0.0000000000000000000000000000000000000
                        cumulinterestpenal=0.0000000000000
                        # if acount_int:
                        acount_pinte = self.env['account.loan.int'].search([('value_date', '<=', da),
                                                                             ('acount_loan_id', '=', predone.id)])
                    
                        for inpen in acount_pinte:
                            cumulinterestpenal += inpen.daily_interest_amount+inpen.daily_penality_amount
                            
                        if predone.isinterest:
                            amount = cumulative_balance + cumulinterestpenal -interst_amount
                            interst_amount = amount * predone.anual_interest_rate / 36500
                        for penality in predone.loan_repayment_ids:
                            #penality_amount=0
                            ndate = penality.expected_payment_date
                            if ndate:
                                cdate = ndate
                                rdate = ndate

                                penality_range = self.env['account.loan.penality.range'].search(
                                        [('id', '>', 0), ('acount_loan_penality_id', '=', predone.id)], order='id')
                                for prange in penality_range:

                                    if prange.name == 'upto':
                                        cdate += relativedelta(days=prange.num_days)
                                        if (ndate < da):

                                            if (da < cdate):
                                                penal = prange.anual_penality_rate/365
                                                break

                                    elif prange.name == 'morethan':
                                        if (da > rdate):
                                            penal = prange.anual_penality_rate/365
                                            break
                                        # if da>cdate:
                                        #     cdate+=relativedelta(days=prange.num_days)
                                        rdate = cdate

                            if ndate:
                                if ndate < da:

                                        #  if not penality.is_paied:

                                    if ndate<da:
                                        penality_amount=0
                                        penality_amount = penal*cumulative_balance/100
                                        break
                            break

                        t=penality_amount
                        if not acount_int :

                            daily_int = self.env['account.loan.int'].create(
                                {'acount_loan_id': predone.id, 'value_date': da,
                                'daily_penality_rate': day_pint, 'daily_interest_rate': day_int,
                                'daily_interest_amount': interst_amount, 'daily_penality_amount': penality_amount,
                                'daily_interest_total': interst_amount+penality_amount})
                # INTEREST UPDATING
                        else:
                            # if not acount_int.posted:
                            acount_int.daily_penality_rate = day_pint
                            acount_int.daily_interest_rate = day_int
                            acount_int.daily_interest_amount = interst_amount
                            acount_int.daily_penality_amount = penality_amount
                            #if penality_amount>0 and acount_int.calculate:
                            #    acount_int.daily_penality_amount = penality_amount
                            acount_int.daily_interest_total = interst_amount+penality_amount
                        
                    da = da + relativedelta(days=1)

    # post data on each month

                    for start_day in starting_days:
                        add_day = 30
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
                        if  da == closing_day:

                            break
                        tern += 1

                    et_years = ayear-8
                    if stday.month > 8:
                        et_years = ayear-7

                    if closing_day >= predone.interest_start_date:

                        if da >= stday:
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

                while predone.next_payment_date < cday:
                    predone.next_payment_date += relativedelta(
                        months=predone.payment_month)
                    acount_payment = self.env['account.loan.repayment'].search(
                        [('expected_payment_date', '=', predone.next_payment_date), ('acount_loan_id', '=', predone.id)])
                    if not acount_payment:
                        if predone.loan_schedule_ids:
                            for schedule in predone.loan_schedule_ids:
                                if schedule.payment_date == predone.next_payment_date:
                                    payments = self.env['account.loan.repayment'].create({'acount_loan_id': predone.id,
                                                                                        'expected_payment_date': predone.next_payment_date, 'total_payment': predone.payment,
                                                                                        'payment_term': schedule.name})

    """  #calculating cumulative amount with the formula
    cumulative balance= loan amount+recit-payment some payment are 
    for interest and not calculated
    in some case interest can be added
    cumulative balance=loan amount+reciet+interest-payment """

    
    @api.depends('loan_repayment_ids', 'loan_receipt_ids', 'loan_interest_ids', 'current_cumlative_balace','payment_month')
    def _compute_qty_amount(self):
        for line in self:
            balance = 0.00000000000000000000000000000
            repay = 0.000000000000000000000000000000000
            reciep = 0.000000000000000000000000000000000000000000
            interest = 0.000000000000000000000000000000000000000
            penality=0.000000000000000000000000000000000000000

            recipt = self.env['account.loan.receipt'].search(
                [('id', '>', 0), ('acount_loan_id', '=', line.id)], order='id', limit=1)
            if recipt:
                line.interest_start_date = recipt.value_date
                
                line.payment_start_date=recipt.value_date+relativedelta(months=line.payment_month)-relativedelta(days=1)
                if line.loan_schedule_ids:

                    idddd=0
            if line.current_cumlative_balace and line.opening_date:
                line.interest_start_date=line.opening_date
                line.payment_start_date=line.opening_payment_date
            # if line.interest_start_date:
            #     line.payment_start_date=line.payment_start_date-relativedelta(days=1)
                    
            if line.current_cumlative_balace:
                if line.opening_date:
                    line.interest_start_date=line.opening_date
            
            if line.opening_date or recipt:
                pay=self.env['account.loan.repayment'].search(
                [('id', '>', 0), ('acount_loan_id', '=', line.id)], order='id', limit=1)
                acount_payment = self.env['account.loan.repayment'].search(
                                [ ('id', '=', pay.id)])
                if not  acount_payment:
                    payments = self.env['account.loan.repayment'].create({'acount_loan_id': line.id,
                                                                            'expected_payment_date': line.payment_start_date, 'total_payment': line.payment,
                                                                                 'payment_term':'1'})
                    line.next_payment_date = line.payment_start_date                                                         
                else:
                    line.next_payment_date = line.payment_start_date 
                    acount_payment.expected_payment_date=line.payment_start_date
                    acount_payment.total_payment=line.payment
                
           #""" calculating total reciept """
            for reciept in line.loan_receipt_ids:
                reciep += reciept.receipt

            if line.isinterest:
                for repayment in line.loan_repayment_ids:
                    repay += repayment.principal_repayment
            else:
                for repayment in line.loan_repayment_ids.loan_repayment_detail_ids:

                        # if not repayment.is_interest:
                    repay += repayment.principal_repayment
                    acount_int = self.env['account.loan.int'].search(
                            [('value_date', '<=', repayment.value_date), ('acount_loan_id', '=', line.id)])

            # """ calculating total repayment """
            if line.isinterest:
                for inter in line.loan_interest_ids:
                    interest += inter.daily_interest_total

            balance = reciep+-repay
            line.cumulative_balance = balance+line.current_cumlative_balace

    @api.depends('loan_interest_ids', 'loan_repayment_ids', 'current_cumlative_interest')
    def _compute_total_interest(self):
        for record in self:
            current_date = datetime.today()
            cday = current_date.date()

            

            itotal = 0.00000000000000000000000000
            value = 0.00000000000000000000000000000
            repaymenti = 0.000000000000000000000000000
            ctotal = 0.00000000000000000000000000000
            ptotal=0.000000000000000000000000000000000000000000
            pctotal=0.000000000000000000000000000000000000000000
            repaymentp = 0.000000000000000000000000000
            for inter in record.loan_interest_ids:
                itotal += inter.daily_interest_amount
                ptotal+=inter.daily_penality_amount

            record.total_interest = itotal+record.current_interest_total
            record.total_penality=ptotal
            for repay in record.loan_repayment_ids:
                    # if repay.is_interest:
                    
                repaymenti += repay.is_interest
                repaymentp+=repay.is_penality
            ctotal = itotal
            value = ctotal-repaymenti
            pctotal=ptotal-repaymentp

            record.cumulative_interest = value+record.current_cumlative_interest
            record.cumulative_penality=pctotal

    @api.depends("loan_type")
    def _compute_isinterest(self):
        for record in self:
            record.isinterest = record.loan_type.isinterest

    def compute_done(self):
        for record in self:
            
            record.isactive = False
            record.state="done"


    @api.depends("anual_interest_rate")
    def _compute_interestdaily(self):
        for record in self:
            record.daily_interest_rate = record.anual_interest_rate/365
           # loan=self.env['account.loan']._compute_all_sa()
    # daily penality calculation
    @api.depends("anual_penalit_rate")
    def _compute_penalitydaily(self):
        for record in self:
            record.daily_penalit_rate = record.anual_penalit_rate/365
# ceating closing date


class AccountLoanSchedule(models.Model):
    _name = 'account.loan.schedule'

    name = fields.Char(string='Peyment term', readonly=True)
    payment_date = fields.Date(string="Payment Date", readonly=True)

    acount_loan_id = fields.Many2one(
        comodel_name='account.loan', string="Parent ID", readonly=True)
    payment_amount = fields.Float(string="Payment", readonly=True)
    interest = fields.Float(string="Interest", readonly=True)
    prencipal = fields.Float(string="Prencipal", readonly=True)
    balance = fields.Float(string="Remaining Balance", readonly=True)

    @api.model
    def write(self, values):
        result = super(AccountLoanSchedule, self).write(values)
        return result

    @api.model
    def create(self, values):
        return super(AccountLoanSchedule, self).create(values)


