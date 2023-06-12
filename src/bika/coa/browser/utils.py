# -*- coding: utf-8 -*-

import os
from senaite.impress.template import TemplateFinder as TF


class TemplateFinder(TF):

    def get_templates(self, extensions=[".pt", ".html"]):
        templates = []
        for resource in self.resources:
            name = resource["name"]
            path = resource["path"]
            contents = resource["contents"] or []
            for content in contents:
                basename, ext = os.path.splitext(content)
                if ext not in extensions:
                    continue
                if basename.lower().startswith("example"):
                    continue
                template = content
                if name:
                    template = u"{}:{}".format(name, content)
                template_path = os.path.join(path, content)
                templates.append((template, template_path))
        templates.sort(key=lambda x: x[0])
        return templates
