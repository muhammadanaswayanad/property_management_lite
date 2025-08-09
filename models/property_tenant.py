from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'
    tenant_id = fields.Many2one('property.tenant', string='Tenant', help="Link to the tenant record if this partner is a tenant.")

class PropertyTenant(models.Model):
    _name = 'property.tenant'
    _description = 'Property Tenant'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # Basic Information
    name = fields.Char('Full Name', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', 'Related Contact', ondelete='cascade')
    mobile = fields.Char('Mobile Number', related="partner_id.mobile", store=True, readonly=False, required=True, tracking=True)
    phone = fields.Char('Phone Number', related="partner_id.phone", store=True, readonly=False, required=True, tracking=True)
    email = fields.Char('Email', related="partner_id.email", store=True, readonly=False, required=True, tracking=True)
    nationality = fields.Many2one('res.country', 'Nationality', related="partner_id.country_id", store=True, readonly=False)

    # Identification
    id_passport = fields.Char('ID/Passport Number', required=True, tracking=True)
    id_type = fields.Selection([
        ('emirates_id', 'Emirates ID'),
        ('passport', 'Passport'),
        ('visa', 'Visa'),
        ('other', 'Other'),
    ], string='ID Type', required=True, default='emirates_id')
    
    # Additional Contact Information
    emergency_contact_name = fields.Char('Emergency Contact Name')
    emergency_contact_phone = fields.Char('Emergency Contact Phone')
    emergency_contact_relation = fields.Char('Relation')
    
    # Professional Information
    company_name = fields.Char('Company Name')
    job_title = fields.Char('Job Title')
    work_phone = fields.Char('Work Phone')
    monthly_income = fields.Monetary('Monthly Income', currency_field='currency_id')
    
    # Preferences
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('online', 'Online Payment'),
    ], string='Preferred Payment Method', default='cash')
    
    preferred_language = fields.Selection([
        ('en', 'English'),
        ('ar', 'Arabic'),
        ('ur', 'Urdu'),
        ('hi', 'Hindi'),
        ('fr', 'French'),
        ('other', 'Other'),
    ], string='Preferred Language', default='en')
    
    # Status
    status = fields.Selection([
        ('prospect', 'Prospect'),
        ('active', 'Active Tenant'),
        ('inactive', 'Inactive'),
        ('blacklisted', 'Blacklisted'),
    ], string='Status', default='prospect', tracking=True)
    
    # Relations
    partner_id = fields.Many2one('res.partner', 'Contact', ondelete='cascade')
    current_room_id = fields.Many2one('property.room', 'Current Room')
    agreement_ids = fields.One2many('property.agreement', 'tenant_id', 'Agreements')
    collection_ids = fields.One2many('property.collection', 'tenant_id', 'Collections')
    
    # Documents
    document_ids = fields.One2many('ir.attachment', 'res_id', 'Documents',
                                   domain=[('res_model', '=', 'property.tenant')])
    
    # Computed Fields
    active_agreements_count = fields.Integer('Active Agreements', compute='_compute_agreement_stats')
    total_agreements_count = fields.Integer('Total Agreements', compute='_compute_agreement_stats')
    total_paid = fields.Monetary('Total Paid', compute='_compute_payment_stats', currency_field='currency_id')
    last_payment_date = fields.Date('Last Payment', compute='_compute_payment_stats')
    
    # Financial
    currency_id = fields.Many2one('res.currency', 'Currency', 
                                  default=lambda self: self.env.company.currency_id)
    
    # Additional Fields
    notes = fields.Text('Notes')
    date_joined = fields.Date('Date Joined', default=fields.Date.today)
    
    # Image
    image = fields.Image('Photo', max_width=1920, max_height=1920)
    
    @api.depends('agreement_ids.state')
    def _compute_agreement_stats(self):
        for record in self:
            record.total_agreements_count = len(record.agreement_ids)
            record.active_agreements_count = len(record.agreement_ids.filtered(lambda a: a.state == 'active'))
    
    @api.depends('collection_ids.amount_collected')
    def _compute_payment_stats(self):
        for record in self:
            record.total_paid = sum(record.collection_ids.mapped('amount_collected'))
            record.last_payment_date = max(record.collection_ids.mapped('date')) if record.collection_ids else False

    def write(self, vals):
        # Update corresponding res.partner
        if self.partner_id:
            partner_vals = {}
            if 'name' in vals:
                partner_vals['name'] = vals['name']
            if 'mobile' in vals:
                partner_vals['mobile'] = vals['mobile']
            if 'email' in vals:
                partner_vals['email'] = vals['email']
            
            if partner_vals:
                self.partner_id.write(partner_vals)
        
        return super().write(vals)
    
    @api.constrains('id_passport')
    def _check_id_passport_unique(self):
        for record in self:
            if record.id_passport:
                existing = self.search([
                    ('id_passport', '=', record.id_passport),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(_('ID/Passport number must be unique!'))
    
    @api.constrains('mobile')
    def _check_mobile_unique(self):
        for record in self:
            if record.mobile:
                existing = self.search([
                    ('mobile', '=', record.mobile),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(_('Mobile number must be unique!'))
    
    def action_activate(self):
        self.write({'status': 'active'})
        
    def action_deactivate(self):
        self.write({'status': 'inactive'})
        
    def action_blacklist(self):
        self.write({'status': 'blacklisted'})
    
    def action_view_agreements(self):
        return {
            'name': _('Tenant Agreements'),
            'view_mode': 'list,form',
            'res_model': 'property.agreement',
            'type': 'ir.actions.act_window',
            'domain': [('tenant_id', '=', self.id)],
            'context': {'default_tenant_id': self.id}
        }
    
    # @api.model
    # def create(self, vals):
    #     # Create or link to partner
    #     if not vals.get('partner_id'):
    #         partner_vals = {
    #             'name': vals.get('name'),
    #             'phone': vals.get('mobile'),
    #             'email': vals.get('email'),
    #             'is_company': False,
    #             'customer_rank': 1,
    #         }
    #         partner = self.env['res.partner'].create(partner_vals)
    #         vals['partner_id'] = partner.id
        
    #     return super(PropertyTenant, self).create(vals)
    
    @api.model_create_multi
    def create(self, vals_list):
        # Create corresponding res.partner
        for vals in vals_list:
            if not vals.get('partner_id'):
                partner_vals = {
                    'name': vals.get('name'),
                    'mobile': vals.get('mobile'),
                    'email': vals.get('email'),
                    'is_company': False,
                    'customer_rank': 1,
                    'category_id': [(4, self.env.ref('property_management_lite.partner_category_tenant').id)],
            }
            partner = self.env['res.partner'].create(partner_vals)
            vals['partner_id'] = partner.id
        recs = super().create(vals_list)
        for rec in recs:
            if rec.partner_id:
                rec.partner_id.tenant_id = rec.id
        return recs
    
    def write(self, vals):
        # Sync changes to partner
        result = super(PropertyTenant, self).write(vals)
        
        for record in self:
            if record.partner_id:
                partner_vals = {}
                if 'name' in vals:
                    partner_vals['name'] = vals['name']
                if 'mobile' in vals:
                    partner_vals['phone'] = vals['mobile']
                if 'email' in vals:
                    partner_vals['email'] = vals['email']
                
                if partner_vals:
                    record.partner_id.write(partner_vals)
        
        return result

    def action_view_collections(self):
        return {
            'name': _('Tenant Collections'),
            'view_mode': 'list,form',
            'res_model': 'property.collection',
            'type': 'ir.actions.act_window',
            'domain': [('tenant_id', '=', self.id)],
            'context': {'default_tenant_id': self.id}
        }
    
    def action_create_agreement(self):
        return {
            'name': _('Create Agreement'),
            'view_mode': 'form',
            'res_model': 'property.agreement',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_tenant_id': self.id}
        }
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name} ({record.mobile})"
            result.append((record.id, name))
        return result
