from odoo import models, fields, api, _


class PropertyLandlordPayment(models.Model):
    _name = 'property.landlord.payment'
    _description = 'Landlord Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Payment Reference', required=True)
    
    landlord_id = fields.Many2one('res.partner', 'Landlord', required=True, 
                                  domain=[('is_landlord', '=', True)])
    property_id = fields.Many2one('property.property', 'Property', required=True)
    
    payment_date = fields.Date('Payment Date', required=True, default=fields.Date.today)
    amount = fields.Monetary('Amount', required=True, currency_field='currency_id')
    
    period_from = fields.Date('Period From')
    period_to = fields.Date('Period To')
    
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
    ], required=True, default='bank_transfer')
    
    status = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True)
    
    notes = fields.Text('Notes')
    
    currency_id = fields.Many2one('res.currency', 'Currency', 
                                  default=lambda self: self.env.company.currency_id)
