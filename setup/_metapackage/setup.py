import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-open-synergy-ssi-customer-invoice-export",
    description="Meta package for open-synergy-ssi-customer-invoice-export Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-ssi_customer_invoice_export',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
