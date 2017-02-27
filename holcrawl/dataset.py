"""Unite various resources into a movies dataset."""

import os

import numpy as np
import pandas as pd
from tqdm import tqdm
import morejson as json

import holcrawl.shared
import holcrawl.imdb_crawl


_IMDB_DIR_PATH = holcrawl.shared._get_imdb_dir_path()
_METACRITIC_DIR_PATH = holcrawl.shared._get_metacritic_dir_path()
_UNITED_DIR_PATH = holcrawl.shared._get_united_dir_path()
_DEMOGRAPHICS = holcrawl.imdb_crawl._DEMOGRAPHICS


def _prof_names_in_dir(dir_path):
    profile_file_paths = os.listdir(dir_path)
    return [
        os.path.splitext(os.path.split(fpath)[1])[0]
        for fpath in profile_file_paths
        if os.path.splitext(os.path.split(fpath)[1])[1] == '.json'
    ]


def _prof_names_in_all_resources():
    imdb_profs = _prof_names_in_dir(_IMDB_DIR_PATH)
    meta_profs = _prof_names_in_dir(_METACRITIC_DIR_PATH)
    return set(imdb_profs).intersection(meta_profs)


def build_united_profiles(verbose):
    """Build movie profiles with data from all resources."""
    os.makedirs(_UNITED_DIR_PATH, exist_ok=True)
    prof_names = sorted(_prof_names_in_all_resources())
    if verbose:
        print("Building movie profiles with data from all resources.")
        prof_names = tqdm(prof_names)
    for prof_name in prof_names:
        file_name = prof_name + '.json'
        imdb_prof_path = os.path.join(_IMDB_DIR_PATH, file_name)
        with open(imdb_prof_path, 'r') as imbd_prof_file:
            imdb_prof = json.load(imbd_prof_file)
        meta_prof_path = os.path.join(_METACRITIC_DIR_PATH, file_name)
        with open(meta_prof_path, 'r') as meta_prof_file:
            meta_prof = json.load(meta_prof_file)
        united_prof = {**imdb_prof, **meta_prof}
        united_prof_fpath = os.path.join(_UNITED_DIR_PATH, file_name)
        with open(united_prof_fpath, 'w+') as unite_prof_file:
            json.dump(united_prof, unite_prof_file, indent=2, sort_keys=True)


def _num_reviews_by_opening_generator(colname):
    def _num_reviews_by_opening(row):
        return len([
            review for review in row[colname]
            if review['review_date'] <= row['opening_weekend_date']
        ])
    return _num_reviews_by_opening


def _avg_review_generator(colname):
    def _avg_review(row):
        return np.mean([review['score'] for review in row[colname]])
    return _avg_review


def _avg_review_by_opening_generator(colname):
    def _avg_review_by_opening(row):
        return np.mean([
            review['score'] for review in row[colname]
            if review['review_date'] <= row['opening_weekend_date']
        ])
    return _avg_review_by_opening


def build_csv(verbose):
    """Build movie dataset from united profiles."""

    # build profiles array
    profiles = []
    profile_files = os.listdir(_UNITED_DIR_PATH)
    if verbose:
        profile_files = tqdm(profile_files)
    for profile_file in profile_files:
        if verbose:
            profile_files.set_description('Reading {}'.format(profile_file))
        file_path = os.path.join(_UNITED_DIR_PATH, profile_file)
        _, ext = os.path.splitext(file_path)
        if ext == '.json':
            with open(file_path, 'r') as json_file:
                profiles.append(json.load(json_file))

    # flatten some dict or array columns
    df = pd.DataFrame(profiles)
    df = df[df['opening_weekend_date'].notnull()]
    df = holcrawl.imdb_crawl._decompose_dict_column(
        df, 'avg_rating_per_demo', _DEMOGRAPHICS)
    df = holcrawl.imdb_crawl._decompose_dict_column(
        df, 'votes_per_demo', _DEMOGRAPHICS)
    df = holcrawl.imdb_crawl._decompose_dict_column(
        df, 'rating_freq', [str(i) for i in range(1, 11)])
    df = holcrawl.imdb_crawl._dummy_list_column(df, 'genres')

    df['num_mc_critic'] = df.apply(
        lambda row: len(row['mc_pro_critic_reviews']), axis=1)
    df['avg_mc_critic'] = df.apply(
        _avg_review_generator('mc_pro_critic_reviews'), axis=1)
    df['num_mc_critic_by_opening'] = df.apply(
        _num_reviews_by_opening_generator('mc_pro_critic_reviews'), axis=1)
    df['avg_mc_critic_by_opening'] = df.apply(
        _avg_review_by_opening_generator('mc_pro_critic_reviews'), axis=1)

    df['num_mc_user'] = df.apply(
        lambda row: len(row['mc_user_reviews']), axis=1)
    df['avg_mc_user'] = df.apply(
        _avg_review_generator('mc_user_reviews'), axis=1)
    df['num_mc_user_by_opening'] = df.apply(
        _num_reviews_by_opening_generator('mc_user_reviews'), axis=1)
    df['avg_mc_user_by_opening'] = df.apply(
        _avg_review_by_opening_generator('mc_user_reviews'), axis=1)


    df['num_imdb_user'] = df.apply(
        lambda row: len(row['imdb_user_reviews']), axis=1)
    df['avg_imdb_user'] = df.apply(
        _avg_review_generator('imdb_user_reviews'), axis=1)
    df['num_imdb_user_by_opening'] = df.apply(
        _num_reviews_by_opening_generator('imdb_user_reviews'), axis=1)
    df['avg_imdb_user_by_opening'] = df.apply(
        _avg_review_by_opening_generator('imdb_user_reviews'), axis=1)

    df['opening_month'] = df['opening_weekend_date'].map(
        lambda opendate: opendate.month)
    df['opening_day'] = df['opening_weekend_date'].map(
        lambda opendate: opendate.day)
    df['opening_day_of_year'] = df['opening_weekend_date'].map(
        lambda opendate: opendate.timetuple().tm_yday)

    # save to file
    dataset_dir = holcrawl.shared._get_dataset_dir_path()
    os.makedirs(dataset_dir, exist_ok=True)
    csv_fpath = os.path.join(dataset_dir, 'movies_dataset.csv')
    df.to_csv(csv_fpath, index=False)
