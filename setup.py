# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

version = "1.0.2"

setup(
    name="bika.coa",
    version=version,
    description="Custom COAs for SENAITE LIMS",
    long_description='',
    classifiers=[
        "Framework :: Plone",
        "Framework :: Zope2",
        "Programming Language :: Python",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords="",
    author="BikaLabs",
    author_email="info@bikalabs.com",
    url="https://github.com/bika/bika.coa",
    license="GPLv2",
    packages=find_packages("src", exclude=["ez_setup"]),
    package_dir={"": "src"},
    namespace_packages=["bika"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "setuptools",
        "senaite.impress",
        'archetypes.schemaextender',
    ],
    extras_require={
        "test": [
            "Products.PloneTestCase",
            "plone.app.testing",
            "robotsuite",
            "unittest2",
        ]
    },
    entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
)
