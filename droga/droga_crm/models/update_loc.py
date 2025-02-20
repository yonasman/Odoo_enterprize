from datetime import datetime, timedelta
from math import radians, sin, atan2, sqrt, cos

from odoo import models,fields

class update_crm_visit_per_customer(models.Model):
    _name='crm.update.location'

    def update_loc(self):
        leads=self.env['crm.lead'].search(['|',('check_out_distance_meters', '>', 3000000),('check_in_distance_meters', '>', 3000000)])

        for lead in leads:
            if lead.check_in_descr:
                dist=self.calculate_distance(lead.check_in_lati,lead.check_in_long,lead.partner_id.partner_latitude,lead.partner_id.partner_longitude)
                lead.check_in_distance_meters=int(dist)
                lead.check_in_descr=(lead.check_in_time_and_date+timedelta(hours=3)).strftime("%d %b, %H:%M")+' ('+f"{int(dist):,}"+' m)'

            if lead.check_out_descr:
                dist=self.calculate_distance(lead.check_out_lati,lead.check_out_long,lead.partner_id.partner_latitude,lead.partner_id.partner_longitude)
                lead.check_out_distance_meters=int(dist)
                lead.check_out_descr = (lead.check_out_time_and_date+timedelta(hours=3)).strftime("%d %b, %H:%M")+' ('+f"{int(dist):,}"+' m)'

        leads = self.env['crm.lead'].search(
            [ ('check_out_distance_meters', '!=', False)])


    def calculate_distance(self, lat1, lon1, lat2, lon2):
        lat1 = radians(lat1)
        lon1 = radians(lon1)
        lat2 = radians(lat2)
        lon2 = radians(lon2)

        R = 6371000

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c

        return distance
