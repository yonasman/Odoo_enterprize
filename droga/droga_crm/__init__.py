# -*- coding: utf-8 -*-

from . import controllers
from . import models,reports,wizards


from odoo import api, SUPERUSER_ID
def create_days(cr, registry):
  env = api.Environment(cr, SUPERUSER_ID, {})
  env['droga.crm.settings.day'].sudo().create({
      'day': 'Monday',
  })
  env['droga.crm.settings.day'].sudo().create({
      'day': 'Tuesday',
  })
  env['droga.crm.settings.day'].sudo().create({
      'day': 'Wednesday',
  })
  env['droga.crm.settings.day'].sudo().create({
      'day': 'Thursday',
  })
  env['droga.crm.settings.day'].sudo().create({
      'day': 'Friday',
  })
  env['droga.crm.settings.day'].sudo().create({
      'day': 'Saturday',
  })