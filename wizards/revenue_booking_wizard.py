from odoo import models, fields, api
from datetime import datetime, timedelta

class RevenueReportWizard(models.TransientModel):
    _name = 'revenue.report.wizard'
    _description = 'Revenue Report Wizard'

    time_period = fields.Selection([
        ('week', 'Week'),
        ('month', 'Month'),
        ('year', 'Year')
    ], string="Period", required=True)

    start_date = fields.Date(string="Start Date", compute="_compute_dates", store=True)
    end_date = fields.Date(string="End Date", compute="_compute_dates", store=True)
    total_revenue = fields.Float(string="Total Revenue", readonly=True, compute="_compute_total_revenue")

    @api.depends('start_date', 'end_date')
    def _compute_total_revenue(self):
        """Total revenue from booking"""
        for record in self:
                bookings = self.env['hotel.booking'].search([
                    ('payment_status', '=', 'paid'),
                    ('check_in_date', '>=', record.start_date),
                    ('check_out_date', '<=', record.end_date),
                ])
                record.total_revenue = sum(booking.payment_amount for booking in bookings)

    @api.depends('time_period')
    def _compute_dates(self):
        """Calculate start_date and end_date base on time_period"""
        today = datetime.today()
        for record in self:
            if record.time_period == 'week':
                record.start_date = today - timedelta(days=today.weekday())
                record.end_date = record.start_date + timedelta(days=6)
            elif record.time_period == 'month':
                record.start_date = today.replace(day=1)
                next_month = record.start_date + timedelta(days=31)
                record.end_date = next_month.replace(day=1) - timedelta(days=1)
            elif record.time_period == 'year':
                record.start_date = today.replace(month=1, day=1)
                record.end_date = today.replace(month=12, day=31)
            else:
                record.start_date = None
                record.end_date = None

    def action_generate_revenue_report(self):
        """Return list booking as conditions"""
        if not self.start_date or not self.end_date:
            raise ValueError("Start date and end date are required.")

        # find booking
        bookings = self.env['hotel.booking'].search([
            ('payment_status', '=', 'paid'),
            ('check_in_date', '>=', self.start_date),
            ('check_out_date', '<=', self.end_date),
        ])

        if not bookings:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Data Found',
                    'message': f"No bookings found from {self.start_date} to {self.end_date}.",
                    'sticky': False,
                },
            }

        return {
            'type': 'ir.actions.act_window',
            'name': f"Bookings from {self.start_date} to {self.end_date}",
            'res_model': 'hotel.booking',
            'view_mode': 'list',
            'domain': [
                ('payment_status', '=', 'paid'),
                ('check_in_date', '>=', self.start_date),
                ('check_out_date', '<=', self.end_date),
            ],
            'target': 'current',
        }
