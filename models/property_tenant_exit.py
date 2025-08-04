from odoo import models, fields, api, _


class PropertyTenantExit(models.Model):
    _name = 'property.tenant.exit'
    _description = 'Tenant Exit Process'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Exit Reference', compute='_compute_name', store=True)
    
    tenant_id = fields.Many2one('property.tenant', 'Tenant', required=True)
    agreement_id = fields.Many2one('property.agreement', 'Agreement', required=True)
    room_id = fields.Many2one(related='agreement_id.room_id', string='Room', store=True)
    
    exit_date = fields.Date('Exit Date', required=True, default=fields.Date.today)
    notice_date = fields.Date('Notice Given Date')
    
    exit_reason = fields.Selection([
        ('end_of_term', 'End of Agreement Term'),
        ('early_termination', 'Early Termination'),
        ('eviction', 'Eviction'),
        ('transfer', 'Transfer to Another Room'),
        ('other', 'Other'),
    ], string='Exit Reason', required=True)
    
    exit_type = fields.Selection([
        ('normal', 'Normal Exit'),
        ('emergency', 'Emergency Exit'),
        ('absconding', 'Absconding'),
    ], string='Exit Type', default='normal')
    
    # Financial Settlement
    deposit_refund = fields.Monetary('Deposit Refund', currency_field='currency_id')
    pending_dues = fields.Monetary('Pending Dues', currency_field='currency_id')
    damages_deduction = fields.Monetary('Damages Deduction', currency_field='currency_id')
    final_settlement = fields.Monetary('Final Settlement', compute='_compute_settlement', store=True, currency_field='currency_id')
    
    # Status
    status = fields.Selection([
        ('notice_given', 'Notice Given'),
        ('in_progress', 'Exit in Progress'),
        ('completed', 'Exit Completed'),
        ('archived', 'Archived'),
    ], string='Status', default='notice_given', tracking=True)
    
    # Additional Information
    notes = fields.Text('Exit Notes')
    damages_description = fields.Text('Damages Description')
    
    currency_id = fields.Many2one('res.currency', 'Currency', 
                                  default=lambda self: self.env.company.currency_id)
    
    @api.depends('tenant_id', 'exit_date')
    def _compute_name(self):
        for record in self:
            if record.tenant_id and record.exit_date:
                record.name = f"EXIT/{record.tenant_id.name}/{record.exit_date.strftime('%Y%m%d')}"
            else:
                record.name = 'New Exit'
    
    @api.depends('deposit_refund', 'pending_dues', 'damages_deduction')
    def _compute_settlement(self):
        for record in self:
            record.final_settlement = record.deposit_refund - record.pending_dues - record.damages_deduction
    
    def action_complete_exit(self):
        self.write({'status': 'completed'})
        
        # Terminate the agreement
        self.agreement_id.action_terminate()
        
        # Archive tenant if no other active agreements
        if not self.tenant_id.agreement_ids.filtered(lambda a: a.state == 'active'):
            self.tenant_id.write({'status': 'inactive'})
    
    def action_archive(self):
        self.write({'status': 'archived'})
