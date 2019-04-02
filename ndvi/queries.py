import uuid

import numpy as np
import numpy.ma as ma
import rasterio as rio
from pyproj import transform, Proj
from rasterio import mask
# Create your views here.
from shapely.geometry import Polygon
from matplotlib import cm

colormaps = {'NDVI': cm.Greens, 'NDWI': cm.Blues}


def clip_image(coords_poly, fname):
    """
    Clips the given downloaded image
    :param coords_poly: coordinates to clip to
    :param fname: filename to open
    :return: the masked image as a numpy array
    """
    with rio.open("%s.tif" % fname) as src:
        out_image, out_transform = mask.mask(src, [to_geojson(coords_poly)],
                                             crop=True, nodata=-9999)
        masked_image = ma.masked_equal(out_image, -9999)
    return masked_image


def generate_request(data, out_crs='EPSG:32634'):
    """
    Formats the data for the incoming request to WCS format
    :param data: data from the request
    :param out_crs: the crs to reproject the image to
    :return: The coordinates to clip against, the layer name and the request URL
    """
    layer_name = data['properties']['layer_name']
    feature = data['geometry']
    poly = Polygon(feature['coordinates'][0])
    coords_poly = reproject_coordinates(feature['coordinates'][0], Proj(init='EPSG:4326'), Proj(init=out_crs))
    coords = [[poly.bounds[0], poly.bounds[1]], [poly.bounds[2], poly.bounds[3]]]
    min_x, min_y, max_x, max_y = reproject_coordinates(coords, Proj(init='EPSG:4326'), Proj(init='EPSG:32634'),
                                                       flat=True)
    req_url = "http://geoserver:8080/geoserver/wcs?service=WCS&version=2.0.1&request=getcoverage&coverageid=%s&subset=E(%%22%f%%22,%%22%f%%22)&subset=N(%%22%f%%22,%%22%f%%22)" % (
        layer_name, min_x, max_x, min_y, max_y)
    if '3857' in out_crs:
        req_url += '&outputCrs=http://www.opengis.net/def/crs/EPSG/0/3857'
    return coords_poly, layer_name, req_url


def reproject_coordinates(coordinates, inproj, outproj, flat=False):
    """
    Given a shapely polygon, reproject the polygon and return in a dictionary usable by rasterio downstream.
    This method iterates over all points within the polygon and reprojects them individually
    :param polygon: polygon to reproject
    :param inproj: input projection (pyproj Proj object)
    :param outproj: output projection (pyproj Proj object)
    :return: dictonary for use within rasterio's mask method
    """
    if flat:
        return np.array([transform(inproj, outproj, coord[0], coord[1]) for coord in coordinates]).flatten()
    return [list(transform(inproj, outproj, coord[0], coord[1])) for coord in coordinates]


def to_geojson(coords):
    return {"type": "Polygon", "coordinates": [coords]}

def color_image(image_type, masked_image):
    cm = colormaps.get(image_type)
    if image_type == 'NDWI':
        return cm(masked_image[0] + 1) * 255
    else:
        return cm(masked_image[0]) * 255