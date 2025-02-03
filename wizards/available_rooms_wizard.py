from odoo import models, fields
class AvailableRoomsWizard(models.TransientModel):
    _name = 'available.rooms.wizard'
    _description = 'Available Rooms Wizard'

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date")

    def action_get_available_rooms(self):
        available_rooms = self.env['hotel.room'].get_available_rooms(self.start_date, self.end_date)
        action = self.env.ref('hotel_management_module.action_room').read()[0]
        action['domain'] = [('id', 'in', available_rooms.ids)]
        return action

