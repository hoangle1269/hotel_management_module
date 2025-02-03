from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta
from odoo.exceptions import UserError


class HotelBooking(models.Model):
    _name = 'hotel.booking'
    _description = 'Room Booking'
    _order = 'booking_date desc'
    _rec_name = 'booking_code'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Booking Information
    booking_code = fields.Char(string='Booking Code', readonly=True)
    booking_status = fields.Selection([
        ('draft', 'Draft'),
        ('new', 'New'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled')
    ], string='Booking Status', default='new')
    # booking_ids = fields.One2many('hotel.booking', 'partner_id', string="Booking History")

    #Customer
    partner_id = fields.Many2one(
        'res.partner', string='Customer', required=True,
        domain="[('customer_rank', '>', 0)]", tracking=True
    )
    guest_name = fields.Char(related='partner_id.name', string='Guest Name', readonly=True, store=True)
    guest_contact = fields.Char(related='partner_id.phone', string='Guest Contact', readonly=True, store=True)

    # Dates
    booking_date = fields.Date(string='Booking Date', default=fields.Date.context_today, readonly=True)
    check_in_date = fields.Date(string='Check-in Date', required=True)
    check_out_date = fields.Date(string='Check-out Date', required=True)

    # Relations
    room_id = fields.Many2one('hotel.room', string='Room', required=True)
    hotel_id = fields.Many2one('hotel.hotel', related='room_id.hotel_id', store=True)
    room_type = fields.Selection(related='room_id.room_type', string="Room Type", store=True, readonly=True)

    # Financial Fields
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    room_price = fields.Float(related='room_id.current_price', readonly=True)
    total_nights = fields.Integer(compute='_compute_total_nights', store=True)
    total_amount = fields.Float(compute='_compute_total_amount', store=True)

    # Payment Information
    payment_status = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid')
    ], default='unpaid', readonly=True)
    payment_date = fields.Datetime(readonly=True)
    payment_amount = fields.Float(readonly=True, compute='_compute_payment_amount', store=True)

    # Related Documents
    sale_order_id = fields.Many2one('sale.order', readonly=True)

    def action_create_sale_order(self):
        for record in self:
            # check payment status
            if record.payment_status != 'paid':
                raise UserError("Please complete the payment before creating a sale order.")

            if record.sale_order_id:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Sale Order',
                    'view_mode': 'form',
                    'res_model': 'sale.order',
                    'res_id': record.sale_order_id.id,
                }

            partner = self.env['res.partner'].search([('name', '=', record.guest_name)], limit=1)
            if not partner:
                partner = self.env['res.partner'].create({'name': record.guest_name})

            sale_order = self.env['sale.order'].create({
                'partner_id': partner.id,
                'origin': record.booking_code,
            })

            if record.room_id and record.check_in_date and record.check_out_date:
                sale_name = f"{record.room_id.room_code}: {record.check_in_date} - {record.check_out_date}"
            else:
                sale_name = "Room Booking"

            product = self.env['product.product'].search([('name', '=', sale_name)], limit=1)
            if not product:
                product = self.env['product.product'].create({
                    'name': sale_name,
                    'type': 'service',
                    'list_price': record.total_amount,
                })

            duration = (record.check_out_date - record.check_in_date).days
            if duration <= 0:
                raise UserError("Check-out date must be later than check-in date.")

            self.env['sale.order.line'].create({
                'order_id': sale_order.id,
                'name': product.name,
                'product_uom_qty': max(duration, 1),
                'price_unit': record.total_amount,
                'product_id': product.id,
            })

            record.write({
                'sale_order_id': sale_order.id,
            })

            return {
                'type': 'ir.actions.act_window',
                'name': 'Sale Order',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'res_id': sale_order.id,
            }

    def action_open_payment_wizard(self):
        return {
            'name': 'Make Payment',
            'type': 'ir.actions.act_window',
            'res_model': 'booking.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_booking_id': self.id,
                'default_hotel_id': self.hotel_id.id,
                'default_room_id': self.room_id.id,
                'default_amount': self.total_amount
            }
        }

    def action_confirm_payment(self):
        self.ensure_one()
        if self.payment_status == 'paid':
            raise ValidationError('This booking has already been paid.')

        self.write({
            'payment_status': 'paid',
            'payment_date': fields.Datetime.now(),
            'payment_amount': self.total_amount
        })

        # Send confirmation email or other actions if necessary
        self._send_payment_confirmation()

        return {'type': 'ir.actions.act_window_close'}

    def _send_payment_confirmation(self):
        template = self.env.ref('hotel_management_module.payment_confirmation_email_template', False)
        if template:
            try:
                template.send_mail(self.id, force_send=True)
            except Exception as e:
                raise ValidationError(f"Failed to send email: {str(e)}")

    @api.model
    def _auto_cancel_draft_bookings(self):
        draft_bookings = self.search([
            ('booking_status', '=', 'draft'),
            ('create_date', '<', fields.Datetime.now() - timedelta(hours=24))
        ])
        draft_bookings.write({'booking_status': 'cancelled'})

    def unlink(self):
        for booking in self:
            # if not admin
            if not self.env.user.has_group('base.group_system'):
                # status rule
                if booking.booking_status not in ['draft', 'cancelled']:
                    raise ValidationError('Only bookings in Draft or Cancelled status can be deleted.')

            # admin rule
            if not (self.env.user.has_group('hotel_management_module.group_hotel_manager') or
                    self.env.user.has_group('base.group_system')):
                raise ValidationError('Only managers or admin can delete bookings.')

        return super(HotelBooking, self).unlink()

    @api.model
    def create(self, vals):
        if not vals.get('booking_code'):
            vals['booking_code'] = self.env['ir.sequence'].next_by_code('hotel.booking')
        return super().create(vals)

    @api.depends('check_in_date', 'check_out_date')
    def _compute_total_nights(self):
        for booking in self:
            if booking.check_in_date and booking.check_out_date:
                delta = booking.check_out_date - booking.check_in_date
                booking.total_nights = delta.days
            else:
                booking.total_nights = 0

    @api.depends('check_in_date', 'check_out_date', 'room_id')
    def _compute_total_amount(self):
        for booking in self:
            if not (booking.check_in_date and booking.check_out_date and booking.room_id):
                booking.total_amount = 0
                continue

            total = 0
            current_date = booking.check_in_date
            while current_date < booking.check_out_date:
                is_weekend = current_date.weekday() >= 5
                if is_weekend:
                    total += booking.room_id.room_price * 1.5
                else:
                    total += booking.room_id.room_price
                current_date += timedelta(days=1)

            booking.total_amount = total

    @api.depends('total_amount', 'sale_order_id.amount_total')
    def _compute_payment_amount(self):
        for record in self:
            if record.sale_order_id:
                record.payment_amount = record.sale_order_id.amount_total
            else:
                record.payment_amount = record.total_amount if record.total_amount else 0.0


    @api.constrains('check_in_date', 'check_out_date')
    def _check_dates(self):
        for booking in self:
            if booking.check_in_date and booking.check_out_date:
                if booking.check_in_date >= booking.check_out_date:
                    raise ValidationError('Check-out date must be later than check-in date.')
                if booking.check_in_date < fields.Date.today():
                    raise ValidationError('Check-in date cannot be in the past.')

    @api.constrains('room_id', 'check_in_date', 'check_out_date')
    def _check_room_availability(self):
        for booking in self:
            if not booking.room_id.room_active:
                raise ValidationError('This room is currently unavailable.')

            domain = [
                ('room_id', '=', booking.room_id.id),
                ('id', '!=', booking.id),
                ('check_in_date', '<', booking.check_out_date),
                ('check_out_date', '>', booking.check_in_date),
                ('booking_status', 'in', ['new', 'confirmed', 'checked_in'])
            ]
            if self.search_count(domain):
                raise ValidationError('Room is already booked for these dates.')

    def action_check_in(self):
        for booking in self:
            # Check if booking is in confirmed status
            if booking.booking_status != 'confirmed':
                raise ValidationError("Only confirmed bookings can be checked in.")

            # Check if today is the check-in date
            today = fields.Date.today()
            if today != booking.check_in_date:
                if today < booking.check_in_date:
                    raise ValidationError(
                        f"Cannot check in before the scheduled check-in date ({booking.check_in_date})")
                else:
                    raise ValidationError(
                        f"Check-in date ({booking.check_in_date}) has passed. Please contact hotel management.")

            booking.write({'booking_status': 'checked_in'})
            # Update the room status to 'occupied'
            booking.room_id.sudo().write({'room_status': 'occupied'})
            booking._send_status_update_email()

    def action_check_out(self):
        for booking in self:
            if booking.booking_status != 'checked_in':
                raise ValidationError("Only checked-in bookings can be checked out.")
            booking.write({'booking_status': 'checked_out'})
            # Update the room status to 'available'
            booking.room_id.sudo().write({'room_status': 'available'})
            booking._send_status_update_email()

    def _send_status_update_email(self):
        manager = self.hotel_id.manager_id
        if manager and manager.user_id:
            template = self.env.ref('hotel.booking_status_update_email_template')
            self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)

    @api.model
    def _send_status_update_notification(self, booking):
        message = f"Booking {booking.booking_code} status updated to {booking.booking_status}."
        booking.message_post(body=message)

    def action_approve(self):
        for record in self:
            if record.booking_status == 'new':
                if record.payment_status != 'paid':
                    raise ValidationError("Payment must be completed before approving the booking.")
                record.write({'booking_status': 'confirmed'})
            else:
                raise ValidationError("Only bookings in 'New' status can be approved.")