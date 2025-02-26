# -*- coding: utf-8 -*-

import os
import time
from weasyprint import HTML

from senaite.impress.template import TemplateFinder as TF
from senaite.impress.publisher import Publisher as Pu

from bika.coa import logger


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


class Publisher(Pu):
    """Publishes HTML into printable formats
    """

    def _layout_and_paginate(self, html):
        """Layout and paginate the given HTML into WeasyPrint `Document` objects

        http://weasyprint.readthedocs.io/en/stable/api.html#python-api
        """
        old_html = html
        # ensure we have plain html and not a BS4 node
        html = self.to_html(html)

        start = time.time()
        # Lay out and paginate the document
        html = HTML(
            string=html, url_fetcher=self.url_fetcher, base_url=self.base_url)
        document = html.render(stylesheets=self.css)
        end = time.time()
        logger.info("Publisher::Layout step took {:.2f}s for {} pages"
                    .format(end-start, len(document.pages)))
        number_of_pages = str(len(document.pages))
        del html
        del document
        # NOTE: Rerun now that we have number_of_pages HACK!!!
        tags = old_html.find_all("div", text=lambda x: x and "number_of_pages" in x)
        for tag in tags:
            tag.string = tag.text.replace("number_of_pages", number_of_pages)

        tag = old_html.find("div", text=lambda x: x and "last" in x)
        if tag:
            tag.string = tag.text.replace("last", number_of_pages)

        # ensure we have plain html and not a BS4 node
        html = self.to_html(old_html)

        start = time.time()
        # Lay out and paginate the document
        html = HTML(
            string=html, url_fetcher=self.url_fetcher, base_url=self.base_url)
        document = html.render(stylesheets=self.css)
        end = time.time()
        logger.info("Publisher::Layout step took {:.2f}s for {} pages"
                    .format(end-start, len(document.pages)))
        return document
