from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PropertyProperty(models.Model):
    _name = 'property.property'
    _description = 'Property'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char('Property Name', required=True, tracking=True)
    code = fields.Char('Property Code', required=True, tracking=True)
    address = fields.Text('Address', required=True)
    city = fields.Char('City', default='Dubai')
    country_id = fields.Many2one('res.country', 'Country', default=lambda self: self.env.ref('base.ae'))
    
    # Property Details
    property_type = fields.Selection([
        ('apartment', 'Apartment Building'),
        ('villa', 'Villa'),
        ('office', 'Office Building'),
        ('warehouse', 'Warehouse'),
        ('commercial', 'Commercial Building'),
    ], string='Property Type', required=True, default='apartment')
    
    total_flats = fields.Integer('Total Flats', compute='_compute_total_flats', store=True)
    total_rooms = fields.Integer('Total Rooms', compute='_compute_total_rooms', store=True)
    occupied_rooms = fields.Integer('Occupied Rooms', compute='_compute_room_stats', store=True)
    vacant_rooms = fields.Integer('Vacant Rooms', compute='_compute_room_stats', store=True)
    
    # Owner/Landlord Information
    landlord_id = fields.Many2one('res.partner', 'Landlord', 
                                  domain=[('is_company', '=', False), ('supplier_rank', '>', 0)])
    manager_id = fields.Many2one('res.users', 'Property Manager', default=lambda self: self.env.user)
    
    # Financial
    property_value = fields.Monetary('Property Value', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', 'Currency', 
                                  default=lambda self: self.env.company.currency_id)
    
    # Relations
    flat_ids = fields.One2many('property.flat', 'property_id', 'Flats')
    collection_ids = fields.One2many('property.collection', 'property_id', 'Collections')
    expense_ids = fields.One2many('property.expense', 'property_id', 'Expenses')
    
    # Status
    active = fields.Boolean('Active', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance'),
        ('inactive', 'Inactive'),
    ], string='Status', default='draft', tracking=True)
    
    # Computed Financial Fields
    monthly_rent_income = fields.Monetary('Monthly Rent Income', compute='_compute_financial_summary', currency_field='currency_id')
    monthly_expenses = fields.Monetary('Monthly Expenses', compute='_compute_financial_summary', currency_field='currency_id')
    monthly_profit = fields.Monetary('Monthly Profit', compute='_compute_financial_summary', currency_field='currency_id')
    occupancy_rate = fields.Float('Occupancy Rate (%)', compute='_compute_room_stats')
    
    # Images and Attachments
    image = fields.Image('Property Image', max_width=1920, max_height=1920)
    image_medium = fields.Image('Medium-sized Image', related='image', max_width=128, max_height=128, store=True)
    image_small = fields.Image('Small-sized Image', related='image', max_width=64, max_height=64, store=True)
    
    @api.depends('flat_ids')
    def _compute_total_flats(self):
        for record in self:
            record.total_flats = len(record.flat_ids)
    
    @api.depends('flat_ids.room_ids')
    def _compute_total_rooms(self):
        for record in self:
            record.total_rooms = sum(len(flat.room_ids) for flat in record.flat_ids)
    
    @api.depends('flat_ids.room_ids.status')
    def _compute_room_stats(self):
        for record in self:
            rooms = record.flat_ids.mapped('room_ids')
            record.occupied_rooms = len(rooms.filtered(lambda r: r.status == 'occupied'))
            record.vacant_rooms = len(rooms.filtered(lambda r: r.status == 'vacant'))
            # Calculate as decimal (0.0 to 1.0) since view uses percentage widget
            record.occupancy_rate = (record.occupied_rooms / record.total_rooms) if record.total_rooms > 0 else 0
    
    @api.depends('flat_ids.room_ids.rent_amount', 'expense_ids.amount')
    def _compute_financial_summary(self):
        for record in self:
            # Monthly rent income from occupied rooms
            occupied_rooms = record.flat_ids.mapped('room_ids').filtered(lambda r: r.status == 'occupied')
            record.monthly_rent_income = sum(occupied_rooms.mapped('rent_amount'))
            
            # Monthly expenses (average from last 12 months)
            expenses = record.expense_ids.filtered(
                lambda e: e.date >= fields.Date.today().replace(day=1) - fields.timedelta(days=365)
            )
            record.monthly_expenses = sum(expenses.mapped('amount')) / 12 if expenses else 0
            
            # Monthly profit
            record.monthly_profit = record.monthly_rent_income - record.monthly_expenses
    
    @api.constrains('code')
    def _check_code_unique(self):
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_('Property code must be unique!'))
    
    def action_activate(self):
        self.write({'state': 'active'})
        
    def action_maintenance(self):
        self.write({'state': 'maintenance'})
        
    def action_deactivate(self):
        self.write({'state': 'inactive'})
    
    def action_view_flats(self):
        return {
            'name': _('Flats'),
            'view_mode': 'list,form',
            'res_model': 'property.flat',
            'type': 'ir.actions.act_window',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id}
        }
    
    def action_view_rooms(self):
        return {
            'name': _('Rooms'),
            'view_mode': 'list,form',
            'res_model': 'property.room',
            'type': 'ir.actions.act_window',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id}
        }
    
    def action_view_collections(self):
        return {
            'name': _('Collections'),
            'view_mode': 'list,form',
            'res_model': 'property.collection',
            'type': 'ir.actions.act_window',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id}
        }
    
    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result
