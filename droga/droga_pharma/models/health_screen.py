from email.policy import default
from odoo import models, fields, api

class droga_pharma_health_screening(models.Model):
    _name = 'droga.pharma.health.screening'

    #Text fields
    weight=fields.Float("Weight",required=True)
    #height
    #bmi
    #blood_pressure
    #blood_fasting_glucose
    #pregnancy_test
    #hiv
    #rbs (random blood sugar)

