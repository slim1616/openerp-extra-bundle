# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2004-2007 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: account.py 1005 2005-07-25 08:41:42Z nicoe $
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import fields,osv
from service import security
import pooler

try:
    import ldap
except ImportError:
    import netsvc
    logger = netsvc.Logger()
    logger.notifyChannel("init", netsvc.LOG_WARNING, "could not import ldap!")


class CompanyLDAP(osv.osv):
    _name = 'res.company.ldap'
    _order = 'sequence'
    _rec_name = 'ldap_server'
    _columns = {
        'sequence': fields.integer('Sequence'),
        'company': fields.many2one('res.company', 'Company', required=True,
            ondelete='cascade'),
        'ldap_server': fields.char('LDAP Server address', size=64, required=True),
        'ldap_binddn': fields.char('LDAP binddn', size=64, required=True),
        'ldap_password': fields.char('LDAP password', size=64, required=True),
        'ldap_filter': fields.char('LDAP filter', size=64, required=True),
        'ldap_base': fields.char('LDAP base', size=64, required=True),
        'user': fields.many2one('res.users', 'Model user',
            help="Model used for user creation"),
        'create_user': fields.boolean('Create user',
            help="Create the user if not in database"),
    }
    _defaults = {
        'sequence': lambda *a: 10,
        'create_user': lambda *a: True,
    }

CompanyLDAP()


class res_company(osv.osv):
    _inherit = "res.company"

    _columns = {
        'ldaps': fields.one2many('res.company.ldap', 'company', 'LDAP Parameters'),
    }
res_company()

def ldap_login(oldfnc):
    def _ldap_login(db, login, passwd):
        cr = pooler.get_db(db).cursor()
        module_obj = pooler.get_pool(cr.dbname).get('ir.module.module')
        module_ids = module_obj.search(cr, 1, [('name', '=', 'users_ldap')])
        if module_ids:
            state = module_obj.read(cr, 1, module_ids, ['state'])[0]['state']
            if state in ('installed', 'to upgrade', 'to remove'):
                cr.execute("select id, company, ldap_server, ldap_binddn, ldap_password, ldap_filter, ldap_base, \"user\", create_user from res_company_ldap where ldap_server != '' and ldap_binddn != '' order by sequence")
                for res_company_ldap in cr.dictfetchall():
                    try:
                        l = ldap.open(res_company_ldap['ldap_server'])
                        if l.simple_bind_s(res_company_ldap['ldap_binddn'], res_company_ldap['ldap_password']):
                            base = res_company_ldap['ldap_base']
                            scope = ldap.SCOPE_SUBTREE
                            filter = res_company_ldap['ldap_filter']%(login,)
                            retrieve_attributes = None
                            result_id = l.search(base, scope, filter, retrieve_attributes)
                            timeout = 60
                            result_type, result_data = l.result(result_id, timeout)
                            if not result_data:
                                continue
                            if result_type == ldap.RES_SEARCH_RESULT and len(result_data) == 1:
                                dn=result_data[0][0]
                                name=result_data[0][1]['cn'][0]
                                if l.bind_s(dn, passwd):
                                    l.unbind()
                                    cr.execute("select id from res_users where login=%s",(login.encode('utf-8'),))
                                    res = cr.fetchone()
                                    if res:
                                        cr.close()
                                        return res[0]
                                    if not res_company_ldap['create_user']:
                                        continue
                                    users_obj = pooler.get_pool(cr.dbname).get('res.users')
                                    action_obj = pooler.get_pool(cr.dbname).get('ir.actions.actions')
                                    action_id = action_obj.search(cr, 1, [('usage', '=', 'menu')])[0]
                                    if res_company_ldap['user']:
                                        res = users_obj.copy(cr, 1, res_company_ldap['user'],
                                                default={'active': True})
                                        users_obj.write(cr, 1, res, {
                                            'name': name,
                                            'login': login.encode('utf-8'),
                                            'company_id': res_company_ldap['company'],
                                            })
                                    else:
                                        res = users_obj.create(cr, 1, {
                                            'name': name,
                                            'login': login.encode('utf-8'),
                                            'company_id': res_company_ldap['company'],
                                            'action_id': action_id,
                                            'menu_id': action_id,
                                            })
                                    cr.commit()
                                    cr.close()
                                    return res
                            l.unbind()
                    except Exception, e:
                        continue
        cr.close()
        return oldfnc(db, login, passwd)
    return _ldap_login

security.login = ldap_login(security.login)

def ldap_check(oldfnc):
    def _ldap_check(db, uid, passwd):
        if security._uid_cache.has_key(uid) and (security._uid_cache[uid]==passwd):
            return True
        cr = pooler.get_db(db).cursor()
        module_obj = pooler.get_pool(cr.dbname).get('ir.module.module')
        module_ids = module_obj.search(cr, 1, [('name', '=', 'users_ldap')])
        if module_ids:
            state = module_obj.read(cr, 1, module_ids, ['state'])[0]['state']
            if state in ('installed', 'to upgrade', 'to remove'):
                users_obj = pooler.get_pool(cr.dbname).get('res.users')
                user = users_obj.browse(cr, 1, uid)
                if user and user.company_id.ldaps:
                    for res_company_ldap in user.company_id.ldaps:
                        try:
                            l = ldap.open(res_company_ldap.ldap_server)
                            if l.simple_bind_s(res_company_ldap.ldap_binddn,
                                    res_company_ldap.ldap_password):
                                base = res_company_ldap.ldap_base
                                scope = ldap.SCOPE_SUBTREE
                                filter = res_company_ldap.ldap_filter % (user.login,)
                                retrieve_attributes = None
                                result_id = l.search(base, scope, filter, retrieve_attributes)
                                timeout = 60
                                result_type, result_data = l.result(result_id, timeout)
                                if result_data and result_type == ldap.RES_SEARCH_RESULT and len(result_data) == 1:
                                    dn=result_data[0][0]
                                    name=result_data[0][1]['cn']
                                    if l.bind_s(dn, passwd):
                                        l.unbind()
                                        security._uid_cache[uid] = passwd
                                        cr.close()
                                        return True
                                l.unbind()
                        except Exception, e:
                            pass
        cr.close()
        return oldfnc(db, uid, passwd)
    return _ldap_check

security.check = ldap_check(security.check)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

