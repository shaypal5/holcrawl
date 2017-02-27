"""Crawls and extracts choice metrics from IMDB movie profiles."""

import sys
import re
import os
from datetime import datetime
from urllib import request
import urllib
import traceback

from bs4 import BeautifulSoup as bs
from tqdm import tqdm
import pandas as pd
import morejson as json

from holcrawl.shared import (
    _get_imdb_dir_path,
    _titles_from_file,
    _result,
    _parse_string,
    _parse_name_for_file_name,
    _get_dataset_dir_path
)

_IMDB_DIR_PATH = _get_imdb_dir_path()


# ==== extracting movie properties ====

def _get_rating(prof_page):
    return float(prof_page.find_all(
        "span", {"itemprop": "ratingValue"})[0].contents[0])


def _get_rating_count(prof_page):
    return int(prof_page.find_all(
        "span", {"itemprop": "ratingCount"})[0].contents[0].replace(',', ''))


def _get_geners(prof_page):
    genres = []
    for span in prof_page.find_all("span", {"itemprop": "genre"}):
        genres.append(_parse_string(span.contents[0]))
    return genres


_REVIEW_COUNT_REGEX = r'([0-9,]+) ([a-zA-Z]+)'

def _get_review_counts(prof_page):
    user_review_count = 0
    critic_review_count = 0
    for span in prof_page.find_all("span", {"itemprop": "reviewCount"}):
        span_str = span.contents[0]
        res = re.findall(_REVIEW_COUNT_REGEX, span_str)[0]
        if res[1] == 'user':
            user_review_count = int(res[0].replace(',', ''))
        elif res[1] == 'critic':
            critic_review_count = int(res[0].replace(',', ''))
    return user_review_count, critic_review_count


def _get_metascore(prof_page):
    try:
        return int(prof_page.find_all(
            "div", {"class": "metacriticScore"})[0].contents[1].contents[0])
    except IndexError:
        return None


def _get_year(prof_page):
    return int(prof_page.find_all(
        "span", {"id": "titleYear"})[0].contents[1].contents[0])


_MOVIE_DURATION_REGEX = r'PT([0-9]+)M'

def _get_duration(prof_page):
    duration_str = prof_page.find_all(
        "time", {"itemprop": "duration"})[0]['datetime']
    return int(re.findall(_MOVIE_DURATION_REGEX, duration_str)[0])


# ==== crawling the box office section ====

_BUDGET_REGEX = r"<h4.*>Budget:</h4>\s*[\$\£]([0-9,]+)"

def _get_budget(box_contents):
    try:
        return int(re.findall(_BUDGET_REGEX, box_contents)[0].replace(',', ''))
    except IndexError:
        return None


_BUDGET_CURRENCY_REGEX = r"<h4.*>Budget:</h4>\s*([\$\£])"

def _get_budget_currency(box_contents):
    try:
        return re.findall(_BUDGET_CURRENCY_REGEX, box_contents)[0]
    except IndexError:
        return None


_OPEN_DATE_REGEX = r"<h4.*>Opening Weekend:</h4>[\s\S]*?\([A-Z]+\)[\s\S]*?" \
                  r"\(([0-9a-zA-Z\s]+)\)[\s\S]*?<h4"

def _get_opening_weekend_date(box_contents):
    try:
        open_date_str = re.findall(_OPEN_DATE_REGEX, box_contents)[0]
        return datetime.strptime(open_date_str, "%d %B %Y").date()
    except IndexError:
        return None


_OPEN_INC_REGEX = r"<h4.*>Opening Weekend:</h4>\s*[\$\£]([0-9,]+)"

def _get_opening_weekend_income(box_contents):
    try:
        return int(re.findall(
            _OPEN_INC_REGEX, box_contents)[0].replace(',', ''))
    except IndexError:
        return None


_OPEN_INC_CURRENCY_REGEX = r"<h4.*>Opening Weekend:</h4>\s*([\$\£])[0-9,]+"

def _get_opening_weekend_income_currency(box_contents):
    try:
        return re.findall(_OPEN_INC_CURRENCY_REGEX, box_contents)[0]
    except IndexError:
        return None


_CLOSING_DATE_REGEX = r"<h4.*>Gross:</h4>[\s\S]*?\([A-Z]+\)[\s\S]*?" \
                     r"\(([0-9a-zA-Z\s]+)\)"

def _get_closing_date(box_contents):
    try:
        gross_date_str = re.findall(_CLOSING_DATE_REGEX, box_contents)[0]
        return datetime.strptime(gross_date_str, "%d %B %Y").date()
    except IndexError:
        return None


_GROSS_REGEX = r"<h4.*>Gross:</h4>\s*\$([0-9,]+)[\s\S]*?\([A-Z]+\)"

def _get_gross_income(box_contents):
    try:
        return int(re.findall(_GROSS_REGEX, box_contents)[0].replace(',', ''))
    except IndexError:
        return None


_BOX_CONTENT_REGEX = r"<h3.*>Box Office</h3>([\s\S]+?)<h3"

def _get_box_office_props(prof_page):
    box_contents = re.findall(_BOX_CONTENT_REGEX, str(prof_page))[0]
    box_props = {}
    box_props['budget'] = _get_budget(box_contents)
    box_props['budget_currency'] = _get_budget_currency(box_contents)
    box_props['opening_weekend_date'] = _get_opening_weekend_date(box_contents)
    box_props['opening_weekend_income'] = _get_opening_weekend_income(
        box_contents)
    box_props['opening_weekend_income_currency'] = \
        _get_opening_weekend_income_currency(box_contents)
    box_props['closing_date'] = _get_closing_date(box_contents)
    box_props['gross_income'] = _get_gross_income(box_contents)
    return box_props


# ==== crawling the ratings page ====

def _extract_table(table):
    content = []
    for row in table.find_all("tr")[1:]:
        content.append([td.get_text() for td in row.find_all("td")])
    return content


_RATINGS_URL = 'http://www.imdb.com/title/{code}/ratings'

def _get_rating_props(movie_code):
    cur_ratings_url = _RATINGS_URL.format(code=movie_code)
    ratings_page = bs(request.urlopen(cur_ratings_url), "html.parser")
    tables = ratings_page.find_all("table")
    hist_table = tables[0]
    hist_content = _extract_table(hist_table)
    rating_freq = {}
    for row in hist_content:
        rating_freq[int(row[2])] = int(row[0])
    rating_props = {}
    rating_props['rating_freq'] = rating_freq
    demog_table = tables[1]
    demog_content = _extract_table(demog_table)
    votes_per_demo = {}
    avg_rating_per_demo = {}
    for row in demog_content:
        try:
            votes_per_demo[_parse_string(row[0])] = int(row[1])
            avg_rating_per_demo[_parse_string(row[0])] = float(row[2])
        except IndexError:
            pass
    rating_props['votes_per_demo'] = votes_per_demo
    rating_props['avg_rating_per_demo'] = avg_rating_per_demo
    return rating_props


# ==== crawling the business page ====

_BUSINESS_URL = 'http://www.imdb.com/title/{code}/business?ref_=tt_dt_bus'
_WEEKEND_CONTENT_REGEX = r"<h5>Weekend Gross</h5>([\s\S]+?)<h[0-9]>"
_US_OPEN_WEEKEND_REGEX = r"\$[\s\S]*?\(USA\)[\s\S]*?\(([0-9,]*) Screens\)"

def _get_business_props(movie_code):
    cur_business_url = _BUSINESS_URL.format(code=movie_code)
    busi_page = bs(request.urlopen(cur_business_url), "html.parser")
    busi_str = str(busi_page)
    weekend_contents = re.findall(_WEEKEND_CONTENT_REGEX, busi_str)[0]
    num_screens_list = [
        int(match.replace(',', ''))
        for match in re.findall(_US_OPEN_WEEKEND_REGEX, weekend_contents)]
    busi_props = {}
    busi_props['screens_by_weekend'] = [
        val for val in reversed(num_screens_list)]
    busi_props['opening_weekend_screens'] = busi_props['screens_by_weekend'][0]
    busi_props['max_screens'] = max(num_screens_list)
    busi_props['total_screens'] = sum(num_screens_list)
    busi_props['avg_screens'] = sum(num_screens_list) / len(num_screens_list)
    busi_props['num_weekends'] = len(num_screens_list)
    return busi_props


# ==== crawling the release page ====

_RELEASE_URL = 'http://www.imdb.com/title/{code}/releaseinfo'
_USA_ROW_REGEX = r"<tr[\s\S]*?USA[\s\S]*?(\d\d?)\s+([a-zA-Z]+)"\
                r"[\s\S]*?(\d\d\d\d)[\s\S]*?<td></td>[\s\S]*?</tr>"

def _get_release_props(movie_code):
    cur_release_url = _RELEASE_URL.format(code=movie_code)
    release_page = bs(urllib.request.urlopen(cur_release_url), "html.parser")
    release_table = release_page.find_all("table", {"id": "release_dates"})[0]
    us_rows = []
    for row in release_table.find_all("tr")[1:]:
        row_str = str(row)
        if 'USA' in row_str:
            us_rows.append(row_str)
    release_props = {}
    release_props['release_day'] = None
    release_props['release_month'] = None
    release_props['release_year'] = None
    for row in us_rows:
        if re.match(_USA_ROW_REGEX, row):
            release = re.findall(_USA_ROW_REGEX, row)[0]
            release_props['release_day'] = int(release[0])
            release_props['release_month'] = release[1]
            release_props['release_year'] = int(release[2])
    return release_props


# ==== crawling the user reviews page ====

_REVIEWS_URL = ('http://www.imdb.com/title/{code}/'
                'reviews-index?start=0;count=9999')
_USER_REVIEW_RATING_REGEX = r"alt=\"(\d|10)/10"

def _get_reviews_props(movie_code):
    cur_reviews_url = _REVIEWS_URL.format(code=movie_code)
    reviews_page = bs(urllib.request.urlopen(cur_reviews_url), "html.parser")
    reviews = reviews_page.find_all("td", {"class": "comment-summary"})
    user_reviews = []
    for review in reviews:
        try:
            rating = int(re.findall(_USER_REVIEW_RATING_REGEX, str(review))[0])
            date_str = re.findall(
                r"on (\d{1,2} [a-zA-Z]+ \d{4})", str(review))[0]
            date = datetime.strptime(date_str, "%d %B %Y").date()
            contents = review.find_all(
                'a', href=re.compile(r'reviews.+?'))[0].contents[0]
            user = review.find_all(
                'a', href=re.compile(r'/user/.+?'))[1].contents[0]
            user_reviews.append({
                'score': rating, 'review_date': date,
                'contents': contents, 'user': user
            })
        except Exception:  # pylint: disable=W0703
            pass
    return {'imdb_user_reviews': user_reviews}


# ==== crawling a movie profile ====

_TITLE_QUERY = (
    'http://www.imdb.com/find'
    '?q={title}&s=tt&ttype=ft&exact=true&ref_=fn_tt_ex'
)
_MOVIE_CODE_REGEX = r'/title/([a-z0-9]+)/'
_PROFILE_URL = 'http://www.imdb.com/title/{code}/' #?region=us


def _convert_title(title):
    return urllib.parse.quote(title).lower()


def crawl_movie_profile(movie_name, year=None):
    """Returns a basic profile for the given movie."""

    # Search
    query = _TITLE_QUERY.format(title=_convert_title(movie_name))
    search_res = bs(request.urlopen(query), "html.parser")
    tables = search_res.find_all("table", {"class": "findList"})
    if len(tables) < 1:
        return {}
    res_table = tables[0]
    if year is None:
        movie_row = res_table.find_all("tr")[0]
    else:
        for row in res_table.find_all("tr"):
            if (str(year) in str(row)) or (str(year-1) in str(row)):
                movie_row = row
    movie_code = re.findall(_MOVIE_CODE_REGEX, str(movie_row))[0]

    # Movie Profile
    cur_profile_url = _PROFILE_URL.format(code=movie_code)
    prof_page = bs(request.urlopen(cur_profile_url), "html.parser")

    # Extracting properties
    props = {}
    props['name'] = movie_name
    props['rating'] = _get_rating(prof_page)
    props['rating_count'] = _get_rating_count(prof_page)
    props['genres'] = _get_geners(prof_page)
    props['user_review_count'], props['critic_review_count'] = \
        _get_review_counts(prof_page)
    props['metascore'] = _get_metascore(prof_page)
    props['year'] = _get_year(prof_page)
    props['duration'] = _get_duration(prof_page)
    props.update(_get_box_office_props(prof_page))
    props.update(_get_rating_props(movie_code))
    props.update(_get_business_props(movie_code))
    props.update(_get_release_props(movie_code))
    props.update(_get_reviews_props(movie_code))
    return props


# ==== interface ====

def crawl_by_title(movie_name, verbose, year=None, parent_pbar=None):
    """Extracts a movie profile from IMDB and saves it to disk."""
    def _print(msg):
        if verbose:
            if parent_pbar is not None:
                parent_pbar.set_description(msg)
                parent_pbar.refresh()
                sys.stdout.flush()
                tqdm()
            else:
                print(msg)

    os.makedirs(_IMDB_DIR_PATH, exist_ok=True)
    file_name = _parse_name_for_file_name(movie_name) + '.json'
    file_path = os.path.join(_IMDB_DIR_PATH, file_name)
    if os.path.isfile(file_path):
        _print('{} already processed'.format(movie_name))
        return _result.EXIST

    # _print("Extracting a profile for {} from IMDB...".format(movie_name))
    try:
        props = crawl_movie_profile(movie_name, year)
        # _print("Profile extracted succesfully")
        # _print("Saving profile for {} to disk...".format(movie_name))
        with open(file_path, 'w+') as json_file:
            # json.dump(props, json_file, cls=_RottenJsonEncoder, indent=2)
            json.dump(props, json_file, indent=2)
        _print("Done saving a profile for {}.".format(movie_name))
        return _result.SUCCESS
    except Exception as exc:
        _print("Extracting a profile for {} failed".format(movie_name))
        # traceback.print_exc()
        return _result.FAILURE
        # print("Extracting a profile for {} failed with:".format(movie_name))
        # raise exc


def crawl_by_file(file_path, verbose, year=None):
    """Crawls IMDB and builds movie profiles for a movies in the given file."""
    results = {res_type : 0 for res_type in _result.ALL_TYPES}
    titles = _titles_from_file(file_path)
    if verbose:
        print("Crawling over all {} IMDB movies in {}...".format(
            len(titles), file_path))
    movie_pbar = tqdm(titles, miniters=1, maxinterval=0.0001,
                      mininterval=0.00000000001, total=len(titles))
    for title in movie_pbar:
        res = crawl_by_title(title, verbose, year, movie_pbar)
        results[res] += 1
    print("{} IMDB movie profiles crawled.".format(len(titles)))
    for res_type in _result.ALL_TYPES:
        print('{} {}.'.format(results[res_type], res_type))


# === uniting movie profiles to csv ===

_DEMOGRAPHICS = [
    'aged_under_18',
    'males_under_18',
    'males_aged_45+',
    'females',
    'males_aged_18-29',
    'imdb_staff',
    'imdb_users',
    'males',
    'aged_30-44',
    'females_aged_45+',
    'aged_18-29',
    'females_aged_18-29',
    'aged_45+',
    'males_aged_30-44',
    'top_1000_voters',
    'females_under_18',
    'females_aged_30-44',
    'us_users',
    'non-us_users'
]

def _decompose_dict_column(df, colname, allowed_cols):
    newdf = df[colname].apply(pd.Series)
    newdf = newdf.drop([
        col for col in newdf.columns if col not in allowed_cols], axis=1)
    newdf.columns = [colname+'.'+col for col in newdf.columns]
    return pd.concat([df.drop([colname], axis=1), newdf], axis=1)


def _dummy_list_column(df, colname):
    value_set = set([
        value for value_list in df[colname].dropna() for value in value_list])
    def _value_list_to_dict(value_list):
        try:
            return {
                value : 1 if value in value_list else 0
                for value in value_set}
        except TypeError:
            return {value : 0 for value in value_set}
    df[colname] = df[colname].apply(_value_list_to_dict)
    return _decompose_dict_column(df, colname, list(value_set))


def unite_imdb_profiles(verbose):
    """Unite all movie profiles in the IMDB profile directory."""
    if verbose:
        print("Uniting IMDB movie profiles to one csv file...")
    if not os.path.exists(_IMDB_DIR_PATH):
        print("No IMDB profiles to unite!")
        return
    profiles = []
    profile_files = os.listdir(_IMDB_DIR_PATH)
    if verbose:
        profile_files = tqdm(profile_files)
    for profile_file in profile_files:
        if verbose:
            profile_files.set_description('Reading {}'.format(profile_file))
        file_path = os.path.join(_IMDB_DIR_PATH, profile_file)
        _, ext = os.path.splitext(file_path)
        if ext == '.json':
            with open(file_path, 'r') as json_file:
                profiles.append(json.load(json_file))
    df = pd.DataFrame(profiles)
    df = _decompose_dict_column(df, 'avg_rating_per_demo', _DEMOGRAPHICS)
    df = _decompose_dict_column(df, 'votes_per_demo', _DEMOGRAPHICS)
    df = _decompose_dict_column(
        df, 'rating_freq', [str(i) for i in range(1, 11)])
    df = _dummy_list_column(df, 'genres')
    unison_fpath = os.path.join(
        _get_dataset_dir_path(), 'imdb_dataset.csv')
    df.to_csv(unison_fpath, index=False)
