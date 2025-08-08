# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class PropertyDashboard(models.TransientModel):
    _name = 'property.dashboard'
    _description = 'Property Management Dashboard'

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
        
        month_start_datetime = fields.Datetime.to_string(datetime.combine(month_start, datetime.min.time()))
        month_tenants = self.env['property.tenant'].search([
            ('create_date', '>=', month_start_datetime),
            ('create_date', '<', today_end_datetime)
        ])
        res['month_new_tenants'] = len(month_tenants)
        
        expenses = self.env['property.expense'].search([
            ('date', '>=', month_start),
            ('date', '<=', today),
            ('state', '=', 'paid')
        ])
        res['month_expenses'] = sum(expenses.mapped('amount'))
        
        # Overall stats
        res['total_properties'] = self.env['property.property'].search_count([])
        
        all_rooms = self.env['property.room'].search([])
        res['total_rooms'] = len(all_rooms)
        
        occupied_rooms = all_rooms.filtered(lambda r: r.status == 'occupied')
        res['occupied_rooms'] = len(occupied_rooms)
        res['vacant_rooms'] = res['total_rooms'] - res['occupied_rooms']
        
        if res['total_rooms'] > 0:
            res['occupancy_rate'] = (res['occupied_rooms'] / res['total_rooms']) * 100
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
    today_collections = fields.Float('Today Collections', compute='_compute_today_stats')
    today_collections_count = fields.Integer('Today Collections Count', compute='_compute_today_stats')
    today_new_tenants = fields.Integer('Today New Tenants', compute='_compute_today_stats')
    today_vacant_rooms = fields.Integer('Vacant Rooms Today', compute='_compute_today_stats')

    # Weekly Stats
    week_collections = fields.Float('This Week Collections', compute='_compute_week_stats')
    week_collections_count = fields.Integer('This Week Collections Count', compute='_compute_week_stats')
    week_new_tenants = fields.Integer('This Week New Tenants', compute='_compute_week_stats')

    # Monthly Stats
    month_collections = fields.Float('This Month Collections', compute='_compute_month_stats')
    month_collections_count = fields.Integer('This Month Collections Count', compute='_compute_month_stats')
    month_new_tenants = fields.Integer('This Month New Tenants', compute='_compute_month_stats')
    month_expenses = fields.Float('This Month Expenses', compute='_compute_month_stats')

    # Overall Stats
    total_properties = fields.Integer('Total Properties', compute='_compute_overall_stats')
    total_rooms = fields.Integer('Total Rooms', compute='_compute_overall_stats')
    occupied_rooms = fields.Integer('Occupied Rooms', compute='_compute_overall_stats')
    vacant_rooms = fields.Integer('Vacant Rooms', compute='_compute_overall_stats')
    occupancy_rate = fields.Float('Occupancy Rate (%)', compute='_compute_overall_stats')
    total_tenants = fields.Integer('Total Active Tenants', compute='_compute_overall_stats')

    # Recent Activities
    recent_collections = fields.Text('Recent Collections', compute='_compute_recent_activities')
    recent_tenants = fields.Text('Recent Tenants', compute='_compute_recent_activities')

    @api.model
    def _compute_today_stats(self):
        for rec in self:
            today = fields.Date.today()
            
            # Today's collections
            collections = self.env['property.collection'].search([
                ('date', '=', today),
                ('status', '!=', 'cancelled')
            ])
            rec.today_collections = sum(collections.mapped('amount_collected'))
            rec.today_collections_count = len(collections)
            
            # Today's new tenants
            tenants = self.env['property.tenant'].search([
                ('create_date', '>=', fields.Datetime.to_string(datetime.combine(today, datetime.min.time()))),
                ('create_date', '<', fields.Datetime.to_string(datetime.combine(today + timedelta(days=1), datetime.min.time())))
            ])
            rec.today_new_tenants = len(tenants)
            
            # Vacant rooms today
            vacant_rooms = self.env['property.room'].search([('status', '=', 'vacant')])
            rec.today_vacant_rooms = len(vacant_rooms)

    @api.model
    def _compute_week_stats(self):
        for rec in self:
            today = fields.Date.today()
            week_start = today - timedelta(days=today.weekday())
            
            # This week's collections
            collections = self.env['property.collection'].search([
                ('date', '>=', week_start),
                ('date', '<=', today),
                ('status', '!=', 'cancelled')
            ])
            rec.week_collections = sum(collections.mapped('amount_collected'))
            rec.week_collections_count = len(collections)
            
            # This week's new tenants
            week_start_datetime = fields.Datetime.to_string(datetime.combine(week_start, datetime.min.time()))
            today_end_datetime = fields.Datetime.to_string(datetime.combine(today + timedelta(days=1), datetime.min.time()))
            
            tenants = self.env['property.tenant'].search([
                ('create_date', '>=', week_start_datetime),
                ('create_date', '<', today_end_datetime)
            ])
            rec.week_new_tenants = len(tenants)

    @api.model
    def _compute_month_stats(self):
        for rec in self:
            today = fields.Date.today()
            month_start = today.replace(day=1)
            
            # This month's collections
            collections = self.env['property.collection'].search([
                ('date', '>=', month_start),
                ('date', '<=', today),
                ('status', '!=', 'cancelled')
            ])
            rec.month_collections = sum(collections.mapped('amount_collected'))
            rec.month_collections_count = len(collections)
            
            # This month's new tenants
            month_start_datetime = fields.Datetime.to_string(datetime.combine(month_start, datetime.min.time()))
            today_end_datetime = fields.Datetime.to_string(datetime.combine(today + timedelta(days=1), datetime.min.time()))
            
            tenants = self.env['property.tenant'].search([
                ('create_date', '>=', month_start_datetime),
                ('create_date', '<', today_end_datetime)
            ])
            rec.month_new_tenants = len(tenants)
            
            # This month's expenses
            expenses = self.env['property.expense'].search([
                ('date', '>=', month_start),
                ('date', '<=', today),
                ('state', '=', 'paid')
            ])
            rec.month_expenses = sum(expenses.mapped('amount'))

    @api.model
    def _compute_overall_stats(self):
        for rec in self:
            # Total properties
            rec.total_properties = self.env['property.property'].search_count([])
            
            # Room statistics
            all_rooms = self.env['property.room'].search([])
            rec.total_rooms = len(all_rooms)
            
            occupied_rooms = all_rooms.filtered(lambda r: r.status == 'occupied')
            rec.occupied_rooms = len(occupied_rooms)
            
            rec.vacant_rooms = rec.total_rooms - rec.occupied_rooms
            
            if rec.total_rooms > 0:
                rec.occupancy_rate = (rec.occupied_rooms / rec.total_rooms) * 100
            else:
                rec.occupancy_rate = 0.0
            
            # Active tenants
            rec.total_tenants = self.env['property.tenant'].search_count([('status', '=', 'active')])

    @api.model
    def _compute_recent_activities(self):
        for rec in self:
            # Recent collections (last 5)
            recent_collections = self.env['property.collection'].search([
                ('status', '!=', 'cancelled')
            ], order='date desc', limit=5)
            
            collections_text = ""
            for collection in recent_collections:
                collections_text += f"• {collection.date} - {collection.tenant_id.name} - {collection.amount_collected} AED\n"
            rec.recent_collections = collections_text or "No recent collections"
            
            # Recent tenants (last 5)
            recent_tenants = self.env['property.tenant'].search([], order='create_date desc', limit=5)
            
            tenants_text = ""
            for tenant in recent_tenants:
                tenants_text += f"• {tenant.name} - {tenant.mobile} - {tenant.status}\n"
            rec.recent_tenants = tenants_text or "No recent tenants"

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
