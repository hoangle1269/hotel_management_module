from odoo.tests.common import TransactionCase

class TestHotel(TransactionCase):

    def test_create_room(self):
        # Tạo một phòng khách sạn
        room = self.env['hotel.room'].create({
            'room_name': 'Luxury Suite',
            'room_price': 12,
        })
        # Kiểm tra các giá trị
        self.assertEqual(room.name, 'Luxury Suite')
        self.assertEqual(room.price, 12)
