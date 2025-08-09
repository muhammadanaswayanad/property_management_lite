from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
from datetime import date, timedelta


class AccountInvoice(models.Model):
    _inherit = 'account.move'
    _description = 'Journal Entry/Invoice'
    _order = 'invoice_date desc, id desc'

    # name = fields.Char('Invoice Number', required=True, copy=False, readonly=True, 
    #                    default=lambda self: _('New'))
    
    # Basic Information
    # invoice_date = fields.Date('Invoice Date', required=True, default=fields.Date.today, tracking=True)
    # invoice_date_due = fields.Date('Due Date', required=True, tracking=True)
    
    # Relations
    tenant_id = fields.Many2one('property.tenant', 'Tenant', tracking=True)
    @api.onchange('partner_id')
    def _onchange_partner_id_tenant(self):
       if self.partner_id:
           self.tenant_id = self.partner_id.tenant_id

    room_id = fields.Many2one('property.room', 'Room', tracking=True, domain="[('property_id','=',property_id)]")

    @api.onchange('property_id')
    def _onchange_property_id(self):
        if self.property_id:
            self.room_id = False
            self.agreement_id = False
    property_id = fields.Many2one('property.property', string='Property', store=True)
    agreement_id = fields.Many2one('property.agreement', 'Agreement',)
    collection_id = fields.Many2one('property.collection', 'Collection', readonly=True)
    
    # Invoice Lines
    # invoice_line_ids = fields.One2many('property.invoice.line', 'invoice_id', 'Invoice Lines')
    
    # Amounts
    # currency_id = fields.Many2one('res.currency', 'Currency', 
    #                               default=lambda self: self.env.company.currency_id)
    # amount_untaxed = fields.Monetary('Subtotal', compute='_compute_amounts', store=True, currency_field='currency_id')
    # amount_tax = fields.Monetary('Tax', compute='_compute_amounts', store=True, currency_field='currency_id')
    # amount_total = fields.Monetary('Total', compute='_compute_amounts', store=True, currency_field='currency_id')
    # amount_paid = fields.Monetary('Amount Paid', currency_field='currency_id', tracking=True)
    # amount_residual = fields.Monetary('Amount Due', compute='_compute_amounts', store=True, currency_field='currency_id')
    
    # Status
    # state = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('posted', 'Posted'),
    #     ('paid', 'Paid'),
    #     ('partial', 'Partially Paid'),
    #     ('cancelled', 'Cancelled'),
    # ], string='Status', default='draft', tracking=True)
    
    # Payment Info
    # payment_ids = fields.One2many('property.payment', 'invoice_id', 'Payments')
    # payment_state = fields.Selection([
    #     ('not_paid', 'Not Paid'),
    #     ('in_payment', 'In Payment'),
    #     ('partial', 'Partially Paid'),
    #     ('paid', 'Paid'),
    #     ('reversed', 'Reversed'),
    # ], string='Payment Status', compute='_compute_payment_state', store=True)
    
    # Additional Fields
    invoice_type = fields.Selection([
        ('rent', 'Monthly Rent'),
        ('deposit', 'Security Deposit'),
        ('maintenance', 'Maintenance'),
        ('utility', 'Utilities'),
        ('penalty', 'Late Fee'),
        ('other', 'Other'),
    ], string='Invoice Type', default='rent')

    def _default_period_from(self):
        today = date.today()
        return today.replace(day=1)

    def _default_period_to(self):
        today = date.today()
        next_month = today.replace(day=28) + timedelta(days=4)  # this will never fail
        last_day = next_month - timedelta(days=next_month.day)
        return last_day

    period_from = fields.Date('Period From', default=_default_period_from)
    period_to = fields.Date('Period To', default=_default_period_to)
    notes = fields.Text('Terms and Conditions')
    
    # Company Info
    # company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    
    # @api.model
    # def create(self, vals):
    #     if vals.get('name', _('New')) == _('New'):
    #         vals['name'] = self.env['ir.sequence'].next_by_code('property.invoice') or _('New')
    #     return super(PropertyInvoice, self).create(vals)

    # @api.depends('invoice_line_ids.price_total')
    # def _compute_amounts(self):
    #     for invoice in self:
    #         amount_total = 0.0
    #         for line in invoice.invoice_line_ids:
    #             amount_total += line.price_subtotal
            
    #         invoice.amount_untaxed = amount_total
    #         invoice.amount_tax = 0.0
    #         invoice.amount_total = amount_total
    #         invoice.amount_residual = invoice.amount_total - invoice.amount_paid

    # @api.depends('amount_total', 'amount_paid')
    # def _compute_payment_state(self):
    #     for invoice in self:
    #         if invoice.amount_paid == 0:
    #             invoice.payment_state = 'not_paid'
    #         elif invoice.amount_paid >= invoice.amount_total:
    #             invoice.payment_state = 'paid'
    #         else:
    #             invoice.payment_state = 'partial'

    @api.onchange('room_id')
    def _onchange_room_id(self):
        if self.room_id:
            self.tenant_id = self.room_id.current_tenant_id
            self.agreement_id = self.room_id.current_agreement_id
            self._onchange_agreement_id()

    @api.onchange('agreement_id', 'invoice_date', 'invoice_type')
    def _onchange_agreement_id(self):
        if self.agreement_id and self.invoice_date:
            # Set due invoice_date based on payment terms
            self.invoice_date_due = self.invoice_date + timedelta(days=self.agreement_id.payment_terms or 30)
            
            # Create default invoice lines based on agreement
            lines = []
            if self.invoice_type == 'rent':
                lines.append({
                    'product_id': self.env.ref('property_management_lite.product_property_rent').product_variant_id.id,
                    'name': f'Monthly Rent - {self.room_id.name}',
                    'quantity': 1,
                    'price_unit': self.agreement_id.rent_amount,
                })
            elif self.invoice_type == 'deposit':
                lines.append({
                    'product_id': self.env.ref('property_management_lite.product_property_deposit').product_variant_id.id,
                    'name': f'Security Deposit - {self.room_id.name}',
                    'quantity': 1,
                    'price_unit': self.agreement_id.deposit_amount,
                })
            
            self.invoice_line_ids = [(5, 0, 0)] + [(0, 0, line) for line in lines]

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
            ('invoice_date', '>=', invoice_date.replace(day=1)),
            ('invoice_date', '<=', invoice_date),
            ('state', '!=', 'cancelled')
        ])
        
        if not existing:
            # Calculate period
            period_from = invoice_date.replace(day=1)
            if invoice_date.month == 12:
                period_to = period_from.replace(year=period_from.year + 1, month=1) - timedelta(days=1)
            else:
                period_to = period_from.replace(month=period_from.month + 1) - timedelta(days=1)
            
            # Create invoice
            invoice = self.create({
                'partner_id': agreement.tenant_id.partner_id.id,
                'tenant_id': agreement.tenant_id.id,
                'room_id': agreement.room_id.id,
                'agreement_id': agreement.id,
                'invoice_date': invoice_date,
                'invoice_date_due': invoice_date + timedelta(days=agreement.payment_terms or 30),
                'move_type': 'out_invoice',
                'invoice_type': 'rent',
                'period_from': period_from,
                'period_to': period_to,
                'invoice_line_ids': [(0, 0, {
                    'product_id': self.env.ref('property_management_lite.product_property_rent').product_variant_id.id,
                    'name': f'Monthly Rent - {agreement.room_id.name} ({period_from.strftime("%B %Y")})',
                    'quantity': 1,
                    'price_unit': agreement.rent_amount,
                })],
                'notes': 'Monthly rent invoice as per rental agreement.',
            })
            
            # Auto-post if configured
            if agreement.auto_post_invoices:
                invoice.action_post()

    def action_register_payment(self):
        res = super(AccountInvoice, self).action_register_payment()
        res['context'].update({
            'default_tenant_id': self.tenant_id.id,
            'default_room_id': self.room_id.id,
            'default_property_id': self.property_id.id,
            'default_agreement_id': self.agreement_id.id
        })
        return res
    
class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    name = fields.Char(compute="_compute_name", store=True, readonly=False)

    def _compute_name(self):
        for line in self:
            line.name = line.name

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.description_sale or self.product_id.name

    @api.model_create_multi
    def create(self, vals_list):
        # Override create method to set name
        recs = super(AccountInvoiceLine, self).create(vals_list)
        for rec in recs:
            if not rec.name:
                rec.write({'name': rec.product_id.description_sale or rec.product_id.name})
        return recs


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    _description = 'Property Payment'
    
    # Relations
    tenant_id = fields.Many2one('property.tenant', compute="_compute_tenant", readonly=True, store=True)
    @api.depends('partner_id')
    def _compute_tenant(self):
        for payment in self:
            if payment.partner_id:
                payment.tenant_id = payment.partner_id.tenant_id

    collection_id = fields.Many2one('property.collection', 'Collection')
    # room_id = fields.Many2one('property.room', 'Room', tracking=True)
    # property_id = fields.Many2one(related='room_id.property_id', string='Property', store=True)
    # agreement_id = fields.Many2one('property.agreement', 'Agreement',)

    reference = fields.Char('Reference', tracking=True)

    notes = fields.Text('Notes', tracking=True)
    
    # # Payment Details
    # payment_method = fields.Selection([
    #     ('cash', 'Cash'),
    #     ('bank_transfer', 'Bank Transfer'),
    #     ('cheque', 'Cheque'),
    #     ('online', 'Online Payment'),
    #     ('card', 'Card Payment'),
    # ], string='Payment Method', required=True, default='cash', tracking=True)
    

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    tenant_id = fields.Many2one('property.tenant', 'Tenant', tracking=True)
    # room_id = fields.Many2one('property.room', 'Room', tracking=True)
    # property_id = fields.Many2one(related='room_id.property_id', string='Property', store=True)
    # agreement_id = fields.Many2one('property.agreement', 'Agreement',)
    reference = fields.Char('Reference', tracking=True)

    notes = fields.Text('Notes', tracking=True)


    def _create_payment_vals_from_wizard(self, batch_result):
        values = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard(batch_result)
        values.update({
            'tenant_id': self.tenant_id.id,
            'notes': self.notes,
            # 'room_id': self.room_id.id,
            # 'property_id': self.property_id.id,
            # 'agreement_id': self.agreement_id.id,
            'reference': self.reference
        })
        return values

    def action_create_payments(self):
        """Override to handle property payments"""
        res = super(AccountPaymentRegister, self).action_create_payments()
        return res
    
# class PropertyPaymentWizard(models.TransientModel):
#     _name = 'property.payment.wizard'
#     _description = 'Property Payment Registration Wizard'

#     invoice_id = fields.Many2one('property.invoice', 'Invoice', required=True)
#     tenant_id = fields.Many2one(related='invoice_id.tenant_id', readonly=True)
#     amount = fields.Monetary('Payment Amount', required=True, currency_field='currency_id')
#     currency_id = fields.Many2one(related='invoice_id.currency_id', readonly=True)
#     date = fields.Date('Payment Date', required=True, default=fields.Date.today)
#     payment_method = fields.Selection([
#         ('cash', 'Cash'),
#         ('bank_transfer', 'Bank Transfer'),
#         ('cheque', 'Cheque'),
#         ('online', 'Online Payment'),
#         ('card', 'Card Payment'),
#     ], string='Payment Method', required=True, default='cash')
#     reference = fields.Char('Reference')

#     def action_register_payment(self):
#         """Register the payment"""
#         payment = self.env['property.payment'].create({
#             'invoice_id': self.invoice_id.id,
#             'amount': self.amount,
#             'date': self.date,
#             'payment_method': self.payment_method,
#             'reference': self.reference,
#         })
        
#         payment.action_post()
        
#         # Also create collection record
#         self.env['property.collection'].create({
#             'tenant_id': self.invoice_id.tenant_id.id,
#             'room_id': self.invoice_id.room_id.id,
#             'agreement_id': self.invoice_id.agreement_id.id,
#             'date': self.date,
#             'amount_collected': self.amount,
#             'payment_method': self.payment_method,
#             'reference_number': self.reference,
#             'collection_type': self.invoice_id.invoice_type,
#             'period_from': self.invoice_id.period_from,
#             'period_to': self.invoice_id.period_to,
#             'status': 'collected',
#             'invoice_reference': self.invoice_id.name,
#         })
        
#         return {'type': 'ir.actions.act_window_close'}
