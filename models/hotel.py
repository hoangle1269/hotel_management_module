from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Hotel(models.Model):
    _name = 'hotel.hotel'
    _description = 'Hotel Information'
    _rec_name = 'hotel_name'
    _inherit = ['mail.thread']

    hotel_code = fields.Char(string='Hotel Code', required=True)
    hotel_name = fields.Char(string='Hotel Name', required=True)
    hotel_address = fields.Text(string='Hotel Address')
    number_of_floors = fields.Integer(string='Number of Floors', required=True)
    number_of_rooms = fields.Integer(string='Total Rooms', compute='_compute_total_rooms', store=True)
    room_ids = fields.One2many('hotel.room', 'hotel_id', string='Rooms')
    hotel_active = fields.Boolean(default=True)
    manager_id = fields.Many2one('hr.employee', string="Manager", domain="[('job_id', '=', 'Manager')]")
    employee_ids = fields.One2many('hr.employee', 'parent_id', string="Employees")
    user_id = fields.Many2one('res.users', string="User", related="manager_id.user_id", store=True)

    @api.constrains('manager_id')
    def _check_manager(self):
        for hotel in self:
            if self.search_count([
                ('manager_id', '=', hotel.manager_id.id),
                ('id', '!=', hotel.id)
            ]):
                raise ValidationError('An employee can only manage one hotel.')

    _sql_constraints = [
        ('unique_hotel_code', 'UNIQUE(hotel_code)', 'Hotel code must be unique!')
    ]

    @api.depends('room_ids')
    def _compute_total_rooms(self):
        for hotel in self:
            hotel.number_of_rooms = len(hotel.room_ids)

