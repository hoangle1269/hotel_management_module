from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

class HotelPaymentWizard(models.TransientModel):
    _name = 'hotel.payment.wizard'
    _description = 'Hotel Payment Wizard'

    booking_id = fields.Many2one('hotel.booking', string='Booking', required=True)
    hotel_id = fields.Many2one('hotel.hotel', string='Hotel', readonly=True)
    room_id = fields.Many2one('hotel.room', string='Room', readonly=True)
    payment_amount = fields.Float(string='Payment Amount', required=True)

    @api.constrains('payment_amount')
    def _check_amount(self):
        for wizard in self:
            if wizard.payment_amount <= 0:
                raise ValidationError('Payment amount must be greater than 0.')

    def action_confirm_payment(self):
        self.ensure_one()
        if self.booking_id.payment_status == 'paid':
            raise ValidationError('This booking has already been paid.')

        self.booking_id.write({
            'payment_status': 'paid',
            'payment_date': fields.Datetime.now(),
            'payment_amount': self.payment_amount
        })

        # Optional: Send confirmation email or create activity
        self._send_payment_confirmation()
        return {'type': 'ir.actions.act_window_close'}

    def _send_payment_confirmation(self):
        # Template for payment confirmation email
        template = self.env.ref('hotel_management_module.payment_confirmation_email_template', False)
        if template:
            template.send_mail(self.booking_id.id, force_send=True)