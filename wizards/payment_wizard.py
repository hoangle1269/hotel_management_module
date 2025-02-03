from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HotelPaymentWizard(models.TransientModel):
    _name = 'booking.payment.wizard'
    _description = 'Booking Payment Wizard'

    booking_id = fields.Many2one('hotel.booking', string='Booking', required=True)
    hotel_id = fields.Many2one('hotel.hotel', string='Hotel', readonly=True)
    room_id = fields.Many2one('hotel.room', string='Room', readonly=True)
    payment_amount = fields.Float(string='Payment Amount', required=True, compute='_compute_payment_amount',
                                  readonly=True, store=True)
    currency_id = fields.Many2one(related='booking_id.currency_id', readonly=True)

    @api.model
    def default_get(self, fields):
        """ Tự động lấy thông tin từ booking_id khi mở wizard """
        res = super(HotelPaymentWizard, self).default_get(fields)
        booking_id = self.env.context.get('active_id')  # Lấy ID đơn đặt phòng từ context
        if booking_id:
            booking = self.env['hotel.booking'].browse(booking_id)
            res.update({
                'booking_id': booking.id,
                'hotel_id': booking.hotel_id.id,
                'room_id': booking.room_id.id,
                'payment_amount': booking.payment_amount,  # Giá trị thanh toán mặc định
            })
        return res

    @api.depends('booking_id')
    def _compute_payment_amount(self):
        for wizard in self:
            wizard.payment_amount = wizard.booking_id.total_amount

    @api.constrains('payment_amount')
    def _check_amount(self):
        for wizard in self:
            if wizard.payment_amount <= 0:
                raise ValidationError('Payment amount must be greater than 0.')
            if wizard.payment_amount > wizard.booking_id.total_amount:
                raise ValidationError('Payment amount cannot exceed the total booking amount.')

    def action_confirm_payment(self):
        self.ensure_one()
        if self.booking_id.payment_status == 'paid':
            raise ValidationError('This booking has already been paid.')

        # Create and confirm sale order first
        # self.booking_id.action_create_sale_order()

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