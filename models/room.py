from odoo import models, fields, api
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)

class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room'
    _rec_name = 'room_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    room_code = fields.Char(string='Room Code', required=True)
    room_name = fields.Char(string='Room Name', required=True)
    hotel_id = fields.Many2one('hotel.hotel', string='Hotel', required=True)
    bed_type = fields.Selection([
        ('single', 'Single'),
        ('double', 'Double'),
        ('suite', 'Suite')
    ], string='Bed Type', required=True)
    room_price = fields.Float(string='Price per Night', required=True)
    feature_ids = fields.Many2many('hotel.feature', string='Features')
    room_status = fields.Selection([
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Under Maintenance')
    ], string='Status', default='available', tracking=True)
    booking_ids = fields.One2many('hotel.booking', 'room_id', string='Bookings')
    room_active = fields.Boolean(default=True)
    last_rented_date = fields.Date(string='Last Rented Date')

    _sql_constraints = [
        ('unique_room_code_hotel', 'UNIQUE(room_code, hotel_id)', 'Room code must be unique per hotel!')
    ]

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    @api.model
    def _check_unrented_rooms_and_apply_discount(self):
        one_week_ago = fields.Date.context_today(self) - timedelta(days=7)
        unrented_rooms = self.search([
            ('last_rented_date', '<', one_week_ago),
            ('room_status', '=', 'available')
        ])
        _logger.info("=== Unrented Rooms Report ===")
        for room in unrented_rooms:
            log_message = f"""
                                Unrented Room Details:
                                - Room Code: {room.room_code}
                                - Room Name: {room.room_name}
                                - Hotel Name: {room.hotel_id.hotel_name}
                                - Last Rented: {room.last_rented_date}
                            """
            _logger.info(log_message)

            # Apply 10% discount
            room.room_price *= 0.9
            room.message_post(body="Room price reduced by 10% due to being unrented for a week.")
            room.message_post(
                body=f"Room has not been rented for more than 7 days (Last rental: {room.last_rented_date})",
                subject="Unrented Room Alert"
            )