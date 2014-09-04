from HTMLParser import HTMLParser

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash


def hash_pass(password):
    return generate_password_hash(password, 'pbkdf2:sha256:3000',
                                  salt_length=8)


def is_complete_tags(feed):
    parser = ParseCompleteHTMLTags()
    parser.feed(feed)
    parser.close()
    if parser._error:
        return False
    return True


class ParseCompleteHTMLTags(HTMLParser):
    """
    Check if every html tag has a closing tag, and in order 'last in first out'
    e.g
    <div><p></p></div>      is ok
    <div><p></div></p>      is NOT ok
    </div>                  is Not ok
    """

    start_tags = []
    _error = False

    def handle_starttag(self, tag, attrs):
        if not tag == 'br':
            self.start_tags.append(tag)

    def handle_endtag(self, tag):
        if self.start_tags and tag == self.start_tags[-1]:
            self.start_tags.pop()
        else:
            self._error = True
            return

    # def unescape(self, s):
    #     print s