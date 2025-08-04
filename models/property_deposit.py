from odoo import models, fields, api, _


class PropertyDeposit(models.Model):
    _name = 'property.deposit'
    _description = 'Deposit Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Deposit Reference', compute='_compute_name', store=True)
    
    tenant_id = fields.Many2one('property.tenant', 'Tenant', required=True)
    agreement_id = fields.Many2one('property.agreement', 'Agreement', required=True)
    
    deposit_amount = fields.Monetary('Deposit Amount', required=True, currency_field='currency_id')
    deposit_date = fields.Date('Deposit Date', required=True, default=fields.Date.today)
    
    status = fields.Selection([
        ('held', 'Held'),
        ('partially_refunded', 'Partially Refunded'),
        ('refunded', 'Refunded'),
        ('forfeited', 'Forfeited'),
    ], string='Status', default='held', tracking=True)
    
    refund_amount = fields.Monetary('Refund Amount', currency_field='currency_id')
    refund_date = fields.Date('Refund Date')
    refund_reason = fields.Text('Refund/Deduction Reason')
    
    currency_id = fields.Many2one('res.currency', 'Currency', 
                                  default=lambda self: self.env.company.currency_id)
    
    @api.depends('tenant_id', 'deposit_date')
    def _compute_name(self):
        for record in self:
            if record.tenant_id and record.deposit_date:
                record.name = f"DEP/{record.tenant_id.name}/{record.deposit_date.strftime('%Y%m%d')}"
            else:
                record.name = 'New Deposit'
