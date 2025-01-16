{
    'name': 'Hotel Management',
    'version': '1.0',
    'category': 'Services/Hotel',
    'summary': 'Manage hotels, rooms, and bookings',
    'description': """
        Hotel Management Module for Odoo 18
        - Hotel Information Management
        - Room Management
        - Booking System
        - Feature Management
    """,
    'depends': ['base', 'mail', 'hr', 'sale'],
    'data': [
        'security/hotel_security.xml',
        'security/ir.model.access.csv',
        'security/record_rule_hotel.xml',
        'security/record_rule_room.xml',
        'security/record_rule_booking.xml',
        'data/hotel_sequence.xml',
        'data/ir.cron.xml',
        'views/hotel_views.xml',
        'views/room_views.xml',
        'views/feature_views.xml',
        'views/booking_views.xml',
        'views/booking_new.xml',
        'views/hotel_payment_views.xml',
        'views/payment_views.xml',
        'views/menus.xml',
        'views/email_template.xml',
        'reports/hotel_reports.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
