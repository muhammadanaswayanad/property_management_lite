from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PropertyRoom(models.Model):
    _name = 'property.room'
    _description = 'Property Room'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'property_id, flat_id, room_number'

    name = fields.Char('Room Name', compute='_compute_name', store=True)
    room_number = fields.Char('Room Number', required=True)
    
    # Relations
    property_id = fields.Many2one('property.property', 'Property', required=True, ondelete='cascade')
    flat_id = fields.Many2one('property.flat', 'Flat', required=True, ondelete='cascade')
    room_type_id = fields.Many2one('property.room.type', 'Room Type', required=True)
    
    # Current Tenant & Agreement
    current_tenant_id = fields.Many2one('property.tenant', 'Current Tenant')
    current_agreement_id = fields.Many2one('property.agreement', 'Current Agreement')
    
    # Room Details
    area = fields.Float('Area (Sq.Ft.)')
    rent_amount = fields.Monetary('Monthly Rent', required=True, currency_field='currency_id', tracking=True)
    deposit_amount = fields.Monetary('Security Deposit', currency_field='currency_id')
    
    # Status
    status = fields.Selection([
        ('vacant', 'Vacant'),
        ('occupied', 'Occupied'),
        ('booked', 'Booked'),
        ('maintenance', 'Under Maintenance'),
        ('not_available', 'Not Available'),
    ], string='Status', default='vacant', required=True, tracking=True)
    
    # Facilities
    has_ac = fields.Boolean('Air Conditioning')
    has_heater = fields.Boolean('Heater')
    has_wardrobe = fields.Boolean('Wardrobe')
    has_desk = fields.Boolean('Desk')
    has_wifi = fields.Boolean('WiFi', default=True)
    has_private_bathroom = fields.Boolean('Private Bathroom')
    has_balcony_access = fields.Boolean('Balcony Access')
    
    # Parking
    parking_number = fields.Char('Parking Number')
    has_parking = fields.Boolean('Has Parking')
    
    # Utilities
    has_gas = fields.Boolean('Gas Included')
    electricity_included = fields.Boolean('Electricity Included')
    water_included = fields.Boolean('Water Included', default=True)
    internet_included = fields.Boolean('Internet Included', default=True)
    
    # Additional Information
    inclusions = fields.Text('Other Inclusions')
    notes = fields.Text('Notes')
    
    # Computed Fields
    currency_id = fields.Many2one(related='property_id.currency_id')
    is_available = fields.Boolean('Available for Rent', compute='_compute_availability')
    days_vacant = fields.Integer('Days Vacant', compute='_compute_days_vacant')
    
    # Financial Tracking
    total_collected = fields.Monetary('Total Collected', compute='_compute_financial_stats', currency_field='currency_id')
    last_collection_date = fields.Date('Last Collection', compute='_compute_financial_stats')
    pending_amount = fields.Monetary('Pending Amount', compute='_compute_financial_stats', currency_field='currency_id')
    
    # Images
    image = fields.Image('Room Image', max_width=1920, max_height=1920)
    image_ids = fields.One2many('ir.attachment', 'res_id', 'Additional Images', 
                                domain=[('res_model', '=', 'property.room'), ('mimetype', 'like', 'image/')])
    
    @api.depends('property_id', 'flat_id', 'room_number')
    def _compute_name(self):
        for record in self:
            if record.property_id and record.flat_id and record.room_number:
                record.name = f"{record.property_id.code}-{record.flat_id.flat_number}-{record.room_number}"
            else:
                record.name = record.room_number or 'New Room'
    
    @api.depends('status')
    def _compute_availability(self):
        for record in self:
            record.is_available = record.status in ['vacant', 'booked']
    
    @api.depends('status', 'current_agreement_id.end_date')
    def _compute_days_vacant(self):
        for record in self:
            if record.status == 'vacant':
                if record.current_agreement_id and record.current_agreement_id.end_date:
                    delta = fields.Date.today() - record.current_agreement_id.end_date
                    record.days_vacant = delta.days
                else:
                    record.days_vacant = 0
            else:
                record.days_vacant = 0
    
    def _compute_financial_stats(self):
        for record in self:
            collections = self.env['property.collection'].search([('room_id', '=', record.id)])
            record.total_collected = sum(collections.mapped('amount_collected'))
            record.last_collection_date = max(collections.mapped('date')) if collections else False
            
            # Calculate pending amount based on current agreement
            if record.current_agreement_id and record.status == 'occupied':
                # This would need more complex logic based on payment schedule
                record.pending_amount = 0  # Simplified for now
            else:
                record.pending_amount = 0
    
    @api.constrains('property_id', 'flat_id', 'room_number')
    def _check_room_number_unique(self):
        for record in self:
            if record.flat_id and record.room_number:
                existing = self.search([
                    ('flat_id', '=', record.flat_id.id),
                    ('room_number', '=', record.room_number),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(_('Room number must be unique within a flat!'))
    
    @api.onchange('flat_id')
    def _onchange_flat_id(self):
        if self.flat_id:
            self.property_id = self.flat_id.property_id
    
    @api.onchange('room_type_id')
    def _onchange_room_type_id(self):
        if self.room_type_id:
            self.rent_amount = self.room_type_id.default_rent
            self.deposit_amount = self.room_type_id.default_deposit
            self.has_private_bathroom = self.room_type_id.has_private_bathroom
    
    def action_book_room(self):
        self.write({'status': 'booked'})
        
    def action_occupy_room(self):
        self.write({'status': 'occupied'})
        
    def action_vacate_room(self):
        self.write({
            'status': 'vacant',
            'current_tenant_id': False,
            'current_agreement_id': False,
        })
        
    def action_maintenance(self):
        self.write({'status': 'maintenance'})
    
    def action_view_collections(self):
        return {
            'name': _('Room Collections'),
            'view_mode': 'list,form',
            'res_model': 'property.collection',
            'type': 'ir.actions.act_window',
            'domain': [('room_id', '=', self.id)],
            'context': {'default_room_id': self.id, 'default_property_id': self.property_id.id}
        }
    
    def action_create_agreement(self):
        return {
            'name': _('Create Agreement'),
            'view_mode': 'form',
            'res_model': 'property.agreement',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_room_id': self.id,
                'default_property_id': self.property_id.id,
                'default_rent_amount': self.rent_amount,
                'default_deposit_amount': self.deposit_amount,
            }
        }
