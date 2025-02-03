{
    'name': 'Hotel Management',
    'version': '18.0.1.0.0',
    'category': 'Services/Hotel',
    'summary': 'Hotel Management System',
    'description': """
        Hotel Management module for managing rooms, bookings, and services.
        Includes integration with Sales, Inventory and POS.
    """,
    'depends': ['base', 'sale_management', 'stock', 'point_of_sale', 'sale', 'website', 'website_payment', 'contacts',
                'mail', 'account'],
    'data': [
        'data/hotel_sequence.xml',
        'data/ir.cron.xml',

        'controllers/available_rooms_template.xml',
        'controllers/booking_room_template.xml',
        'controllers/booking_success_template.xml',
        'controllers/booking_error_template.xml',

        'security/hotel_security.xml',
        'security/ir.model.access.csv',
        'security/record_rule_hotel.xml',
        'security/record_rule_room.xml',
        'security/record_rule_booking.xml',

        'views/hotel_views.xml',
        'views/room_views.xml',
        'views/feature_views.xml',
        'views/booking_views.xml',
        'views/pending_views.xml',
        'views/email_template.xml',

        'wizards/payment_views.xml',
        'wizards/available_rooms_views.xml',
        'wizards/revenue_booking_views.xml',

        'reports/hotel_reports.xml',
        'reports/action_report_available_room.xml',
        'reports/action_report_revenue_booking.xml',
        # 'reports/report_booking_template.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
