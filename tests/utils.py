import os
import tempfile
import sh


def xml_compare(x1, x2, reporter=None):
    if x1.tag != x2.tag:
        if reporter:
            reporter('Tags do not match: %s and %s' % (x1.tag, x2.tag))
        return False
    for name, value in x1.attrib.items():
        if not text_compare(x2.attrib.get(name), value):
            if reporter:
                reporter('<%s> Attributes do not match: %s=%r, %s=%r'
                         % (x1.tag, name, value, name, x2.attrib.get(name)))
            return False
    for name in x2.attrib.keys():
        if name not in x1.attrib:
            if reporter:
                reporter('<%s> x2 has an attribute x1 is missing: %s'
                         % (x1.tag, name))
            return False
    if not text_compare(x1.text, x2.text):
        if reporter:
            reporter('<%s> text: %r != %r' % (x1.tag, x1.text, x2.text))
        return False
    if not text_compare(x1.tail, x2.tail):
        if reporter:
            reporter('<%s> tail: %r != %r' % (x1.tag, x1.tail, x2.tail))
        return False
    cl1 = x1.getchildren()
    cl2 = x2.getchildren()
    if len(cl1) != len(cl2):
        if reporter:
            reporter('<%s> children length differs, %i != %i'
                     % (x1.tag, len(cl1), len(cl2)))
        return False
    for i, c1 in enumerate(cl1):
        for c2 in cl2:
            if xml_compare(c1, c2):  # no reporter, fail silently
                # cl2.remove(c2)
                break
        else:
            if reporter:
                xml_compare(c1, x2.getchildren()[i], reporter=reporter)
                # xml_compare(c1, cl2[0], reporter=reporter)
                reporter('<%s> children %i do not match: %s'
                         % (x1.tag, i, c1.tag))
            return False
    return True


def text_compare(t1, t2):
    if not t1 and not t2:
        return True
    if t1 == '*' or t2 == '*':
        return True
    return (t1 or '').strip() == (t2 or '').strip()


def xsd_validate(xml_bytes):
    with tempfile.NamedTemporaryFile() as f:
        f.write(xml_bytes)
        f.flush()

        sh.xmllint(f.name, '--noout', '--schema',
                   os.path.abspath('tests/schema.xsd'))
