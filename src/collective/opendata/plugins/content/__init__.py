# -*- coding: utf-8 -*-
from Products.CMFPlone import PloneMessageFactory as pmf
from collective.opendata import _
from collective.opendata.interfaces import IDataPlugin
from collective.opendata.plugins import DataPlugin
from plone import api
from zope.interface import implements
import rdflib
from rdflib.namespace import RDF, RDFS

DC_MAPPING = {
    'contributor': 'listContributors',
    'coverage': '',
    'creator': 'Creator',
    'date': 'Date',
    'description': 'Description',
    'format': 'Format',
    'identifier': 'Identifier',
    'language': 'Language',
    'publisher': 'Publisher',
    'relation': '',
    'rights': 'Rights',
    'source': '',
    'subject': 'Subject',
    'title': 'Title',
    'type': ''
}


class Content(DataPlugin):
    implements(IDataPlugin)

    name = 'content'
    title = _(u'Content Metadata')
    description = _(u'''Content information''')

    portal_types = [pmf(u'File'), pmf(u'Page'), pmf(u'Image'), pmf(u'Event'), pmf(u'News Item'), pmf(u'Folder')]

    def __init__(self, *args, **kwargs):

        for pt in self.portal_types:
            attr_name = pt.replace(' ', '_')
            setattr(self, attr_name, self._process_content)

    def _process_content(self, request=None, **kwargs):
        subpath = kwargs.get('subpath', [])
        portal_type = subpath[1] if len(subpath) > 1 else None
        uid = subpath[2] if len(subpath) > 2 else None
        if uid:
            return self.content(portal_type=portal_type, uid=uid)
        else:
            return self.list(portal_type=portal_type)

    @property
    def structure(self):
        structure = {}
        dc_fields = {
            'uri': _(u'Content URI'),
            'url': _(u'Content site address'),
            'Id': _(u'Content id'),
            'Title': _(u'Dublin Core Title element - resource name.'),
            'Description': _(u'Dublin Core Description element - resource name.'),
            'Creator': _(u'Dublin Core Creator element - resource author.'),
        }
        for portal_type in self.portal_types:
            msgid = _(u'dublin_core_conttype_msg', default=u'Dublin Core info for ${type} content type', mapping={u"type": portal_type})
            structure[portal_type] = {
                'description': msgid
            }
            structure[portal_type]['fields'] = dc_fields.copy()
        return structure

    def _dc_content(self, content):
        """ Returns DC info

        :returns: dictionary with content information
        :rtype: dict
        """
        data = {}
        for key, value in DC_MAPPING.items():
            if value and hasattr(content, value):
                # Using method
                data[key] = getattr(content, value)()
        data['type'] = content.portal_type
        return data

    def content(self, portal_type=None, uid=None):
        """ Returns info about a content

        :returns: dictionary with content information
        :rtype: dict
        """
        data = {}
        if uid:
            try:
                content = api.content.get(UID=uid)
            except ValueError:
                return data
            if content.portal_type == portal_type:
                data = self._dc_content(content)
        return data

    def list(self, portal_type=None):
        """ Returns info about a content

        :returns: dictionary with content information
        :rtype: dict
        """
        ct = api.portal.get_tool('portal_catalog')
        items = []
        results = ct.searchResults(portal_type=portal_type)
        for brain in results:
            uid = brain.UID
            item = {'uid': uid}
            item['identifier'] = brain.getURL()
            # Need to escape portal_type
            item['uri'] = '{0}/{1}/{2}'.format(
                self.uri,
                portal_type,
                uid
            )
            item['title'] = brain.Title
            items.append(item)
        return items
    
    @property
    def dc_properties(self):
        g = rdflib.Graph()
        g.parse("dcelements.rdf")
        properties = g.subjects(RDF['type'], RDF['Property'])
        prop_dict = {}
        for prop in properties:
            prop_dict[prop.split('/')[-1]] = {
                'label' : g.value(prop, RDFS['label']),
                'description' : g.value(prop, RDFS['comment'])
            }
        return prop_dict
