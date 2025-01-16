from odoo import models, fields, api

class BookingPaymentWizard(models.TransientModel):
    _name = 'booking.payment.wizard'
    _description = 'Booking Payment Wizard'

    booking_id = fields.Many2one('hotel.booking', string="Booking Order", readonly=True)
    hotel_id = fields.Many2one('hotel.hotel', string="Hotel Information", readonly=True)
    room_id = fields.Many2one('hotel.room', string="Room Name", readonly=True)
    payment_amount = fields.Float(string="Payment Amount",related='booking_id.payment_amount',readonly=True)

    @api.constrains('payment_amount')
    def _check_payment_amount(self):
        if self.payment_amount <= 0:
            raise models.ValidationError("Payment must be bigger than 0.")

    def confirm_payment(self):
        self.booking_id.write({
            'payment_status': 'paid',
            'payment_date': fields.Datetime.now(),
            'payment_amount': self.payment_amount
        })
