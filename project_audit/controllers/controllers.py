# -*- coding: utf-8 -*-
# from odoo import http


# class ProjectAudit(http.Controller):
#     @http.route('/project_audit/project_audit/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/project_audit/project_audit/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('project_audit.listing', {
#             'root': '/project_audit/project_audit',
#             'objects': http.request.env['project_audit.project_audit'].search([]),
#         })

#     @http.route('/project_audit/project_audit/objects
#     /<model("project_audit.project_audit"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('project_audit.object', {
#             'object': obj
#         })
