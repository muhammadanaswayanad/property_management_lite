from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class PropertyAgreement(models.Model):
    _name = 'property.agreement'
    _description = 'Rental Agreement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc'

    name = fields.Char('Agreement Reference', compute='_compute_name', store=True)
    
    # Parties
    tenant_id = fields.Many2one('property.tenant', 'Tenant', required=True, tracking=True)
    room_id = fields.Many2one('property.room', 'Room', required=True, tracking=True)
    property_id = fields.Many2one(related='room_id.property_id', string='Property', store=True)
    
    # Dates
    start_date = fields.Date('Start Date', required=True, tracking=True)
    end_date = fields.Date('End Date', required=True, tracking=True)
    notice_period_days = fields.Integer('Notice Period (Days)', default=30)
    
    # Financial Terms
    rent_amount = fields.Monetary('Monthly Rent', required=True, currency_field='currency_id', tracking=True)
    deposit_amount = fields.Monetary('Security Deposit', currency_field='currency_id', tracking=True)
    token_money = fields.Monetary('Token Money', currency_field='currency_id')
    extra_charges = fields.Monetary('Extra Charges', currency_field='currency_id')

    invoice_ids = fields.One2many('account.move', 'agreement_id', 'Invoices')
    invoices_count = fields.Integer('Invoices Count', compute='_compute_invoices_count',)

    def _compute_invoices_count(self):
        for agreement in self:
            agreement.invoices_count = len(agreement.invoice_ids.filtered(lambda inv: inv.move_type in ('out_invoice', 'out_refund')))

    def action_view_invoices(self):
        return {
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', self.invoice_ids.ids), ('move_type', 'in', ('out_invoice', 'out_refund'))],
        }

    # Payment Terms
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('online', 'Online Payment'),
    ], string='Payment Method', required=True, default='cash')
    
    payment_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ], string='Payment Frequency', required=True, default='monthly')
    
    payment_day = fields.Integer('Payment Day of Month', default=1, help="Day of month when rent is due")
    payment_terms = fields.Integer('Payment Terms (Days)', default=30, help="Number of days to pay invoice")
    
    # Invoicing Automation
    auto_generate_invoices = fields.Boolean('Auto Generate Invoices', default=True, 
                                          help="Automatically generate monthly invoices")
    auto_post_invoices = fields.Boolean('Auto Post Invoices', default=False,
                                      help="Automatically post generated invoices")
    invoice_day = fields.Integer('Invoice Generation Day', default=1, 
                               help="Day of month to generate invoice")
    advance_invoice_days = fields.Integer('Advance Invoice Days', default=5,
                                        help="Generate invoice X days before due date")
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    # Agreement Details
    agreement_type = fields.Selection([
        ('fixed', 'Fixed Term'),
        ('renewable', 'Auto-Renewable'),
        ('month_to_month', 'Month to Month'),
    ], string='Agreement Type', default='fixed')
    
    # Terms and Conditions
    terms_and_conditions = fields.Html('Terms and Conditions')
    special_conditions = fields.Text('Special Conditions')
    
    # Utilities & Inclusions
    electricity_included = fields.Boolean('Electricity Included')
    water_included = fields.Boolean('Water Included', default=True)
    gas_included = fields.Boolean('Gas Included')
    internet_included = fields.Boolean('Internet Included', default=True)
    parking_included = fields.Boolean('Parking Included')
    
    # Relations
    collection_ids = fields.One2many('property.collection', 'agreement_id', 'Collections')
    
    # Computed Fields
    duration_months = fields.Integer('Duration (Months)', compute='_compute_duration')
    days_remaining = fields.Integer('Days Remaining', compute='_compute_days_remaining')
    total_collected = fields.Monetary('Total Collected', compute='_compute_payment_stats', currency_field='currency_id')
    pending_amount = fields.Monetary('Pending Amount', compute='_compute_payment_stats', currency_field='currency_id')
    last_payment_date = fields.Date('Last Payment', compute='_compute_payment_stats')
    
    # Financial
    currency_id = fields.Many2one('res.currency', 'Currency', 
                                  default=lambda self: self.env.company.currency_id)
    
    # Documents
    agreement_document = fields.Binary('Agreement Document')
    agreement_filename = fields.Char('Agreement Filename')
    
    @api.depends('tenant_id', 'room_id', 'start_date')
    def _compute_name(self):
        for record in self:
            if record.tenant_id and record.room_id and record.start_date:
                record.name = f"AGR/{record.tenant_id.name}/{record.room_id.name}/{record.start_date.strftime('%Y%m%d')}"
            else:
                record.name = 'New Agreement'
    
    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for record in self:
            if record.start_date and record.end_date:
                delta = record.end_date - record.start_date
                record.duration_months = round(delta.days / 30)
            else:
                record.duration_months = 0
    
    @api.depends('end_date')
    def _compute_days_remaining(self):
        today = fields.Date.today()
        for record in self:
            if record.end_date and record.state == 'active':
                delta = record.end_date - today
                record.days_remaining = delta.days
            else:
                record.days_remaining = 0
    
    @api.depends('collection_ids.amount_collected')
    def _compute_payment_stats(self):
        for record in self:
            record.total_collected = sum(record.collection_ids.mapped('amount_collected'))
            record.last_payment_date = max(record.collection_ids.mapped('date')) if record.collection_ids else False
            
            # Calculate pending amount (simplified logic)
            if record.state == 'active':
                # This should be more sophisticated based on payment schedule
                months_passed = (fields.Date.today() - record.start_date).days / 30
                expected_amount = record.rent_amount * months_passed
                record.pending_amount = max(0, expected_amount - record.total_collected)
            else:
                record.pending_amount = 0
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date:
                if record.end_date <= record.start_date:
                    raise ValidationError(_('End date must be after start date!'))
    
    @api.constrains('room_id', 'start_date', 'end_date')
    def _check_room_availability(self):
        for record in self:
            if record.room_id and record.start_date and record.end_date:
                # Check for overlapping agreements
                overlapping = self.search([
                    ('room_id', '=', record.room_id.id),
                    ('state', 'in', ['active', 'draft']),
                    ('id', '!=', record.id),
                    '|',
                    '&', ('start_date', '<=', record.start_date), ('end_date', '>=', record.start_date),
                    '&', ('start_date', '<=', record.end_date), ('end_date', '>=', record.end_date),
                ])
                if overlapping:
                    raise ValidationError(_('Room is already rented during this period!'))
    
    @api.onchange('room_id')
    def _onchange_room_id(self):
        if self.room_id:
            self.rent_amount = self.room_id.rent_amount
            self.deposit_amount = self.room_id.deposit_amount
            self.property_id = self.room_id.property_id
    
    @api.onchange('tenant_id')
    def _onchange_tenant_id(self):
        if self.tenant_id:
            self.payment_method = self.tenant_id.payment_method
    
    def action_activate(self):
        for record in self:
            # Update room status
            record.room_id.write({
                'status': 'occupied',
                'current_tenant_id': record.tenant_id.id,
                'current_agreement_id': record.id,
            })
            
            # Update tenant status
            record.tenant_id.write({
                'status': 'active',
                'current_room_id': record.room_id.id,
            })
            
            record.write({'state': 'active'})
            
            # Create invoice reference if needed
            record._create_monthly_invoice_reference()
    
    def action_terminate(self):
        for record in self:
            # Update room status
            record.room_id.write({
                'status': 'vacant',
                'current_tenant_id': False,
                'current_agreement_id': False,
            })
            
            # Update tenant status
            record.tenant_id.write({
                'current_room_id': False,
            })
            
            record.write({'state': 'terminated'})
    
    def action_renew(self):
        return {
            'name': _('Renew Agreement'),
            'view_mode': 'form',
            'res_model': 'property.agreement',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_tenant_id': self.tenant_id.id,
                'default_room_id': self.room_id.id,
                'default_rent_amount': self.rent_amount,
                'default_deposit_amount': self.deposit_amount,
                'default_start_date': self.end_date + timedelta(days=1),
                'default_end_date': self.end_date + timedelta(days=365),
            }
        }
    
    def _create_monthly_invoice_reference(self):
        """Create monthly invoice reference for the agreement (Community Edition)"""
        self.ensure_one()
        
        # Create a simple invoice reference without actual accounting integration
        invoice_ref = f"INV/{self.tenant_id.name[:10]}/{fields.Date.today().strftime('%Y%m%d')}"
        
        # You can extend this to create a simple invoice record in a custom model
        # or integrate with accounting module if available
        
        return invoice_ref
    
    @api.model
    def _cron_check_expiring_agreements(self):
        """Cron job to check for expiring agreements"""
        expiring_date = fields.Date.today() + timedelta(days=30)
        expiring_agreements = self.search([
            ('state', '=', 'active'),
            ('end_date', '<=', expiring_date),
        ])
        
        for agreement in expiring_agreements:
            # Send notification or create activity
            agreement.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=f'Agreement expiring for {agreement.tenant_id.name}',
                note=f'Agreement for room {agreement.room_id.name} expires on {agreement.end_date}',
                user_id=agreement.room_id.property_id.manager_id.id,
            )
