from odoo import models, fields, api, _


class PropertyStaffSalary(models.Model):
    _name = 'property.staff.salary'
    _description = 'Staff Salary & Commission'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Reference', required=True)
    
    employee_id = fields.Many2one('res.users', 'Employee', required=True)
    property_id = fields.Many2one('property.property', 'Property')
    
    period_from = fields.Date('Period From', required=True)
    period_to = fields.Date('Period To', required=True)
    
    basic_salary = fields.Monetary('Basic Salary', currency_field='currency_id')
    commission = fields.Monetary('Commission', currency_field='currency_id')
    bonus = fields.Monetary('Bonus', currency_field='currency_id')
    total_amount = fields.Monetary('Total Amount', compute='_compute_total', store=True, currency_field='currency_id')
    
    status = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
    ], default='draft', tracking=True)
    
    currency_id = fields.Many2one('res.currency', 'Currency', 
                                  default=lambda self: self.env.company.currency_id)
    
    @api.depends('basic_salary', 'commission', 'bonus')
    def _compute_total(self):
        for record in self:
            record.total_amount = record.basic_salary + record.commission + record.bonus
