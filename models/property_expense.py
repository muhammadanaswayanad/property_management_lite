from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PropertyExpense(models.Model):
    _name = 'property.expense'
    _description = 'Property Expense'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    name = fields.Char('Description', required=True, tracking=True)
    date = fields.Date('Date', required=True, default=fields.Date.today, tracking=True)
    amount = fields.Monetary('Amount', required=True, currency_field='currency_id', tracking=True)
    
    # Relations
    property_id = fields.Many2one('property.property', 'Property', tracking=True)
    flat_id = fields.Many2one('property.flat', 'Flat')
    room_id = fields.Many2one('property.room', 'Room')
    
    # Expense Details
    expense_type = fields.Selection([
        ('dewa', 'DEWA (Electricity & Water)'),
        ('maintenance', 'Maintenance'),
        ('plumbing', 'Plumbing Items'),
        ('electrical', 'Electrical Items'),
        ('paint', 'Paint'),
        ('ac', 'A.C (Air Conditioning)'),
        ('labor', 'Labor'),
        ('cleaning', 'Cleaning'),
        ('security', 'Security'),
        ('staff_payment', 'Staff Payment'),
        ('repair', 'Repair'),
        ('utility', 'Other Utility Bills'),
        ('insurance', 'Insurance'),
        ('tax', 'Property Tax'),
        ('commission', 'Agent Commission'),
        ('legal', 'Legal Fees'),
        ('other', 'Other'),
    ], string='Expense Type', required=True, default='maintenance')
    
    category = fields.Selection([
        ('operational', 'Operational'),
        ('capital', 'Capital Expenditure'),
        ('emergency', 'Emergency'),
    ], string='Category', default='operational')
    
    # Payment Information
    paid_by = fields.Many2one('res.users', 'Paid By', default=lambda self: self.env.user)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('card', 'Card'),
    ], string='Payment Method', default='cash')
    
    reference_number = fields.Char('Reference Number')
    vendor_id = fields.Many2one('res.partner', 'Vendor', domain=[('supplier_rank', '>', 0)])
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True)
    
    # Approval
    approved_by = fields.Many2one('res.users', 'Approved By')
    approval_date = fields.Datetime('Approval Date')
    
    # Additional Information
    notes = fields.Text('Notes')
    urgency = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string='Urgency', default='medium')
    
    # Attachments
    bill_image = fields.Binary('Bill/Receipt')
    bill_filename = fields.Char('Bill Filename')
    attachment_ids = fields.One2many('ir.attachment', 'res_id', 'Attachments',
                                     domain=[('res_model', '=', 'property.expense')])
    
    # Financial
    currency_id = fields.Many2one('res.currency', 'Currency', 
                                  default=lambda self: self.env.company.currency_id)
    
    # Bill Reference (Community Edition)
    bill_reference = fields.Char('Related Bill Reference')
    
    @api.onchange('flat_id')
    def _onchange_flat_id(self):
        if self.flat_id:
            self.property_id = self.flat_id.property_id
    
    @api.onchange('room_id')
    def _onchange_room_id(self):
        if self.room_id:
            self.flat_id = self.room_id.flat_id
            self.property_id = self.room_id.property_id
    
    @api.constrains('amount')
    def _check_amount_positive(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(_('Expense amount must be positive!'))
    
    def action_submit(self):
        self.write({'state': 'submitted'})
    
    def action_approve(self):
        self.write({
            'state': 'approved',
            'approved_by': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })
    
    def action_pay(self):
        self.write({'state': 'paid'})
    
    def action_reject(self):
        self.write({'state': 'rejected'})
    
    def action_create_bill_reference(self):
        """Create bill reference for this expense (Community Edition)"""
        self.ensure_one()
        
        if not self.vendor_id:
            raise ValidationError(_('Vendor is required to create a bill reference!'))
        
        # Create a simple bill reference
        bill_ref = f"BILL/{self.vendor_id.name[:10]}/{self.date.strftime('%Y%m%d')}"
        self.bill_reference = bill_ref
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bill Reference Created'),
                'message': f'Bill reference: {bill_ref}',
                'type': 'success',
            }
        }
