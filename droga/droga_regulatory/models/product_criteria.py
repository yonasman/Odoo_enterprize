from odoo import models, fields

class Medicine(models.Model):
    _name = 'product.criteria'
    _description = 'Medicine'

    criteria_name = fields.Char(string='Configration Name')

    level_of_professionals = fields.Selection([
        ('general', 'General'),
        ('specialty', 'Specialty')
    ], string='Level of Professionals')
    can_be_substituted = fields.Boolean(string='Can be Substituted')
    manufactured_locally = fields.Boolean(string='Manufactured Locally')
    used_for_chronic_disease = fields.Boolean(string='Used for Chronic Disease')
    government_priority = fields.Boolean(string='Government Priority')
    efda_gmp_approval = fields.Boolean(string='EFDA GMP Approval')

    prevalence_of_indication_low = fields.Integer(string='Prevalence of Indication Lowest value')
    prevalence_of_indication_high = fields.Integer(string='Prevalence of Indication Highest value')
    prevalence_of_indication_weight = fields.Integer(string='Prevalence of Indication Weight')

    number_of_dose_low = fields.Float(string='Number of Dose Lowest Value')
    number_of_dose_high = fields.Float(string='Number of Dose Highest value')
    number_of_dose_weight = fields.Float(string='Number of Dose Weight')

    future_demand_low = fields.Float(string='Future Potential Demand Lowest value')
    future_demand_high = fields.Float(string='Future Potential Demand Highest Value')
    future_demand_weight = fields.Float(string='Future Potential Demand Weight')

    registered_competitors_low = fields.Float(string='Registered Competitors Lowest Value')
    registered_competitors_high = fields.Float(string='Registered Competitors Highest Value')
    registered_competitors_weight = fields.Float(string='Registered Competitors Weight')

    market_usage_low = fields.Float(string='Markt Usage Lowest Value')
    market_usage_high = fields.Float(string='Markt Usage Highest Value')
    market_usage_weight = fields.Float(string='Markt Usage Weight')

    unique_specialty_medicine_low = fields.Float(string='Unique Specialty Medicine Lowest value')
    unique_specialty_medicine_high = fields.Float(string='Unique Specialty Medicine Highest value')
    unique_specialty_medicine_weight = fields.Float(string='Unique Specialty Medicine Weight')

    demand_varies_by_season_low = fields.Float(string='Demand Varies by Season Loest Value')
    demand_varies_by_season_high = fields.Float(string='Demand Varies by Season Highest Value')
    demand_varies_by_season_weight = fields.Float(string='Demand Varies by Season Weight')

    expensive_medicine_low = fields.Float(string='Expensive Medicine Lowest Value')
    expensive_medicine_high = fields.Float(string='Expensive Medicine Highest Value')
    expensive_medicine_Weight = fields.Float(string='Expensive Medicine Weight')

    program_medicine_low = fields.Float(string='Program Medicine Lowest Value')
    program_medicine_high = fields.Float(string='Program Medicine Highest Value')
    program_medicine_weight = fields.Float(string='Program Medicine Weight')

    storage_mechanism_low = fields.Float(string='Storage Mechanism Lowest Value')
    storage_mechanism_high = fields.Float(string='Storage Mechanism Highest Value')
    storage_mechanism_weight = fields.Float(string='Storage Mechanism Weight')


