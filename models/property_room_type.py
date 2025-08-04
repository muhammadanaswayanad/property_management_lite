from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PropertyRoomType(models.Model):
    _name = 'property.room.type'
    _description = 'Room Type'
    _order = 'sequence, name'

    name = fields.Char('Room Type', required=True)
    code = fields.Char('Code', required=True)
    sequence = fields.Integer('Sequence', default=10)
    description = fields.Text('Description')
    
    # Default Settings
    default_rent = fields.Monetary('Default Rent', currency_field='currency_id')
    default_deposit = fields.Monetary('Default Deposit', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', 'Currency', 
                                  default=lambda self: self.env.company.currency_id)
    
    # Characteristics
    max_occupancy = fields.Integer('Maximum Occupancy', default=1)
    has_private_bathroom = fields.Boolean('Private Bathroom', default=True)
    has_kitchen_access = fields.Boolean('Kitchen Access', default=True)
    
    active = fields.Boolean('Active', default=True)
    
    @api.constrains('code')
    def _check_code_unique(self):
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_('Room type code must be unique!'))
