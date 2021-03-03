# -*- coding: utf-8 -*-
{
    'name': "Rio Lerma Tools",

    'summary': """
        Herramientas Rio Lerma""",

    'description': """
        Contabilidad
            -Asientos Contables \n
            - Vehiculo
    """,

    'author': "Marco Gonzalez",
    'website': "http://www.grupoalvamex.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tools',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        'views/contabilidad_asientos_contables.xml',
    ],
    # only loaded in demonstration mode
    'demo': ['demo/demo.xml'],    
    'installable': True,
}