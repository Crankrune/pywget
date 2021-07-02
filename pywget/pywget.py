from re import I
import click
import datetime
import hashlib
import os
import regex
import requests
import sys
import zlib
from dateutil.parser import parse
from pathlib import Path, WindowsPath
from pytz import timezone
from tqdm import tqdm
from typing import Union
from urllib.parse import urlparse


def crc32_str(string: str) -> str:
    return zlib.crc32(bytes(string, "utf-8"))


def md5_str(string: str) -> str:
    return hashlib.md5(bytes(string, "utf-8")).hexdigest()


def get_filename(url: str) -> str:
    name = urlparse(url).path
    if regex.search("/", name):
        name = regex.split("/", name, flags=regex.I)[-1]
        name = regex.search("(.*\.[\w\d]{1,4})", name, regex.I).group()
    return name


def append_filename(target: WindowsPath):
    cp_count = 1
    while target.exists():
        if cp_count == 1:
            name, ext = target.name.split(".")
            target = Path(f"{target.parent}/{name}-1.{ext}")
        else:
            target = Path(
                regex.sub("(-\d{,3})?(\..*?)$", f"-{cp_count}\\2", str(target), regex.I)
            )
        cp_count += 1
    return target


def hash_filename(link: str, fn: str) -> tuple[str]:
    crc = crc32_str(link)
    md5 = md5_str(link)
    nm, ext = regex.search("(.*?)(\.[\d\w]{1,6}$)", fn).groups()
    crc_out = f"{nm}_{crc}{ext}"
    md5_out = f"{nm}_{md5}{ext}"
    return crc_out, md5_out


def pywget(
    url: str,
    path: str = "./",
    filename: str = None,
    timestamping: bool = False,
    noclobber: bool = False,
    cont: bool = False,
    quiet: bool = False,
    crc_name: bool = False,
    md5_name: bool = False,
    force_filename: bool = False,
    spder: bool = False,
) -> None:
    """
    :param url:
    URL to download.
    :param path:
    Folder to download files to, can be relative or absolute. Accepts pathlib objects.
    :param filename:
    Optional: set file instead of getting it from url
    :param timestamping:
    Don't download if already saved file is newer than url.
    :param noclobber:
    Don't download already saved files, no overwrite.
    :param cont:
    Continue downloads.
    :param rename:
    Rename new downloads instead of overwrite
    :param quiet:
    Hide all download progress
    :param crc_name:
    Append crc32 value of link to filename
    :param md5_name:
    Append md5 value of link to filename
    :param force_filename:
    Don't try and get filename, only use the one provided
    :param spder:
    Print the file name and info for the url. Does not download.
    :return:
    """

    if spder:
        return spider(url)

    fl_out = sys.stdout if not quiet else open("nul", "w")
    if force_filename or filename:
        fn = filename
    else:
        fn = get_filename(url)

    if not path:
        path = "./"

    crc_fn, md5_fn = hash_filename(url, fn)
    if crc_name:
        fn = crc_fn
    elif md5_name:
        fn = md5_fn

    output = Path(path, fn)
    headers = {}
    writemode = "wb"

    if output.exists():
        if cont:
            headers["Range"] = f"bytes={output.stat().st_size}-"
            writemode = "ab"
        elif timestamping:
            file_stat = os.stat(output)
            resp = requests.get(url, stream=True, allow_redirects=True)
            try:
                modtime = parse(resp.headers["last-modified"]).astimezone(
                    timezone("America/Chicago")
                )
            except KeyError:
                modtime = datetime.datetime.now()
            if file_stat.st_mtime >= modtime.timestamp():
                print(
                    f'"{fn}" exists, ignoring because of timestamping (-n).',
                    file=fl_out,
                )
                return
        elif noclobber:
            print(f'"{fn}" exists, ignoring because of noclobber (-nc).', file=fl_out)
            return
        else:
            output = append_filename(output)

    os.makedirs(output.parent, exist_ok=True)
    resp = requests.get(url, stream=True, allow_redirects=True, headers=headers)
    try:
        modtime = parse(resp.headers["last-modified"]).astimezone(
            timezone("America/Chicago")
        )
    except KeyError:
        modtime = datetime.datetime.now()

    try:
        content_length = int(resp.headers["content-length"])
    except KeyError:
        content_length = None
    try:
        with open(output, writemode) as f:
            with tqdm(
                # total=int(resp.headers["content-length"]),
                total=content_length,
                unit="B",
                unit_scale=True,
                desc=output.name[:75],
                initial=0,
                ascii=True,
                disable=quiet,
            ) as pbar:
                for chunk in resp.iter_content(chunk_size=1024):
                    f.write(chunk)
                    pbar.update(len(chunk))
        file_stat = os.stat(output)
        os.utime(output, (file_stat.st_atime, modtime.timestamp()))
        # fl_out.close()
    except (ConnectionResetError, requests.exceptions.ChunkedEncodingError) as e:
        raise Exception("Connection reset, stopping.")


@click.command()
@click.argument("url", nargs=-1)
@click.option("-p", "--prefix", "path", type=str)
@click.option("-o", "--output", "filename", type=str)
@click.option("-n", "--timestamping", "timestamping", is_flag=True)
@click.option("-nc", "--noclobber", "noclobber", is_flag=True)
@click.option("-c", "--cont", "cont", is_flag=True)
@click.option("-q", "--quiet", "quiet", is_flag=True)
@click.option("-crc", "crc_name", is_flag=True)
@click.option("-md5", "md5_name", is_flag=True)
@click.option("-ff", "--force-filename", "force_filename", is_flag=True)
@click.option("-s", "--spider", "spder", is_flag=True)
def cli_pywget(
    url: tuple,
    path: str = "./",
    filename: str = None,
    timestamping: bool = False,
    noclobber: bool = False,
    cont: bool = False,
    quiet: bool = False,
    crc_name: bool = False,
    md5_name: bool = False,
    force_filename: bool = False,
    spder: bool = False,
) -> None:
    """
    :param url:
    URL to download.
    :param path:
    Folder to download files to, can be relative or absolute. Accepts pathlib objects.
    :param filename:
    Optional: set file instead of getting it from url
    :param timestamping:
    Don't download if already saved file is newer than url.
    :param noclobber:
    Don't download already saved files, no overwrite.
    :param cont:
    Continue downloads.
    :param rename:
    Rename new downloads instead of overwrite
    :param quiet:
    Hide all download progress
    :param crc_name:
    Append crc32 value of link to filename
    :param md5_name:
    Append md5 value of link to filename
    :param force_filename:
    Don't try and get filename, only use the one provided
    :param spder:
    Print the file name and info for the url. Does not download.
    :return:
    """

    if spder:
        if len(url) == 1:
            return spider(url[0])
        else:
            for l in url:
                spider(l)
    else:
        for l in url:
            pywget(
                l,
                path=path,
                filename=filename,
                timestamping=timestamping,
                noclobber=noclobber,
                cont=cont,
                quiet=quiet,
                crc_name=crc_name,
                md5_name=md5_name,
                force_filename=force_filename,
            )


def spider(url: str) -> dict:
    fn = get_filename(url)
    resp = requests.get(url, stream=True, allow_redirects=True)
    size = int(resp.headers["content-length"]) // 1024
    modtime = parse(resp.headers["last-modified"]).astimezone(
        timezone("America/Chicago")
    )
    print(
        f"Filename: {fn}\nSize: {size}kB\nModified: {modtime:%Y-%m-%d %I:%M:%S %p %Z}\n"
    )
    return {"filename": fn, "size": size, "modtime": modtime, "resp": resp}


if __name__ == "__main__":
    cli_pywget()
