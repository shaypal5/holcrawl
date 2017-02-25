"""Generate movie title files from Wikipedia."""

import urllib.request
import re
import warnings

from bs4 import BeautifulSoup as bs

from holcrawl.shared import _get_wiki_list_file_path

# good for pages from 2014 onwards
class _NewExtractor(object):

    @staticmethod
    def _extract_titles(movie_table):
        rows = movie_table.find_all('tr')
        content = []
        for row in rows:
            content.append(
                [td.get_text() for td in row.find_all(["td", "th"])])
        titles = []
        for row in content:
            if len(row) == 6:
                titles.append(row[0])
            elif len(row) == 7:
                titles.append(row[1])
            elif len(row) == 8:
                titles.append(row[2])
            else:
                print("unknown length!")
                print(row)
        return titles

    @staticmethod
    def _extract_titles_from_wiki_page(wiki_url, verbose):
        wiki_page = bs(urllib.request.urlopen(wiki_url), "html.parser")
        movies_tables = wiki_page.find_all('table', {'class': 'wikitable'})
        titles = []
        for table in movies_tables:
            if verbose:
                print("Extracting a table...")
            titles += _NewExtractor._extract_titles(table)
        titles = [title for title in titles if title != "Title"]
        if verbose:
            print('{} titles collected.'.format(len(titles)))
        return titles


# good for pages from 1999 to 2013
class _OldExtractor(object):

    MIRROR_REGEX = r"([\w\s]+):\1"

    @staticmethod
    def _parse_title(title):
        if "TheThe" in title:
            title = title[title.rfind('TheThe')+3:]
        elif "AA" in title:
            title = title[title.rfind('AA')+1:]
        else:
            matches = re.findall(_OldExtractor.MIRROR_REGEX, title)
            if len(matches) > 0:
                title = title[title.rfind(matches[0]):]
        return title.strip()

    @staticmethod
    def _extract_titles_from_wiki_page(wiki_url, verbose):
        wiki_page = bs(urllib.request.urlopen(wiki_url), "html.parser")
        table = wiki_page.find_all('table', {'class': 'wikitable'})[0]
        rows = table.find_all('tr')
        titles = []
        for row in rows:
            try:
                titles.append(_OldExtractor._parse_title(
                    row.find_all(["td"])[0].get_text()))
            except IndexError:
                pass
        if verbose:
            print('{} titles collected.'.format(len(titles)))
        return titles


FIRST_YEAR_FOR_NEW_EXTRACTOR = 2014
FIRST_YEAR_FOR_2000S_EXTRACTOR = 1999
URL_TEMPLATE = 'https://en.wikipedia.org/wiki/List_of_American_films_of_{}'

def generate_title_file(year, verbose):
    """Generate movie title files from Wikipedia."""
    if verbose:
        print("Generate movie title files from Wikipedia for {}...".format(
            year))
    if year >= FIRST_YEAR_FOR_NEW_EXTRACTOR:
        titles = _NewExtractor._extract_titles_from_wiki_page(
            URL_TEMPLATE.format(year), verbose)
    elif year >= FIRST_YEAR_FOR_2000S_EXTRACTOR:
        titles = _OldExtractor._extract_titles_from_wiki_page(
            URL_TEMPLATE.format(year), verbose)
    else:
        warnings.warn("Wikipedia crawling not supported for years before {}."
                      " Terminating.".format(FIRST_YEAR_FOR_2000S_EXTRACTOR))
        return
    with open(_get_wiki_list_file_path(year), 'w+') as titles_file:
        titles_file.write('\n'.join(titles))
