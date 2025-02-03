from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import ValidationError
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
    room_type = fields.Selection([
        ('single', 'Single'),
        ('double', 'Double'),
        ('suite', 'Suite')
    ], string='Room Type', required=True)
    room_price = fields.Float(string='Base Price', required=True,
                              help="Standard room price for weekdays")
    current_price = fields.Float(string='Current Price', compute='_compute_current_price', store=True,
                                 help="Current room price based on whether it's a weekday or weekend")
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

    def get_available_rooms(self, start_date, end_date=None):
        end_date = end_date or start_date
        # find available roomin a period
        booked_rooms = self.env['hotel.booking'].search([
            ('check_in_date', '<=', end_date),
            ('check_out_date', '>=', start_date)
        ]).mapped('room_id')

        # Lọc ra các phòng trống
        available_rooms = self.search([('id', 'not in', booked_rooms.ids)])
        return available_rooms

    @api.depends('room_price')
    def _compute_current_price(self):
        today = fields.Date.today()
        is_weekend = today.weekday() >= 5  # 5 là thứ 7, 6 là chủ nhật
        for room in self:
            # Kiểm tra xem phòng có được thuê trong 7 ngày qua không
            if room.last_rented_date and (today - room.last_rented_date).days >= 7:
                base_price = room.room_price * 0.9  # Giảm 10% nếu không được thuê trong 7 ngày
            else:
                base_price = room.room_price

            # Tính giá cuối tuần (tăng 50%)
            if is_weekend:
                room.current_price = base_price * 1.5
            else:
                room.current_price = base_price

    @api.constrains('room_price')
    def _check_price(self):
        for room in self:
            if room.room_price <= 0:
                raise ValidationError('Room price must be greater than zero.')

    @api.depends('room_status')
    def _compute_room_status(self):
        for room in self:
            if room.room_status == 'occupied':
                room.room_status = 'occupied'
            elif room.room_status == 'maintenance':
                room.room_status = 'maintenance'
            else:
                room.room_status = 'available'

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
            room.message_post(body="Room base rate reduced by 10% due to being unrented for a week.")
            room.message_post(
                body=f"Room has not been rented for more than 7 days (Last rental: {room.last_rented_date})",
                subject="Unrented Room Alert"
            )