# -*- coding: utf-8 -*-

from operator import attrgetter
from plone.resource.utils import iterDirectoriesOfType
from senaite.impress.template import TemplateFinder as TF


class TemplateFinder(TF):

    @property
    def resources(self):
        out = []
        directories = iterDirectoriesOfType(self.type)
        sorted_directories = sorted(directories, key=attrgetter('__name__'))
        for resource in sorted_directories:
            out.append({
                "name": resource.__name__,
                "path": resource.directory,
                "contents": resource.listDirectory(),
            })
        return out
