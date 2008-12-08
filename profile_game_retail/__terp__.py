# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name":"Bussiness Game",
    "version":"1.0",
    "author":"Tiny",
    "category":"Profile",
    "depends":[
        "board",
        "base",
        "game_scenario",
        "purchase_approve",
        "sale",
        "sale_wo_production",
        "stock_planning",
        "crm_configuration",
        "mrp_jit",
        "account_budget",
        "sale_forecast"
    ],
    "init_xml":[
        "profile_game_data.xml",
        "profile_game_scenario.xml",
    ],
    "demo_xml":[],
    "update_xml":[
        "profile_game_view.xml",
        "wizard_game_phase2.xml",
        "profile_game_account_data.xml",
        "profile_game_partner.xml",
        "profile_game_phase1.xml",
        "profile_game_config.xml",
        "profile_game_product.xml",
        "security/ir.model.access.csv"
    ],
    "active":False,
    "installable":True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: