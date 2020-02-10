from bika.lims import api
from bika.lims.browser.analysisrequest.published_results import \
    AnalysisRequestPublishedResults as ARPR
from bika.lims import bikaMessageFactory as _
from bika.lims.browser.bika_listing import BikaListingView
from ZODB.POSException import POSKeyError


class AnalysisRequestPublishedResults(ARPR):

    def __init__(self, context, request):
        BikaListingView.__init__(self, context, request)
        self.context = context
        self.request = request

        self.catalog = "portal_catalog"
        self.contentFilter = {
            'portal_type': 'ARReport',
            'path': {
                'query': api.get_path(self.context),
                'depth': 1,
            },
            'sort_order': 'reverse'
        }
        self.context_actions = {}
        self.show_select_column = True
        self.show_workflow_action_buttons = False
        self.form_id = 'published_results'
        self.icon = "{}//++resource++bika.lims.images/report_big.png".format(
            self.portal_url)
        self.title = self.context.translate(_("Published results"))
        self.columns = {
            'Date': {'title': _('Published Date')},
            'PublishedBy': {'title': _('Published By')},
            'DownloadPDF': {'title': _('Download PDF')},
            'DownloadCSV': {'title': _('Download CSV')},
            'Recipients': {'title': _('Recipients')},
        }
        self.review_states = [
            {'id': 'default',
             'title': 'All',
             'contentFilter': {},
             'columns': [
                 'Date',
                 'PublishedBy',
                 'Recipients',
                 'DownloadPDF',
                 'DownloadCSV',
             ]
             },
        ]

    def folderitem(self, obj, item, index):

        item['PublishedBy'] = self.user_fullname(obj.Creator())

        # Formatted creation date of report
        creation_date = obj.created()
        fmt_date = self.ulocalized_time(creation_date, long_format=1)
        item['Date'] = fmt_date

        # Recipients as mailto: links
        recipients = obj.getRecipients()
        links = ["<a href='mailto:{EmailAddress}'>{Fullname}</a>".format(**r)
                 for r in recipients if r['EmailAddress']]
        if len(links) == 0:
            links = ["{Fullname}".format(**r) for r in recipients]
        item['replace']['Recipients'] = ', '.join(links)

        # download link 'Download PDF (size)'
        dll = []
        try:  #
            pdf_data = obj.getPdf()
            assert pdf_data
            z = pdf_data.get_size()
            z = z / 1024 if z > 0 else 0
            dll.append("<a href='{}/at_download/Pdf'>{}</a>".format(
                obj.absolute_url(), _("Download PDF"), z))
        except (POSKeyError, AssertionError):
            # POSKeyError: 'No blob file'
            pass
        item['DownloadPDF'] = ''
        item['after']['DownloadPDF'] = ', '.join(dll)
        # download link 'Download CSV (size)'
        dll = []
        if hasattr(obj, 'CSV'):
            try:
                dll.append("<a href='{}/at_download/CSV'>{}</a>".format(
                    obj.absolute_url(), _("Download CSV"), 0))
            except (POSKeyError, AssertionError):
                # POSKeyError: 'No blob file'
                pass
            item['DownloadCSV'] = ''
            item['after']['DownloadCSV'] = ', '.join(dll)

        return item
