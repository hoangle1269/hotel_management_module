from odoo import fields, models, api

class BookingServiceLine(models.Model):
    _name = 'custom.booking.service.line'
    _description = 'Booking Service Line'

    booking_id = fields.Many2one('hotel.booking', string="Booking", ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Service", required=True)
    quantity = fields.Integer(string="Quantity", default=1, store=True)
    price_unit = fields.Float(string="Unit Price", related="product_id.list_price", readonly=True)
    subtotal = fields.Float(string="Subtotal", compute="_compute_subtotal", store=True)
    service_order_id = fields.Many2one(
        'customer.service.order',
        string="Service Order", ondelete='cascade'
    )

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit


    def create_sale_order_lines(self):
        for line in self:
            if line.booking_id.sale_order_id:
                self.env['sale.order.line'].create({
                    'order_id': line.booking_id.sale_order_id.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'price_unit': line.price_unit,
                })