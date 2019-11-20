# -*- coding: utf-8 -*-
{
    'name': "Avicampo Tools",

    'summary': """
        Herramientas Avicampo""",

    'description': """
        Contabilidad
            -Pagos \n
            - Solicitudes de Transferencias
            - Cheques Manuales
    """,

    'author': "Marco Gonzalez",
    'website': "http://www.grupoalvamex.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','mrp',],

    # always loaded
    'data': [
        'security/produccion_costeo_security.xml',
        'security/ir.model.access.csv',
        'data/contabilidad.data.xml',
        'views/contabilidad_pagos_manuales_views.xml',
        'views/contabilidad_pagos_manuales_templates.xml',
        'views/produccion_costeo_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': ['demo/demo.xml'],    
    'installable': True,
}