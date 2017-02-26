"""Crawls Metacritic and extracts critic and user reviews from profiles."""

import re
import os
import sys
import urllib
import urllib.request
from datetime import datetime

from bs4 import BeautifulSoup as bs
from tqdm import tqdm
import morejson as json

from holcrawl.shared import (
    _get_metacritic_dir_path,
    _result,
    _titles_from_file,
    _parse_name_for_file_name
)

METACRITIC_DIR_PATH = _get_metacritic_dir_path()

# === search ===

CHARS_TO_REMOVE = r"[\:\;,\.'/\!]"

def _parse_name_for_search(movie_name):
    parsed = re.sub(CHARS_TO_REMOVE, '', movie_name)
    return parsed.replace(' ', '+')


SEARCH_URL = ("http://www.metacritic.com/search/all/{movie_name}/results?"
              "cats%5Bmovie%5D=1&search_type=advanced")
_HEADERS = {'User-Agent': 'Mozilla/5.0'}
METACRITIC_URL = "http://www.metacritic.com"

def _get_movie_url_by_name(movie_name, year=None):
    query = SEARCH_URL.format(movie_name=_parse_name_for_search(movie_name))
    request = urllib.request.Request(query, headers=_HEADERS)
    search_res = bs(urllib.request.urlopen(request), "html.parser")
    results = search_res.find_all("li", {"class": "result"})
    correct_result = None
    for result in results:
        title = result.find_all(
            "h3", {"class": "product_title"})[0].contents[0].contents[0]
        title_match = title.strip().lower() == movie_name.strip().lower()
        if year is None and title_match:
            correct_result = result
        else:
            year_match = str(year) in str(result)
            if title_match and year_match:
                correct_result = result
    movie_url_suffix = correct_result.find_all("a")[0]['href']
    return METACRITIC_URL + movie_url_suffix


# === critics reviews page ===

MONTH_SHORTHAND_MAP = {
    "Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April",
    "May": "May", "Jun": "June", "Jul": "July", "Aug": "August",
    "Sep": "September", "Oct": "October", "Nov": "November", "Dec": "December"
}

def _parse_date_str(date_str):
    for month in MONTH_SHORTHAND_MAP:
        if month in date_str:
            return date_str.replace(month, MONTH_SHORTHAND_MAP[month])


def _get_critic_review_props(review):
    review_props = {}
    date_str = review.find_all("span", {"class": "date"})[0].contents[0]
    date_str = _parse_date_str(date_str)
    review_props['review_date'] = datetime.strptime(date_str, "%B %d, %Y").date()
    review_props['score'] = int(review.find_all("div", {"class": "metascore_w"})[0].contents[0])
    review_props['summary'] = review.find_all('a', {'class': 'no_hover'})[0].contents[0].strip()
    review_props['publication'] = None
    review_props['critic'] = None
    for link in review.find_all("a"):
        if 'publication' in link['href']:
            review_props['publication'] = link.contents[0]
        if 'critic' in link['href']:
            review_props['critic'] = link.contents[0]
    return review_props


CRITICS_REVIEWS_URL_SUFFIX = "/critic-reviews"
SCORE_CLASSES = [
    "metascore_w larger movie positive",
    "metascore_w larger movie mixed",
    "metascore_w larger movie negative"
]

def _get_critics_reviews_props(movie_url):
    critics_url = movie_url + CRITICS_REVIEWS_URL_SUFFIX
    critics_request = urllib.request.Request(critics_url, headers=_HEADERS)
    critics_page = bs(urllib.request.urlopen(critics_request), "html.parser")
    critics_props = {}
    critics_props['metascore'] = int(critics_page.find_all(
        "span", {"class": SCORE_CLASSES})[0].contents[0])
    critic_reviews = []
    for review in critics_page.find_all("div", {"class": "review"}):
        try:
            critic_reviews.append(_get_critic_review_props(review))
        except Exception:
            continue
    critics_props['pro_critic_reviews'] = critic_reviews
    return critics_props


# === user reviews page ===

def _get_user_rating_freq(users_page, rating):
    return int(users_page.find_all(
        "div", {"class": "chart {}".format(rating)})[0].find_all(
            "div", {"class": "count fr"})[0].contents[0].replace(',', ''))


def _get_user_review_props(review):
    review_props = {}
    date_str = review.find_all("span", {"class": "date"})[0].contents[0]
    date_str = _parse_date_str(date_str)
    review_props['review_date'] = datetime.strptime(
        date_str, "%B %d, %Y").date()
    review_props['score'] = int(review.find_all(
        "div", {"class": "metascore_w"})[0].contents[0])
    try:
        review_props['text'] = review.find_all(
            'span', {'class': 'blurb blurb_expanded'})[0].contents[0].strip()
    except IndexError:
        review_props['text'] = review.find_all(
            'div', {'class': 'review_body'})[0].contents[1].contents[0].strip()
    review_props['user'] = review.find_all(
        'span', {'class': 'author'})[0].contents[0].contents[0]
    review_props['total_reactions'] = int(review.find_all(
        'span', {'class': 'total_count'})[0].contents[0])
    review_props['pos_reactions'] = int(review.find_all(
        'span', {'class': 'yes_count'})[0].contents[0])
    review_props['neg_reactions'] = review_props[
        'total_reactions'] - review_props['pos_reactions']
    return review_props


def _get_user_reviews_from_page(users_page):
    review_elements = users_page.find_all("div", {"class": "review"})
    user_reviews = []
    for review in review_elements:
        try:
            user_reviews.append(_get_user_review_props(review))
        except Exception:
            continue
    # print("Extracted {} reviews.".format(len(user_reviews)))
    nexts = users_page.find_all("a", {"class": "action", "rel": "next"})
    if len(nexts) > 0:
        next_url = METACRITIC_URL + nexts[0]['href']
        next_request = urllib.request.Request(next_url, headers=_HEADERS)
        next_page = bs(urllib.request.urlopen(next_request), "html.parser")
        user_reviews += _get_user_reviews_from_page(next_page)
    return user_reviews


USERS_REVIEWS_URL_SUFFIX = "/user-reviews?page=0"
USER_SCORE_CLASSES = [
    "metascore_w user larger movie positive",
    "metascore_w user larger movie mixed",
    "metascore_w user larger movie negative"
]

def _get_user_reviews_props(movie_url):
    users_url = movie_url + USERS_REVIEWS_URL_SUFFIX
    users_request = urllib.request.Request(users_url, headers=_HEADERS)
    users_page = bs(urllib.request.urlopen(users_request), "html.parser")
    users_props = {}
    users_props['movie_name'] = users_page.find_all(
        "meta", {"property": "og:title"})[0]['content']
    user_score = float(users_page.find_all(
        "span", {"class": USER_SCORE_CLASSES})[0].contents[0])
    users_props['avg_user_score'] = user_score
    for rating in ['positive', 'mixed', 'negative']:
        users_props['{}_rating_frequency'.format(
            rating)] = _get_user_rating_freq(users_page, rating)
    users_props['user_reviews'] = _get_user_reviews_from_page(users_page)
    return users_props


# === metacritic crawling ===

def get_metacritic_movie_properties(movie_name, year=None):
    """Extracts the properties of a movie profile from Metacritic."""
    movie_url = _get_movie_url_by_name(movie_name, year)
    # print(movie_url)
    movie_props = {}
    movie_props.update(_get_critics_reviews_props(movie_url))
    movie_props.update(_get_user_reviews_props(movie_url))
    return movie_props


def crawl_by_title(movie_name, verbose, year=None,
                   parent_pbar=None):
    """Extracts a movie profile from Metacritic and saves it to disk."""
    def _print(msg):
        if verbose:
            if parent_pbar is not None:
                parent_pbar.set_description(msg)
                parent_pbar.refresh()
                sys.stdout.flush()
                tqdm()
            else:
                print(msg)
    os.makedirs(METACRITIC_DIR_PATH, exist_ok=True)
    file_name = _parse_name_for_file_name(movie_name) + ".json"
    file_path = os.path.join(METACRITIC_DIR_PATH, file_name)
    if os.path.isfile(file_path):
        _print('{} already processed'.format(movie_name))
        return _result.EXIST
    try:
        props = get_metacritic_movie_properties(movie_name, year)
        props = {'mc_'+key: props[key] for key in props}
        with open(file_path, 'w+') as json_file:
            json.dump(props, json_file, indent=2, sort_keys=True)
        _print("Done saving a profile for {}.".format(movie_name))
        return _result.SUCCESS
    except Exception as exc:
        _print("Extracting a profile for {} failed".format(movie_name))
        # traceback.print_exc()
        return _result.FAILURE
        # print("Extracting a profile for {} failed with:".format(movie_name))
        # raise exc


def crawl_by_file(file_path, verbose, year=None):
    """Crawls Metacritics, building movie profiles for a movies in the given
    file."""
    results = {res_type : 0 for res_type in _result.ALL_TYPES}
    titles = _titles_from_file(file_path)
    if verbose:
        print("Crawling over all {} Metacritic movies in {}...".format(
            len(titles), file_path))
    movie_pbar = tqdm(titles, miniters=1, maxinterval=0.0001,
                      mininterval=0.00000000001, total=len(titles))
    for title in movie_pbar:
        res = crawl_by_title(title, verbose, year, movie_pbar)
        results[res] += 1
    print("{} Metacritic movie profiles crawled.")
    for res_type in _result.ALL_TYPES:
        print('{} {}.'.format(results[res_type], res_type))
