from odoo import models, fields, api, _


class PropertyDueTracker(models.Model):
    _name = 'property.due.tracker'
    _description = 'Due Tracker'
    _order = 'due_date, priority desc'

    name = fields.Char('Description', compute='_compute_name', store=True)
    
    # Relations
    tenant_id = fields.Many2one('property.tenant', 'Tenant', required=True)
    room_id = fields.Many2one('property.room', 'Room', required=True)
    agreement_id = fields.Many2one('property.agreement', 'Agreement')
    
    # Due Information
    due_date = fields.Date('Due Date', required=True)
    amount_due = fields.Monetary('Amount Due', required=True, currency_field='currency_id')
    due_type = fields.Selection([
        ('rent', 'Monthly Rent'),
        ('deposit', 'Security Deposit'),
        ('penalty', 'Late Payment Penalty'),
        ('utility', 'Utility Bills'),
        ('maintenance', 'Maintenance Charges'),
        ('other', 'Other'),
    ], string='Due Type', required=True, default='rent')
    
    # Status
    status = fields.Selection([
        ('pending', 'Pending'),
        ('overdue', 'Overdue'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
        ('waived', 'Waived'),
    ], string='Status', compute='_compute_status', store=True)
    
    # Payment Tracking
    amount_paid = fields.Monetary('Amount Paid', currency_field='currency_id')
    outstanding_amount = fields.Monetary('Outstanding Amount', compute='_compute_outstanding', store=True, currency_field='currency_id')
    
    # Additional Information
    notes = fields.Text('Notes')
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string='Priority', default='medium')
    
    # Tracking
    days_overdue = fields.Integer('Days Overdue', compute='_compute_days_overdue', store=True)
    last_reminder_date = fields.Date('Last Reminder Date')
    reminder_count = fields.Integer('Reminder Count', default=0)
    
    # Financial
    currency_id = fields.Many2one('res.currency', 'Currency', 
                                  default=lambda self: self.env.company.currency_id)
    
    @api.depends('tenant_id', 'due_type', 'due_date')
    def _compute_name(self):
        for record in self:
            if record.tenant_id and record.due_type and record.due_date:
                record.name = f"{record.due_type.title()} - {record.tenant_id.name} - {record.due_date}"
            else:
                record.name = 'New Due'
    
    @api.depends('due_date', 'amount_paid', 'amount_due')
    def _compute_status(self):
        today = fields.Date.today()
        for record in self:
            if record.amount_paid >= record.amount_due:
                record.status = 'paid'
            elif record.amount_paid > 0:
                record.status = 'partially_paid'
            elif record.due_date < today:
                record.status = 'overdue'
            else:
                record.status = 'pending'
    
    @api.depends('amount_due', 'amount_paid')
    def _compute_outstanding(self):
        for record in self:
            record.outstanding_amount = record.amount_due - record.amount_paid
    
    @api.depends('due_date')
    def _compute_days_overdue(self):
        today = fields.Date.today()
        for record in self:
            if record.due_date and record.due_date < today and record.status != 'paid':
                record.days_overdue = (today - record.due_date).days
            else:
                record.days_overdue = 0
    
    def action_send_reminder(self):
        # Send reminder to tenant
        self.write({
            'last_reminder_date': fields.Date.today(),
            'reminder_count': self.reminder_count + 1,
        })
        
        # Create activity or send email/SMS
        self.activity_schedule(
            'mail.mail_activity_data_call',
            summary=f'Follow up on {self.due_type} payment',
            note=f'Amount due: {self.outstanding_amount}',
            user_id=self.env.user.id,
        )
    
    def action_mark_paid(self):
        self.write({
            'amount_paid': self.amount_due,
            'status': 'paid',
        })
    
    def action_waive(self):
        self.write({'status': 'waived'})
    
    @api.model
    def create_monthly_dues(self):
        """Create monthly dues for all active agreements"""
        active_agreements = self.env['property.agreement'].search([('state', '=', 'active')])
        
        for agreement in active_agreements:
            # Check if due already exists for current month
            existing_due = self.search([
                ('agreement_id', '=', agreement.id),
                ('due_type', '=', 'rent'),
                ('due_date', '=', fields.Date.today().replace(day=agreement.payment_day)),
            ])
            
            if not existing_due:
                self.create({
                    'tenant_id': agreement.tenant_id.id,
                    'room_id': agreement.room_id.id,
                    'agreement_id': agreement.id,
                    'due_date': fields.Date.today().replace(day=agreement.payment_day),
                    'amount_due': agreement.rent_amount,
                    'due_type': 'rent',
                })
