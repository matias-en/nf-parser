from lxml import etree
import pytest


def _parse(xml_str: str):
    return etree.fromstring(xml_str.encode("utf-8"))


@pytest.fixture
def parse_xml():
    return _parse
