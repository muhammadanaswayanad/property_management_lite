from odoo import models, fields, api, _


class PropertyBankTransfer(models.Model):
    _name = 'property.bank.transfer'
    _description = 'Bank Transfer Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Reference', required=True)
    date = fields.Date('Transfer Date', required=True, default=fields.Date.today)
    amount = fields.Monetary('Amount', required=True, currency_field='currency_id')
    
    tenant_id = fields.Many2one('property.tenant', 'Tenant')
    collection_id = fields.Many2one('property.collection', 'Related Collection')
    
    bank_name = fields.Char('Bank Name')
    account_number = fields.Char('Account Number')
    transaction_id = fields.Char('Transaction ID')
    
    status = fields.Selection([
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('reconciled', 'Reconciled'),
    ], default='pending')
    
    currency_id = fields.Many2one('res.currency', 'Currency', 
                                  default=lambda self: self.env.company.currency_id)
