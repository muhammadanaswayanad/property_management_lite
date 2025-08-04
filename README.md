# Property Management Lite - Odoo 18 Module

A comprehensive property and room rental management system designed specifically for Dubai properties, featuring daily rent collection, tenant management, and real-time financial analytics.

## 🏢 Overview

Property Management Lite is a full-featured Odoo 18 module that streamlines property rental operations with a focus on:

- **Property Hierarchy**: Properties → Flats → Rooms (3-level structure)
- **Tenant Management**: Complete tenant profiles with document management
- **Daily Operations**: Rent collection tracking and expense management
- **Financial Analytics**: Real-time profit analysis and reporting
- **Integration**: Leverages Odoo's built-in CRM, Accounting, and HR modules

## 🚀 Key Features

### Property Structure Management
- **Properties**: Multi-property portfolio management
- **Flats**: Floor-wise flat organization with detailed specifications
- **Rooms**: Individual room management with facilities tracking
- **Room Types**: Predefined room categories (Master, Partition, Sharing, Maid, Separate)

### Tenant Management
- **Complete Profiles**: Personal, professional, and emergency contact information
- **Document Storage**: ID/Passport, visa, and other document management
- **Agreement Tracking**: Rental agreements with terms and conditions
- **Exit Process**: Structured tenant exit with deposit settlement

### Daily Operations
- **Collection Tracking**: Daily rent collection with multiple payment methods
- **Due Management**: Automated due tracking with reminder system
- **Expense Management**: Property-wise expense tracking and approval workflow
- **Bank Reconciliation**: Bank transfer tracking and reconciliation

### Financial Management
- **Automated Invoicing**: Integration with Odoo's accounting module
- **Deposit Management**: Security deposit tracking and refund processing
- **Landlord Payments**: Automated landlord payment scheduling
- **Profit Analytics**: Real-time profit/loss calculation per property

### Dashboard & Analytics
- **Real-time Dashboard**: Live occupancy rates and collection status
- **Financial Reports**: Comprehensive financial analytics
- **Occupancy Reports**: Room utilization and vacancy analysis
- **Due Tracking**: Pending payments and follow-up management

## 📋 Installation

1. **Copy the module** to your Odoo addons directory:
   ```bash
   cp -r property_management_lite /path/to/odoo/addons/
   ```

2. **Update the module list** in Odoo:
   - Go to Apps → Update Apps List

3. **Install the module**:
   - Search for "Property Management Lite"
   - Click Install

4. **Configure permissions**:
   - Assign users to appropriate groups (User, Officer, Manager, Admin)

## 🏗️ Module Structure

```
property_management_lite/
├── __manifest__.py           # Module configuration
├── __init__.py              # Main module initialization
├── models/                  # Data models
│   ├── __init__.py
│   ├── property_property.py     # Properties
│   ├── property_flat.py         # Flats
│   ├── property_room.py         # Rooms
│   ├── property_tenant.py       # Tenants
│   ├── property_agreement.py    # Rental agreements
│   ├── property_collection.py   # Rent collections
│   ├── property_expense.py      # Expenses
│   ├── property_due_tracker.py  # Due tracking
│   └── res_partner.py           # Partner extensions
├── views/                   # User interface
│   ├── property_views.xml       # Property views
│   ├── tenant_views.xml         # Tenant management
│   ├── collection_views.xml     # Collections
│   ├── room_views.xml           # Room management
│   └── menu_views.xml           # Navigation menus
├── security/                # Access control
│   ├── property_security.xml    # Security groups
│   └── ir.model.access.csv      # Access permissions
├── data/                   # Default data
│   └── property_data.xml        # Room types, sequences
├── controllers/            # Web controllers
│   ├── main.py                  # Main controllers
│   └── portal.py                # Portal integration
├── static/                 # Assets
└── reports/               # Report templates
```

## 🔧 Configuration

### Initial Setup

1. **Create Room Types**:
   - Master Room (AED 2,500/month)
   - Partition Room (AED 1,800/month)
   - Sharing Room (AED 1,200/month)
   - Maid Room (AED 800/month)
   - Separate Room (AED 2,000/month)

2. **Set up Properties**:
   - Add your properties with complete address information
   - Configure flats within each property
   - Set up rooms with facilities and rent amounts

3. **Configure Users**:
   - **Property User**: Basic access for data entry
   - **Property Officer**: Collections and expense management
   - **Property Manager**: Full operational access
   - **Property Admin**: System configuration access

### Integration with Odoo Modules

- **Contacts**: Automatic customer/supplier creation for tenants/landlords
- **Accounting**: Automated invoice generation and payment tracking
- **Sales**: Integration with quotation system for new tenants
- **HR**: Staff management and commission tracking
- **Website/Portal**: Tenant self-service portal

## 💼 Business Workflow

### Tenant Onboarding
1. Create tenant profile with documents
2. Select available room
3. Create rental agreement
4. Activate agreement (room becomes occupied)
5. Generate first invoice

### Daily Operations
1. **Morning**: Check due payments for the day
2. **Collections**: Record payments received
3. **Expenses**: Log property expenses
4. **Evening**: Verify collections and update status

### Monthly Process
1. Generate monthly invoices
2. Process landlord payments
3. Calculate staff commissions
4. Generate financial reports

## 📊 Reporting Features

### Financial Reports
- Monthly profit/loss by property
- Collection efficiency reports
- Expense analysis by category
- Landlord payment tracking

### Operational Reports
- Room occupancy statistics
- Tenant turnover analysis
- Due payment tracking
- Maintenance request tracking

## 🔐 Security Features

- **Role-based Access**: Four-tier permission system
- **Data Protection**: Tenant document encryption
- **Audit Trail**: Complete activity logging
- **Record Rules**: Data isolation by user role

## 🌐 Website/Portal Integration

### Tenant Portal Features
- View current agreement details
- Payment history and receipts
- Document upload facility
- Maintenance request submission

### Public Website Features
- Available room listings
- Online inquiry forms
- Property showcase
- Contact information

## 📱 Mobile Optimization

- Responsive design for mobile collection teams
- Quick collection entry forms
- Offline-capable expense recording
- Real-time synchronization

## 🔮 Future Enhancements

### Phase 2 Features
- **SMS Integration**: Automated payment reminders
- **WhatsApp Business API**: Communication automation
- **Mobile App**: Dedicated mobile application
- **IoT Integration**: Smart meter readings

### Advanced Features
- **AI Analytics**: Predictive occupancy analysis
- **Automated Pricing**: Dynamic rent optimization
- **Multi-currency**: Support for multiple currencies
- **Multi-company**: Group-level property management

## 🆘 Support & Documentation

### User Guide
- Complete user manual available in the module
- Video tutorials for common operations
- Best practices guide

### Technical Support
- Module customization services
- Integration with external systems
- Performance optimization
- Custom report development

## 📄 License

This module is licensed under LGPL-3. See the LICENSE file for details.

## 🤝 Contributing

We welcome contributions! Please read our contributing guidelines and submit pull requests for any improvements.

---

**Developed with ❤️ for the Dubai property rental market**

For support, customization, or training, please contact your implementation partner.
