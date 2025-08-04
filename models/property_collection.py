from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PropertyCollection(models.Model):
    _name = 'property.collection'
    _description = 'Rent Collection'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char('Collection Reference', compute='_compute_name', store=True)
    
    # Basic Information
    date = fields.Date('Collection Date', required=True, default=fields.Date.today, tracking=True)
    amount_collected = fields.Monetary('Amount Collected', required=True, currency_field='currency_id', tracking=True)
    
    # Relations
    tenant_id = fields.Many2one('property.tenant', 'Tenant', required=True, tracking=True)
    room_id = fields.Many2one('property.room', 'Room', required=True, tracking=True)
    property_id = fields.Many2one(related='room_id.property_id', string='Property', store=True)
    agreement_id = fields.Many2one('property.agreement', 'Agreement')
    
    # Payment Details
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('online', 'Online Payment'),
        ('card', 'Card Payment'),
    ], string='Payment Method', required=True, default='cash', tracking=True)
    
    reference_number = fields.Char('Reference Number', help="Cheque number, transaction ID, etc.")
    
    # Collection Details
    collection_type = fields.Selection([
        ('rent', 'Monthly Rent'),
        ('deposit', 'Security Deposit'),
        ('token', 'Token Money'),
        ('extra', 'Extra Charges'),
        ('penalty', 'Late Payment Penalty'),
        ('maintenance', 'Maintenance Charges'),
        ('utility', 'Utility Bills'),
        ('other', 'Other'),
    ], string='Collection Type', required=True, default='rent')
    
    period_from = fields.Date('Period From')
    period_to = fields.Date('Period To')
    
    # Status
    status = fields.Selection([
        ('draft', 'Draft'),
        ('collected', 'Collected'),
        ('verified', 'Verified'),
        ('deposited', 'Deposited'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    # Additional Information
    notes = fields.Text('Notes')
    collected_by = fields.Many2one('res.users', 'Collected By', default=lambda self: self.env.user)
    verified_by = fields.Many2one('res.users', 'Verified By')
    verification_date = fields.Datetime('Verification Date')
    
    # Receipt Information
    receipt_number = fields.Char('Receipt Number')
    receipt_image = fields.Binary('Receipt Image')
    receipt_filename = fields.Char('Receipt Filename')
    
    # Financial
    currency_id = fields.Many2one('res.currency', 'Currency', 
                                  default=lambda self: self.env.company.currency_id)
    
    # Bank Information (for transfers)
    bank_id = fields.Many2one('res.bank', 'Bank')
    bank_account = fields.Char('Bank Account')
    
    # Late Payment
    due_date = fields.Date('Due Date')
    days_late = fields.Integer('Days Late', compute='_compute_days_late', store=True)
    late_fee = fields.Monetary('Late Fee', currency_field='currency_id')
    
    # Simple Invoice/Payment Reference (Community Edition)
    invoice_reference = fields.Char('Invoice Reference')
    payment_reference = fields.Char('Payment Reference')
    
    @api.depends('tenant_id', 'room_id', 'date', 'collection_type')
    def _compute_name(self):
        for record in self:
            if record.tenant_id and record.room_id and record.date:
                record.name = f"COL/{record.date.strftime('%Y%m%d')}/{record.tenant_id.name[:10]}/{record.room_id.room_number}"
            else:
                record.name = 'New Collection'
    
    @api.depends('due_date', 'date')
    def _compute_days_late(self):
        for record in self:
            if record.due_date and record.date:
                delta = record.date - record.due_date
                record.days_late = max(0, delta.days)
            else:
                record.days_late = 0
    
    @api.onchange('room_id')
    def _onchange_room_id(self):
        if self.room_id:
            self.tenant_id = self.room_id.current_tenant_id
            self.agreement_id = self.room_id.current_agreement_id
            if self.agreement_id:
                self.amount_collected = self.agreement_id.rent_amount
                self.payment_method = self.agreement_id.payment_method
    
    @api.onchange('tenant_id')
    def _onchange_tenant_id(self):
        if self.tenant_id:
            self.room_id = self.tenant_id.current_room_id
            if self.tenant_id.payment_method:
                self.payment_method = self.tenant_id.payment_method
    
    @api.onchange('collection_type', 'agreement_id')
    def _onchange_collection_type(self):
        if self.collection_type and self.agreement_id:
            if self.collection_type == 'rent':
                self.amount_collected = self.agreement_id.rent_amount
            elif self.collection_type == 'deposit':
                self.amount_collected = self.agreement_id.deposit_amount
            elif self.collection_type == 'extra':
                self.amount_collected = self.agreement_id.extra_charges
    
    @api.constrains('amount_collected')
    def _check_amount_positive(self):
        for record in self:
            if record.amount_collected <= 0:
                raise ValidationError(_('Collection amount must be positive!'))
    
    def action_collect(self):
        self.write({'status': 'collected'})
        # Generate receipt number
        if not self.receipt_number:
            sequence = self.env['ir.sequence'].next_by_code('property.collection') or '/'
            self.receipt_number = sequence
    
    def action_verify(self):
        self.write({
            'status': 'verified',
            'verified_by': self.env.user.id,
            'verification_date': fields.Datetime.now(),
        })
    
    def action_deposit(self):
        self.write({'status': 'deposited'})
    
    def action_cancel(self):
        self.write({'status': 'cancelled'})
    
    def action_print_receipt(self):
        # Simple receipt printing - can be enhanced with proper report
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'property.collection',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    @api.model
    def create_daily_collections_reminder(self):
        """Cron job to create daily collection reminders"""
        today = fields.Date.today()
        
        # Find all active agreements
        active_agreements = self.env['property.agreement'].search([('state', '=', 'active')])
        
        for agreement in active_agreements:
            # Check if collection is due based on payment frequency
            last_collection = self.search([
                ('agreement_id', '=', agreement.id),
                ('collection_type', '=', 'rent'),
                ('status', 'in', ['collected', 'verified', 'deposited'])
            ], order='date desc', limit=1)
            
            if agreement.payment_frequency == 'monthly':
                # Monthly payment due on specific day
                if today.day == agreement.payment_day:
                    self._create_due_reminder(agreement, today)
            elif agreement.payment_frequency == 'daily':
                # Daily payment
                if not last_collection or last_collection.date < today:
                    self._create_due_reminder(agreement, today)
    
    def _create_due_reminder(self, agreement, due_date):
        """Create a due reminder activity"""
        agreement.activity_schedule(
            'mail.mail_activity_data_todo',
            summary=f'Rent Collection Due - {agreement.tenant_id.name}',
            note=f'Monthly rent of {agreement.rent_amount} is due for room {agreement.room_id.name}',
            date_deadline=due_date,
            user_id=agreement.room_id.property_id.manager_id.id,
        )
