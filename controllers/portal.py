from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class PropertyPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        
        if 'agreement_count' in counters:
            if partner.tenant_id:
                agreement_count = request.env['property.agreement'].search_count([
                    ('tenant_id', '=', partner.tenant_id.id)
                ])
            else:
                agreement_count = 0
            values['agreement_count'] = agreement_count
            
        if 'collection_count' in counters:
            if partner.tenant_id:
                collection_count = request.env['property.collection'].search_count([
                    ('tenant_id', '=', partner.tenant_id.id)
                ])
            else:
                collection_count = 0
            values['collection_count'] = collection_count
            
        return values

    @http.route(['/my/agreements', '/my/agreements/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_agreements(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        if not partner.tenant_id:
            return request.render('property_management_lite.portal_no_tenant')
            
        Agreement = request.env['property.agreement']
        
        domain = [('tenant_id', '=', partner.tenant_id.id)]
        
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'start_date desc'},
            'name': {'label': _('Name'), 'order': 'name'},
        }
        
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        # Count for pager
        agreement_count = Agreement.search_count(domain)
        
        # Pager
        pager = request.website.pager(
            url="/my/agreements",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=agreement_count,
            page=page,
            step=self._items_per_page
        )
        
        # Content
        agreements = Agreement.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'date': date_begin,
            'date_end': date_end,
            'agreements': agreements,
            'page_name': 'agreement',
            'archive_groups': [],
            'default_url': '/my/agreements',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby
        })
        
        return request.render("property_management_lite.portal_my_agreements", values)

    @http.route(['/my/agreement/<int:agreement_id>'], type='http', auth="user", website=True)
    def portal_agreement_detail(self, agreement_id, **kw):
        agreement = request.env['property.agreement'].browse(agreement_id)
        
        # Check access rights
        if not agreement.exists() or agreement.tenant_id != request.env.user.partner_id.tenant_id:
            return request.not_found()
            
        values = {
            'agreement': agreement,
            'page_name': 'agreement_detail',
        }
        
        return request.render("property_management_lite.portal_agreement_detail", values)

    @http.route(['/my/collections', '/my/collections/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_collections(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        if not partner.tenant_id:
            return request.render('property_management_lite.portal_no_tenant')
            
        Collection = request.env['property.collection']
        
        domain = [('tenant_id', '=', partner.tenant_id.id)]
        
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'date desc'},
            'amount': {'label': _('Amount'), 'order': 'amount_collected desc'},
        }
        
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        # Count for pager
        collection_count = Collection.search_count(domain)
        
        # Pager
        pager = request.website.pager(
            url="/my/collections",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=collection_count,
            page=page,
            step=self._items_per_page
        )
        
        # Content
        collections = Collection.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'date': date_begin,
            'date_end': date_end,
            'collections': collections,
            'page_name': 'collection',
            'archive_groups': [],
            'default_url': '/my/collections',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby
        })
        
        return request.render("property_management_lite.portal_my_collections", values)
