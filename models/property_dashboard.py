# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class PropertyDashboard(models.TransientModel):
    _name = 'property.dashboard'
    _description = 'Property Management Dashboard'
    _rec_name = 'display_name'

    display_name = fields.Char(string='Name', default='Property Management Dashboard', readonly=True)

    def name_get(self):
        """Return proper display name"""
        result = []
        for record in self:
            result.append((record.id, 'Property Management Dashboard'))
        return result

    @api.model
    def default_get(self, fields_list):
        """Override to ensure fresh data is always computed"""
        res = super().default_get(fields_list)
        
        # Compute fresh values directly in the result
        today = fields.Date.today()
        
        # Today's collections
        collections = self.env['property.collection'].search([
            ('date', '=', today),
            ('status', '!=', 'cancelled')
        ])
        res['today_collections'] = sum(collections.mapped('amount_collected'))
        res['today_collections_count'] = len(collections)
        
        # Today's expenses
        expenses = self.env['account.move'].search([
            ('move_type','in', ('in_invoice','in_refund')),
            ('invoice_date', '=', today),
            ('state', 'in', ['posted'])
        ])
        res['today_expenses'] = sum(expenses.mapped('amount_total'))
        res['today_expenses_count'] = len(expenses)
        res['today_profit'] = res['today_collections'] - res['today_expenses']
        
        # Today's new tenants
        tenants = self.env['property.tenant'].search([
            ('create_date', '>=', fields.Datetime.to_string(datetime.combine(today, datetime.min.time()))),
            ('create_date', '<', fields.Datetime.to_string(datetime.combine(today + timedelta(days=1), datetime.min.time())))
        ])
        res['today_new_tenants'] = len(tenants)
        
        # Vacant rooms today
        vacant_rooms = self.env['property.room'].search([('status', '=', 'vacant')])
        res['today_vacant_rooms'] = len(vacant_rooms)
        
        # Week stats
        week_start = today - timedelta(days=today.weekday())
        week_collections = self.env['property.collection'].search([
            ('date', '>=', week_start),
            ('date', '<=', today),
            ('status', '!=', 'cancelled')
        ])
        res['week_collections'] = sum(week_collections.mapped('amount_collected'))
        res['week_collections_count'] = len(week_collections)
        
        # Week expenses
        week_expenses = self.env['account.move'].search([
            ('move_type','in', ('in_invoice','in_refund')),
            ('invoice_date', '>=', week_start),
            ('invoice_date', '<=', today),
            ('state', 'in', ['posted'])
        ])
        res['week_expenses'] = sum(week_expenses.mapped('amount_total'))
        res['week_expenses_count'] = len(week_expenses)
        res['week_profit'] = res['week_collections'] - res['week_expenses']
        
        week_start_datetime = fields.Datetime.to_string(datetime.combine(week_start, datetime.min.time()))
        today_end_datetime = fields.Datetime.to_string(datetime.combine(today + timedelta(days=1), datetime.min.time()))
        week_tenants = self.env['property.tenant'].search([
            ('create_date', '>=', week_start_datetime),
            ('create_date', '<', today_end_datetime)
        ])
        res['week_new_tenants'] = len(week_tenants)
        
        # Month stats
        month_start = today.replace(day=1)
        month_collections = self.env['property.collection'].search([
            ('date', '>=', month_start),
            ('date', '<=', today),
            ('status', '!=', 'cancelled')
        ])
        res['month_collections'] = sum(month_collections.mapped('amount_collected'))
        res['month_collections_count'] = len(month_collections)
        
        # Month expenses
        month_expenses = self.env['account.move'].search([
            ('move_type','in', ('in_invoice','in_refund')),
            ('invoice_date', '>=', month_start),
            ('invoice_date', '<=', today),
            ('state', 'in', ['posted'])
        ])
        res['month_expenses'] = sum(month_expenses.mapped('amount_total'))
        res['month_expenses_count'] = len(month_expenses)
        res['month_profit'] = res['month_collections'] - res['month_expenses']
        
        month_start_datetime = fields.Datetime.to_string(datetime.combine(month_start, datetime.min.time()))
        today_end_datetime = fields.Datetime.to_string(datetime.combine(today + timedelta(days=1), datetime.min.time()))
        month_tenants = self.env['property.tenant'].search([
            ('create_date', '>=', month_start_datetime),
            ('create_date', '<', today_end_datetime)
        ])
        res['month_new_tenants'] = len(month_tenants)
        
        # Overall stats
        res['total_properties'] = self.env['property.property'].search_count([])
        
        all_rooms = self.env['property.room'].search([])
        res['total_rooms'] = len(all_rooms)
        
        occupied_rooms = all_rooms.filtered(lambda r: r.status == 'occupied')
        res['occupied_rooms'] = len(occupied_rooms)
        res['vacant_rooms'] = res['total_rooms'] - res['occupied_rooms']
        
        # Calculate occupancy rate as a decimal (0.0 to 1.0)
        # The percentage widget in the view will multiply by 100 for display
        if res['total_rooms'] > 0:
            res['occupancy_rate'] = res['occupied_rooms'] / res['total_rooms']
        else:
            res['occupancy_rate'] = 0.0
        
        res['total_tenants'] = self.env['property.tenant'].search_count([('status', '=', 'active')])
        
        # Recent activities
        recent_collections = self.env['property.collection'].search([
            ('status', '!=', 'cancelled')
        ], order='date desc', limit=5)
        
        collections_text = ""
        for collection in recent_collections:
            collections_text += f"• {collection.date} - {collection.tenant_id.name} - {collection.amount_collected} AED\n"
        res['recent_collections'] = collections_text or "No recent collections"
        
        recent_tenants = self.env['property.tenant'].search([], order='create_date desc', limit=5)
        tenants_text = ""
        for tenant in recent_tenants:
            tenants_text += f"• {tenant.name} - {tenant.mobile} - {tenant.status}\n"
        res['recent_tenants'] = tenants_text or "No recent tenants"
        
        return res

    # Today's Stats
    today_collections = fields.Float('Today Collections')
    today_collections_count = fields.Integer('Today Collections Count')
    today_expenses = fields.Float('Today Expenses')
    today_expenses_count = fields.Integer('Today Expenses Count')
    today_profit = fields.Float('Today Profit')
    today_new_tenants = fields.Integer('Today New Tenants')
    today_vacant_rooms = fields.Integer('Vacant Rooms Today')

    # Weekly Stats
    week_collections = fields.Float('This Week Collections')
    week_collections_count = fields.Integer('This Week Collections Count')
    week_expenses = fields.Float('This Week Expenses')
    week_expenses_count = fields.Integer('This Week Expenses Count')
    week_profit = fields.Float('This Week Profit')
    week_new_tenants = fields.Integer('This Week New Tenants')

    # Monthly Stats
    month_collections = fields.Float('This Month Collections')
    month_collections_count = fields.Integer('This Month Collections Count')
    month_new_tenants = fields.Integer('This Month New Tenants')
    month_expenses = fields.Float('This Month Expenses')
    month_expenses_count = fields.Integer('This Month Expenses Count')
    month_profit = fields.Float('This Month Profit')

    # Overall Stats
    total_properties = fields.Integer('Total Properties')
    total_rooms = fields.Integer('Total Rooms')
    occupied_rooms = fields.Integer('Occupied Rooms')
    vacant_rooms = fields.Integer('Vacant Rooms')
    occupancy_rate = fields.Float('Occupancy Rate (%)')
    total_tenants = fields.Integer('Total Active Tenants')

    # Recent Activities
    recent_collections = fields.Text('Recent Collections')
    recent_tenants = fields.Text('Recent Tenants')

    def action_open_collections(self):
        return {
            'name': 'Collections',
            'type': 'ir.actions.act_window',
            'res_model': 'property.collection',
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_open_properties(self):
        return {
            'name': 'Properties',
            'type': 'ir.actions.act_window',
            'res_model': 'property.property',
            'view_mode': 'kanban,list,form',
            'target': 'current',
        }

    def action_open_tenants(self):
        return {
            'name': 'Tenants',
            'type': 'ir.actions.act_window',
            'res_model': 'property.tenant',
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_open_rooms(self):
        return {
            'name': 'Rooms',
            'type': 'ir.actions.act_window',
            'res_model': 'property.room',
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_open_vacant_rooms(self):
        return {
            'name': 'Vacant Rooms',
            'type': 'ir.actions.act_window',
            'res_model': 'property.room',
            'view_mode': 'list,form',
            'domain': [('status', '=', 'vacant')],
            'target': 'current',
        }
