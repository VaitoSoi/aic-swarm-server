import os
import shutil
from os import path

import requests
from tqdm import tqdm
import re

import exception
import utils
from utils import (read_json,
                   keyframes,
                   keyframes_mirror,
                   temp,
                   clip_features,
                   clip_features_mirror_url,
                   keyframes_mirror_json)


def check_missing_keyframe():
    missing = []
    for keyframe in read_json(keyframes_mirror):
        if not os.path.exists(f"{keyframes}/{keyframe}"):
            missing += [keyframe]

    return missing


def check_missing_clip_feature():
    if not path.exists(clip_features):
        return True
    return False


def download_ggdrive(id: str, file: str) -> None:
    session = requests.Session()
    warning = session.get(f"https://drive.google.com/uc?id={id}")
    if warning.status_code != 200:
        raise exception.DownloadFailed(f"https://drive.google.com/uc?id={id}")

    uuid = re.findall(r'<input type="hidden" name="uuid" value="(.+)"></form>', warning.text)[0]

    url = f"https://drive.usercontent.google.com/download?export=download&confirm=t&id={id}&uuid={uuid}"
    response = session.get(url, stream=True)
    if response.status_code != 200:
        raise exception.DownloadFailed(url)

    length = int(response.headers.get("content-length", 0))
    chunk_size = 1024 * 1024

    with tqdm(total=length // chunk_size,
              unit="MB",
              ascii=True,
              desc=file) as bar:
        with open(path.join(temp, file), "wb") as file:
            for data in response.iter_content(chunk_size):
                file.write(data)
                bar.update(1)


def download(url: str, file: str) -> None:
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        raise exception.DownloadFailed(url)

    length = int(response.headers.get("content-length", 0))
    chunk_size = 1024 * 1024
    with tqdm(total=length // chunk_size,
              unit="MB",
              ascii=True,
              desc=file) as bar:
        with open(path.join(temp, file), "wb") as file:
            for data in response.iter_content(chunk_size):
                file.write(data)
                bar.update(1)
    return


def download_keyframe(keyframe):
    try:
        url = keyframes_mirror_json.get(keyframe, None)
        if url.startswith("drive:"):
            download_ggdrive(url[6:], f"{keyframe}.zip")
        else:
            download(url, f"{keyframe}.zip")
    except exception.DownloadFailed as error:
        print(f"Download failed: {error.args[0]}")
        return
    else:
        shutil.unpack_archive(path.join(temp, f"{keyframe}.zip"), path.join(temp, keyframe))
        shutil.move(path.join(temp, keyframe, "keyframes"), path.join(keyframes, keyframe))
        os.remove(f"{temp}/{keyframe}.zip")
        shutil.rmtree(f"{temp}/{keyframe}")


def download_clip_feature():
    try:
        download(clip_features_mirror_url, "clip_features.zip")
    except exception.DownloadFailed as error:
        print(f"Download failed: {error.args[0]}")
    else:
        shutil.unpack_archive(path.join(temp, "clip_features.zip"), path.join(temp, "clip_features"))
        shutil.move(path.join(temp, "clip_features", "clip-features-32"), clip_features)
        os.remove(f"{temp}/clip_features.zip")
        shutil.rmtree(f"{temp}/clip_features")


def download_missing() -> None:
    missing = check_missing_keyframe()
    if missing:
        print(f"Missing keyframes: {", ".join(missing)}")
        for keyframe in tqdm(missing, unit="keyframe", ascii=True, desc="Downloading keyframes"):
            download_keyframe(keyframe)

    if check_missing_clip_feature():
        print("Missing clip feature")
        download_clip_feature()
