from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PropertyFlat(models.Model):
    _name = 'property.flat'
    _description = 'Property Flat'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'property_id, flat_number'

    name = fields.Char('Flat Name', compute='_compute_name', store=True)
    flat_number = fields.Char('Flat Number', required=True)
    floor = fields.Integer('Floor', required=True)
    
    # Relations
    property_id = fields.Many2one('property.property', 'Property', required=True, ondelete='cascade')
    room_ids = fields.One2many('property.room', 'flat_id', 'Rooms')
    
    # Details
    flat_type = fields.Selection([
        ('studio', 'Studio'),
        ('1bhk', '1 BHK'),
        ('2bhk', '2 BHK'),
        ('3bhk', '3 BHK'),
        ('4bhk', '4+ BHK'),
        ('penthouse', 'Penthouse'),
    ], string='Flat Type', required=True)
    
    total_area = fields.Float('Total Area (Sq.Ft.)')
    balcony_area = fields.Float('Balcony Area (Sq.Ft.)')
    
    # Computed Fields
    rooms_count = fields.Integer('Number of Rooms', compute='_compute_rooms_count', store=True)
    occupied_rooms = fields.Integer('Occupied Rooms', compute='_compute_room_stats', store=True)
    vacant_rooms = fields.Integer('Vacant Rooms', compute='_compute_room_stats', store=True)
    total_rent = fields.Monetary('Total Rent', compute='_compute_financial', currency_field='currency_id')
    
    # Facilities
    has_parking = fields.Boolean('Has Parking')
    parking_slots = fields.Integer('Parking Slots')
    has_balcony = fields.Boolean('Has Balcony')
    has_kitchen = fields.Boolean('Has Kitchen', default=True)
    has_living_room = fields.Boolean('Has Living Room', default=True)
    
    # Status
    state = fields.Selection([
        ('available', 'Available'),
        ('partially_occupied', 'Partially Occupied'),
        ('fully_occupied', 'Fully Occupied'),
        ('maintenance', 'Under Maintenance'),
    ], string='Status', compute='_compute_state', store=True)
    
    # Financial
    currency_id = fields.Many2one(related='property_id.currency_id')
    
    # Images
    image = fields.Image('Flat Image', max_width=1920, max_height=1920)
    
    @api.depends('property_id', 'flat_number')
    def _compute_name(self):
        for record in self:
            if record.property_id and record.flat_number:
                record.name = f"{record.property_id.name} - Flat {record.flat_number}"
            else:
                record.name = record.flat_number or 'New Flat'
    
    @api.depends('room_ids')
    def _compute_rooms_count(self):
        for record in self:
            record.rooms_count = len(record.room_ids)
    
    @api.depends('room_ids.status')
    def _compute_room_stats(self):
        for record in self:
            record.occupied_rooms = len(record.room_ids.filtered(lambda r: r.status == 'occupied'))
            record.vacant_rooms = len(record.room_ids.filtered(lambda r: r.status == 'vacant'))
    
    @api.depends('room_ids.rent_amount', 'room_ids.status')
    def _compute_financial(self):
        for record in self:
            occupied_rooms = record.room_ids.filtered(lambda r: r.status == 'occupied')
            record.total_rent = sum(occupied_rooms.mapped('rent_amount'))
    
    @api.depends('room_ids.status')
    def _compute_state(self):
        for record in self:
            if not record.room_ids:
                record.state = 'available'
            elif all(room.status == 'vacant' for room in record.room_ids):
                record.state = 'available'
            elif all(room.status == 'occupied' for room in record.room_ids):
                record.state = 'fully_occupied'
            else:
                record.state = 'partially_occupied'
    
    @api.constrains('property_id', 'flat_number')
    def _check_flat_number_unique(self):
        for record in self:
            if record.property_id and record.flat_number:
                existing = self.search([
                    ('property_id', '=', record.property_id.id),
                    ('flat_number', '=', record.flat_number),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(_('Flat number must be unique within a property!'))
    
    def action_view_rooms(self):
        return {
            'name': _('Rooms'),
            'view_mode': 'list,form',
            'res_model': 'property.room',
            'type': 'ir.actions.act_window',
            'domain': [('flat_id', '=', self.id)],
            'context': {'default_flat_id': self.id, 'default_property_id': self.property_id.id}
        }
    
    def action_add_room(self):
        return {
            'name': _('Add Room'),
            'view_mode': 'form',
            'res_model': 'property.room',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_flat_id': self.id, 'default_property_id': self.property_id.id}
        }
