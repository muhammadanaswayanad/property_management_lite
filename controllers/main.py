from odoo import http
from odoo.http import request


class PropertyManagementController(http.Controller):

    @http.route('/property/dashboard', type='http', auth='user', website=True)
    def property_dashboard(self, **kwargs):
        """Property management dashboard"""
        # Get summary statistics
        properties = request.env['property.property'].search([])
        total_properties = len(properties)
        total_rooms = sum(properties.mapped('total_rooms'))
        occupied_rooms = sum(properties.mapped('occupied_rooms'))
        
        collections_today = request.env['property.collection'].search([
            ('date', '=', http.request.env.context.get('today', ''))
        ])
        
        values = {
            'total_properties': total_properties,
            'total_rooms': total_rooms,
            'occupied_rooms': occupied_rooms,
            'occupancy_rate': (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0,
            'collections_today': collections_today,
            'today_collection_amount': sum(collections_today.mapped('amount_collected')),
        }
        
        return request.render('property_management_lite.dashboard_template', values)

    @http.route('/property/api/collections', type='json', auth='user')
    def api_collections(self, **kwargs):
        """API endpoint for collections data"""
        collections = request.env['property.collection'].search([])
        data = []
        for collection in collections:
            data.append({
                'id': collection.id,
                'date': collection.date.strftime('%Y-%m-%d'),
                'tenant': collection.tenant_id.name,
                'room': collection.room_id.name,
                'amount': collection.amount_collected,
                'status': collection.status,
            })
        return data

    @http.route('/property/api/rooms/available', type='json', auth='user')
    def api_available_rooms(self, **kwargs):
        """API endpoint for available rooms"""
        rooms = request.env['property.room'].search([('status', 'in', ['vacant', 'booked'])])
        data = []
        for room in rooms:
            data.append({
                'id': room.id,
                'name': room.name,
                'property': room.property_id.name,
                'rent': room.rent_amount,
                'status': room.status,
            })
        return data
