from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta


class PropertyInvoice(models.Model):
    _name = 'property.invoice'
    _description = 'Property Rental Invoice'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char('Invoice Number', required=True, copy=False, readonly=True, 
                       default=lambda self: _('New'))
    
    # Basic Information
    date = fields.Date('Invoice Date', required=True, default=fields.Date.today, tracking=True)
    due_date = fields.Date('Due Date', required=True, tracking=True)
    
    # Relations
    tenant_id = fields.Many2one('property.tenant', 'Tenant', required=True, tracking=True)
    room_id = fields.Many2one('property.room', 'Room', required=True, tracking=True)
    property_id = fields.Many2one(related='room_id.property_id', string='Property', store=True)
    agreement_id = fields.Many2one('property.agreement', 'Agreement')
    collection_id = fields.Many2one('property.collection', 'Collection', readonly=True)
    
    # Invoice Lines
    invoice_line_ids = fields.One2many('property.invoice.line', 'invoice_id', 'Invoice Lines')
    
    # Amounts
    currency_id = fields.Many2one('res.currency', 'Currency', 
                                  default=lambda self: self.env.company.currency_id)
    amount_untaxed = fields.Monetary('Subtotal', compute='_compute_amounts', store=True, currency_field='currency_id')
    amount_tax = fields.Monetary('Tax', compute='_compute_amounts', store=True, currency_field='currency_id')
    amount_total = fields.Monetary('Total', compute='_compute_amounts', store=True, currency_field='currency_id')
    amount_paid = fields.Monetary('Amount Paid', currency_field='currency_id', tracking=True)
    amount_residual = fields.Monetary('Amount Due', compute='_compute_amounts', store=True, currency_field='currency_id')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    # Payment Info
    payment_ids = fields.One2many('property.payment', 'invoice_id', 'Payments')
    payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('reversed', 'Reversed'),
    ], string='Payment Status', compute='_compute_payment_state', store=True)
    
    # Additional Fields
    invoice_type = fields.Selection([
        ('rent', 'Monthly Rent'),
        ('deposit', 'Security Deposit'),
        ('maintenance', 'Maintenance'),
        ('utility', 'Utilities'),
        ('penalty', 'Late Fee'),
        ('other', 'Other'),
    ], string='Invoice Type', default='rent')
    
    period_from = fields.Date('Period From')
    period_to = fields.Date('Period To')
    notes = fields.Text('Terms and Conditions')
    
    # Company Info
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('property.invoice') or _('New')
        return super(PropertyInvoice, self).create(vals)

    @api.depends('invoice_line_ids.price_total')
    def _compute_amounts(self):
        for invoice in self:
            amount_total = 0.0
            for line in invoice.invoice_line_ids:
                amount_total += line.price_subtotal
            
            invoice.amount_untaxed = amount_total
            invoice.amount_tax = 0.0
            invoice.amount_total = amount_total
            invoice.amount_residual = invoice.amount_total - invoice.amount_paid

    @api.depends('amount_total', 'amount_paid')
    def _compute_payment_state(self):
        for invoice in self:
            if invoice.amount_paid == 0:
                invoice.payment_state = 'not_paid'
            elif invoice.amount_paid >= invoice.amount_total:
                invoice.payment_state = 'paid'
            else:
                invoice.payment_state = 'partial'

    @api.onchange('room_id')
    def _onchange_room_id(self):
        if self.room_id:
            self.tenant_id = self.room_id.current_tenant_id
            self.agreement_id = self.room_id.current_agreement_id
            self._onchange_agreement_id()

    @api.onchange('agreement_id')
    def _onchange_agreement_id(self):
        if self.agreement_id:
            # Set due date based on payment terms
            self.due_date = self.date + timedelta(days=self.agreement_id.payment_terms or 30)
            
            # Create default invoice lines based on agreement
            lines = []
            if self.invoice_type == 'rent':
                lines.append({
                    'name': f'Monthly Rent - {self.room_id.name}',
                    'quantity': 1,
                    'price_unit': self.agreement_id.rent_amount,
                })
            elif self.invoice_type == 'deposit':
                lines.append({
                    'name': f'Security Deposit - {self.room_id.name}',
                    'quantity': 1,
                    'price_unit': self.agreement_id.deposit_amount,
                })
            
            self.invoice_line_ids = [(5, 0, 0)] + [(0, 0, line) for line in lines]

    def action_post(self):
        """Post the invoice"""
        if not self.invoice_line_ids:
            raise UserError(_('You cannot post an invoice without any invoice lines.'))
        self.write({'state': 'posted'})

    def action_cancel(self):
        """Cancel the invoice"""
        self.write({'state': 'cancelled'})

    def action_draft(self):
        """Reset to draft"""
        self.write({'state': 'draft'})

    def action_register_payment(self):
        """Open payment registration wizard"""
        return {
            'name': _('Register Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'property.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_invoice_id': self.id,
                'default_amount': self.amount_residual,
                'default_tenant_id': self.tenant_id.id,
            }
        }

    def action_view_payments(self):
        """View related payments"""
        return {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'property.payment',
            'view_mode': 'list,form',
            'domain': [('invoice_id', '=', self.id)],
            'context': {'default_invoice_id': self.id}
        }

    def action_print_invoice(self):
        """Print invoice PDF"""
        return self.env.ref('property_management_lite.action_report_property_invoice').report_action(self)

    def action_send_invoice(self):
        """Send invoice by email"""
        template = self.env.ref('property_management_lite.email_template_property_invoice', False)
        if template:
            composer = self.env['mail.compose.message'].with_context(
                default_model='property.invoice',
                default_res_id=self.id,
                default_template_id=template.id,
                default_use_template=True,
                force_email=True
            ).create({})
            return composer.action_send_mail()
        return False

    @api.model
    def create_monthly_invoices(self):
        """Cron job to create monthly invoices"""
        today = fields.Date.today()
        
        # Find all active agreements
        active_agreements = self.env['property.agreement'].search([('state', '=', 'active')])
        
        for agreement in active_agreements:
            # Check if invoice should be generated
            if agreement.payment_frequency == 'monthly' and today.day == agreement.invoice_day:
                self._create_monthly_invoice(agreement, today)

    def _create_monthly_invoice(self, agreement, invoice_date):
        """Create monthly invoice for agreement"""
        # Check if invoice already exists for this month
        existing = self.search([
            ('agreement_id', '=', agreement.id),
            ('invoice_type', '=', 'rent'),
            ('date', '>=', invoice_date.replace(day=1)),
            ('date', '<=', invoice_date),
            ('state', '!=', 'cancelled')
        ])
        
        if not existing:
            # Calculate period
            period_from = invoice_date.replace(day=1)
            if invoice_date.month == 12:
                period_to = period_from.replace(year=period_from.year + 1, month=1) - fields.timedelta(days=1)
            else:
                period_to = period_from.replace(month=period_from.month + 1) - fields.timedelta(days=1)
            
            # Create invoice
            invoice = self.create({
                'tenant_id': agreement.tenant_id.id,
                'room_id': agreement.room_id.id,
                'agreement_id': agreement.id,
                'date': invoice_date,
                'due_date': invoice_date + fields.timedelta(days=agreement.payment_terms or 30),
                'invoice_type': 'rent',
                'period_from': period_from,
                'period_to': period_to,
                'invoice_line_ids': [(0, 0, {
                    'name': f'Monthly Rent - {agreement.room_id.name} ({period_from.strftime("%B %Y")})',
                    'quantity': 1,
                    'price_unit': agreement.rent_amount,
                })],
                'notes': 'Monthly rent invoice as per rental agreement.',
            })
            
            # Auto-post if configured
            if agreement.auto_post_invoices:
                invoice.action_post()


class PropertyInvoiceLine(models.Model):
    _name = 'property.invoice.line'
    _description = 'Property Invoice Line'

    invoice_id = fields.Many2one('property.invoice', 'Invoice', required=True, ondelete='cascade')
    name = fields.Text('Description', required=True)
    quantity = fields.Float('Quantity', default=1.0, required=True)
    price_unit = fields.Monetary('Unit Price', required=True, currency_field='currency_id')
    
    # Computed fields
    currency_id = fields.Many2one(related='invoice_id.currency_id', store=True)
    price_subtotal = fields.Monetary('Subtotal', compute='_compute_amounts', store=True, currency_field='currency_id')
    price_total = fields.Monetary('Total', compute='_compute_amounts', store=True, currency_field='currency_id')

    @api.depends('quantity', 'price_unit')
    def _compute_amounts(self):
        for line in self:
            price = line.price_unit * line.quantity
            line.price_subtotal = price
            line.price_total = price


class PropertyPayment(models.Model):
    _name = 'property.payment'
    _description = 'Property Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Payment Reference', required=True, copy=False, readonly=True, 
                       default=lambda self: _('New'))
    
    date = fields.Date('Payment Date', required=True, default=fields.Date.today, tracking=True)
    amount = fields.Monetary('Amount', required=True, currency_field='currency_id', tracking=True)
    
    # Relations
    invoice_id = fields.Many2one('property.invoice', 'Invoice', required=True)
    tenant_id = fields.Many2one(related='invoice_id.tenant_id', store=True)
    collection_id = fields.Many2one('property.collection', 'Collection')
    
    # Payment Details
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('online', 'Online Payment'),
        ('card', 'Card Payment'),
    ], string='Payment Method', required=True, default='cash', tracking=True)
    
    reference = fields.Char('Reference')
    currency_id = fields.Many2one(related='invoice_id.currency_id', store=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('reconciled', 'Reconciled'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('property.payment') or _('New')
        return super(PropertyPayment, self).create(vals)

    def action_post(self):
        """Post the payment and update invoice"""
        self.write({'state': 'posted'})
        
        # Update invoice payment amount
        invoice = self.invoice_id
        total_payments = sum(invoice.payment_ids.filtered(lambda p: p.state == 'posted').mapped('amount'))
        invoice.amount_paid = total_payments
        
        # Update invoice state based on payment
        if invoice.amount_paid >= invoice.amount_total:
            invoice.state = 'paid'
        elif invoice.amount_paid > 0:
            invoice.state = 'partial'

    def action_cancel(self):
        """Cancel the payment"""
        self.write({'state': 'cancelled'})
        
        # Recalculate invoice amounts
        invoice = self.invoice_id
        total_payments = sum(invoice.payment_ids.filtered(lambda p: p.state == 'posted').mapped('amount'))
        invoice.amount_paid = total_payments


class PropertyPaymentWizard(models.TransientModel):
    _name = 'property.payment.wizard'
    _description = 'Property Payment Registration Wizard'

    invoice_id = fields.Many2one('property.invoice', 'Invoice', required=True)
    tenant_id = fields.Many2one(related='invoice_id.tenant_id', readonly=True)
    amount = fields.Monetary('Payment Amount', required=True, currency_field='currency_id')
    currency_id = fields.Many2one(related='invoice_id.currency_id', readonly=True)
    date = fields.Date('Payment Date', required=True, default=fields.Date.today)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('online', 'Online Payment'),
        ('card', 'Card Payment'),
    ], string='Payment Method', required=True, default='cash')
    reference = fields.Char('Reference')

    def action_register_payment(self):
        """Register the payment"""
        payment = self.env['property.payment'].create({
            'invoice_id': self.invoice_id.id,
            'amount': self.amount,
            'date': self.date,
            'payment_method': self.payment_method,
            'reference': self.reference,
        })
        
        payment.action_post()
        
        # Also create collection record
        self.env['property.collection'].create({
            'tenant_id': self.invoice_id.tenant_id.id,
            'room_id': self.invoice_id.room_id.id,
            'agreement_id': self.invoice_id.agreement_id.id,
            'date': self.date,
            'amount_collected': self.amount,
            'payment_method': self.payment_method,
            'reference_number': self.reference,
            'collection_type': self.invoice_id.invoice_type,
            'period_from': self.invoice_id.period_from,
            'period_to': self.invoice_id.period_to,
            'status': 'collected',
            'invoice_reference': self.invoice_id.name,
        })
        
        return {'type': 'ir.actions.act_window_close'}
