from odoo import http, fields
from odoo.http import request
import random, string

class CustomerPortal(http.Controller):

    @http.route(['/rooms/available'], type='http', auth='public', website=True)
    def available_rooms(self, **kwargs):
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')

        available_rooms = []
        if start_date and end_date:
            start_date = fields.Date.from_string(start_date)
            end_date = fields.Date.from_string(end_date)

            available_rooms = request.env['hotel.room'].sudo().get_available_rooms(start_date, end_date)

        return request.render('hotel_management_module.available_rooms_template', {
            'rooms': available_rooms,
            'start_date': kwargs.get('start_date'),
            'end_date': kwargs.get('end_date')
        })
    @http.route(['/book/room/<int:room_id>'], type='http', auth='public', website=True)
    def book_room(self, room_id, **kwargs):
        room = request.env['hotel.room'].sudo().browse(room_id)
        if not room.exists():
            return request.not_found()

        values = {
            'room': room,
            'booking_code': ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)),
            'booking_date': fields.Date.today(),
        }

        return request.render('hotel_management_module.book_room_template', values)

    @http.route(['/confirm/booking'], type='http', auth='public', website=True, methods=['POST'])
    def confirm_booking(self, **kwargs):
        booking_data = {
            'booking_code': kwargs.get('booking_code'),
            'guest_name': kwargs.get('guest_name'),
            'booking_date': fields.Date.today(),
            'check_in_date': kwargs.get('check_in_date'),
            'check_out_date': kwargs.get('check_out_date'),
            'hotel_id': int(kwargs.get('hotel_id')),
            'room_id': int(kwargs.get('room_id')),
            'room_type': kwargs.get('room_type'),
        }

        try:
            request.env['hotel.booking'].sudo().create(booking_data)
        except Exception as e:
            return request.render('hotel_management_module.booking_error_template', {'error': str(e)})

        return request.render('hotel_management_module.booking_success_template', {'booking_code': booking_data['booking_code']})