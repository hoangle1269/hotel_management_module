from odoo import models, fields, api

class HotelFeature(models.Model):
    _name = 'hotel.feature'
    _description = 'Room Features'
    _rec_name = 'feature_name'

    feature_name = fields.Char(string='Feature Name', required=True)
    description = fields.Text(string='Description')
    feature_active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_feature_name', 'UNIQUE(feature_name)', 'Feature name must be unique!')
    ]