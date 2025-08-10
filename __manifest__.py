{
    'name': 'Property Management Lite',
    'version': '18.0.1.0.0',
    'category': 'Real Estate',
    'summary': 'Complete Room Rental Management System with daily rent collection and tenant management',
    'description': """
Property Management Lite - Community Edition
============================================

A comprehensive property and room rental management system designed for Dubai properties 
with features for:

* Property → Flat → Room hierarchy management
* Tenant management with document storage
* Daily rent collection tracking
* Expense management and profit analysis
* Real-time dashboard and analytics

    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'contacts',
        'mail',
        'web',
        'sale',
        'account',
    ],
    'data': [
        # Security
        'security/property_security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/property_data.xml',
        'data/sequences.xml',
        'data/product.xml',
        # Views - Dashboard
        'views/dashboard_views.xml',
        
        # Views - Base Structure
        'views/property_views.xml',
        'views/flat_views.xml',
        'views/room_views.xml',
        
        # Views - Tenant Management
        'views/tenant_views.xml',
        'views/agreement_views.xml',
        
        # Views - Daily Operations
        'views/collection_views.xml',
        # 'views/expense_views.xml',
        'views/invoice_views.xml',
        
        # Reports (must come before email templates that reference them)
        'reports/invoice_reports.xml',
        
        # Email Templates (must come after reports)
        'data/email_templates.xml',
        
        # Menus
        'views/menu_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 10,
}
