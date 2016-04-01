from collections import namedtuple

import dateutil.parser
import requests
from lxml import etree
from requests.exceptions import RequestException

from ocfweb.caching import periodic


_namespaces = {'atom': 'http://www.w3.org/2005/Atom'}


class Post(namedtuple('Post', [
    'id',
    'published',
    'updated',
    'title',
    'content',
    'author_name',
    'author_email',
    'link',
])):

    @classmethod
    def from_element(cls, element):
        def grab_attr(attr):
            el = element
            for part in attr.split('_'):
                el = el.find('atom:' + part, namespaces=_namespaces)
            return el.text

        attrs = {
            attr: grab_attr(attr)
            for attr in cls._fields
        }
        attrs['updated'] = dateutil.parser.parse(attrs['updated'])
        attrs['published'] = dateutil.parser.parse(attrs['published'])
        attrs['link'] = element.xpath(
            'atom:link[@type="text/html"]',
            namespaces=_namespaces,
        )[0].get('href')
        return cls(**attrs)


@periodic(60)
def get_blog_posts():
    """Parse the beautiful OFC status blog atom feed into a list of Posts.

    Unfortunately Blogger is hella flakey so we use it inside a loop and fail
    silently if it doesn't succeed.
    """
    for _ in range(5):
        try:
            tree = etree.fromstring(
                requests.get(
                    'http://status.ocf.berkeley.edu/feeds/posts/default',
                    timeout=2,
                ).content,
            )
        except RequestException:
            pass
        else:
            break
    else:
        # fail silently
        return []

    return [
        Post.from_element(post)
        for post in tree.xpath(
            '//atom:entry',
            namespaces=_namespaces,
        )
    ]
