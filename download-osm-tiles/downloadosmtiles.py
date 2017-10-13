#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# A Python version of GEO OSM TILES (originally in perl).
# The original is located at: https://github.com/RKrahl/geo-osm-tiles
# It only works with osm link, currently.
# Usage: python downloadosmtiles.py -link "OSM_LINK" -z "MIN_ZOOM:MAX_ZOOM" \
#                                    -p "path/to/save/tiles/"
#
# For more info about tile calculations: 
#   http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Implementations
#---------------------------------------------------------


import math
import os
import argparse
import mpmath
import urllib
from re import split
from collections import deque
from time import sleep
try:
    import urlparse
except ImportError:
    # Python 3 import
    import urllib.parse as urlparse


BASE_URL = "http://tile.openstreetmap.org/"
OFF_CONST = 350.0

INPUT_LINK = "http://www.openstreetmap.org/?lat=-15.8137&lon=-47.9031&zoom=10"
ZOOM_LEVEL = '1:5'
DIR_PATH = ""


def parse_args():
    global INPUT_LINK, DIR_PATH, ZOOM_LEVEL
    parser = argparse.ArgumentParser()
    parser.add_argument('-link', '--osm-link', type=str, required=True,
                        help="Link to OSM website with arguments formatted like ?lat=<VALUE>&lon=<VALUE>&zoom=<VALUE>")
    parser.add_argument('-z', '--zoom-range', type=str, required=True,
                        help="Zoom levels to be downloaded in the format '<VALUE>:<VALUE>'")
    parser.add_argument('-p', '--dest-path', type=str, required=False,
                        help="Directory path where the tiles will be stored at.")

    args = parser.parse_args()

    INPUT_LINK = args.osm_link
    ZOOM_LEVEL = args.zoom_range
    if args.dest_path:
        DIR_PATH = args.dest_path


def lon_to_tilex(lon, zoom):
    result = int((lon+180.0)/360.0*(2.0**zoom))
    return result


def lat_to_tiley(lat, zoom):
    lat1 = lat*mpmath.pi/180.0
    result = int((1.0 - math.log(mpmath.tan(lat1) +
                                 mpmath.sec(lat1))/mpmath.pi)/2.0*(2.0**zoom))
    return result


def tile_to_path(x, y, zoom):
    return ("{}/{}/{}.png".format(zoom, x, y))


def parse_url(url):
    parsed = urlparse.urlparse(url)
    return urlparse.parse_qs(parsed.query)


def check_lon_range(min, max):
    if min < -180.0:
        min = -180.0
    elif min > 179.9999999:
        min = 179.9999999

    if max < -180.0:
        max = -180.0
    elif max > 179.9999999:
        max = 179.9999999

    return (min, max)


def check_lat_range(min, max):
    if min < -85.0511287798:
        min = -85.0511287798
    elif min > 85.0511287798:
        min = 85.0511287798

    if max < -85.0511287798:
        max = -85.0511287798
    elif max > 85.0511287798:
        max = 85.0511287798

    return (min, max)


def download_tile(lon, lat, zoom):
    fname = tile_to_path(lon, lat, zoom)
    tile_path = os.path.join(DIR_PATH, fname)
    tile_url = BASE_URL + fname
    if os.path.isfile(tile_path):
        print("The file {} was already downloaded.".format(fname))
    else:
        directory = os.path.dirname(tile_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        for attempt in range(3):
            try:
                urllib.urlretrieve(tile_url, tile_path)
            except:
                print("""Error: Something happened while downloading tile {}. \\ 
                    Trying again ({})...""".fomat(attempt+1))
                sleep(3)
                continue
            else:
                print("Successful download of tile {}.".format(fname, tile_path))
                break

def download_tiles(queue):
    global DIR_PATH
    if not DIR_PATH:
        DIR_PATH = "MAP_TILES/"
        try:
            os.mkdir(DIR_PATH)
        except OSError:
            print("{} already exists.".format(DIR_PATH))

    tiles = sorted(queue, key=lambda k: k['zoom'])
    for t in tiles:
        download_tile(t['lon'], t['lat'], t['zoom'])

def parsing_urls(input_url):
    if "map" in input_url: 
    # new osm url format
        url = input_url.split('/')
        zoom = float(url[3].split('=')[1])
        lat = float(url[5])
        lon = float(url[4])
    else:   
    #old osm format with lat/lon names                
        url = parse_url(input_url)  
        lat = float(url['lat'][0])
        lon = float(url['lon'][0])
        zoom = float(url['zoom'][0])
    return lat, lon, zoom

def main():
    queue = deque([])
    try:
        lat, lon, zoom = parsing_urls(INPUT_LINK)
        offs = float(OFF_CONST/math.pow(2, zoom))
        lat_max, lat_min = check_lat_range(lat - offs, lat + offs)
        lon_min, lon_max = check_lon_range(lon - offs, lon + offs)
        zooms = split('[-:]', ZOOM_LEVEL)
        zoom_min = int(zooms[0])
        zoom_max = int(zooms[1]) + 1

        for z in range(zoom_min, zoom_max):
            tilex_min = lon_to_tilex(lon_min, z)
            tilex_max = lon_to_tilex(lon_max, z)
            tiley_min = lat_to_tiley(lat_min, z)
            tiley_max = lat_to_tiley(lat_max, z)
            n_tilesx = tilex_max - tilex_min + 1
            n_tilesy = tiley_max - tiley_min + 1

            print("Schedule {} tiles ({} x {}) for level {}".format(
                n_tilesx*n_tilesy, n_tilesx, n_tilesy, z))
            for y in range(tiley_min, tiley_max + 1):
                for x in range(tilex_min, tilex_max + 1):
                    queue.append({"lon": x, "lat": y, "zoom": z})
        download_tiles(queue)

    except:
        print("Error: An Unexpected error happened.")

if __name__ == '__main__':
    parse_args()
    main()
