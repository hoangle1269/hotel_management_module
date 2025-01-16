# hotel_management/tests/test_security.py
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase

class TestHotelSecurity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestHotelSecurity, cls).setUpClass()
        # Create employee group and demo user
        cls.employee_group = cls.env.ref('hotel_management_module.group_hotel_employee')
        cls.employee_user = cls.env['res.users'].create({
            'name': 'Test Employee',
            'login': 'test_employee',
            'groups_id': [(6, 0, [cls.employee_group.id])],
        })
        cls.hotel_model = cls.env['hotel.hotel']

    def test_employee_read_access(self):
        """Test that employees have read access to hotels."""
        hotels = self.hotel_model.with_user(self.employee_user).search([])
        self.assertTrue(
            hotels,
            msg="Employee should have read access to hotels"
        )

    def test_employee_no_create_access(self):
        """Test that employees do not have create access to hotels."""
        with self.assertRaises(AccessError, msg="Employee should not have create access to hotels"):
            self.hotel_model.with_user(self.employee_user).create({'name': 'New Hotel'})
