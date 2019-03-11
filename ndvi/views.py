import base64
import json
import os
import uuid
from io import BytesIO
from urllib.request import urlretrieve

import numpy as np
import numpy.ma as ma
import rasterio as rio
import requests
from PIL import Image
from django.http import HttpResponse
from matplotlib import cm
from pyproj import transform, Proj
from rasterio import mask
# Create your views here.
from rest_framework import status
from rest_framework.generics import GenericAPIView
from shapely.geometry import Polygon


class ListLayersView(GenericAPIView):
    def get(self, request, *args, **kwargs):
        layers_url = 'http://127.0.0.1:8600/geoserver/rest/layers/'
        layers_on_server = requests.get(layers_url, auth=('admin', 'geoserver')).json()
        layer_names = [i['name'] for i in layers_on_server['layers']['layer'] if 'greece' in i['name']]
        return HttpResponse(json.dumps(layer_names))

class NDVIView(GenericAPIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        layer_name = data['properties']['layer_name']
        feature = data['geometry']
        poly = Polygon(feature['coordinates'][0])
        coords_poly = reproject_coordinates(feature['coordinates'][0], Proj(init='EPSG:4326'), Proj(init='EPSG:3857'))
        coords = [[poly.bounds[0], poly.bounds[1]], [poly.bounds[2], poly.bounds[3]]]
        min_x, min_y, max_x, max_y = reproject_coordinates(coords, Proj(init='EPSG:4326'), Proj(init='EPSG:32634'),
                                                           flat=True)
        req_url = 'http://127.0.0.1:8600/geoserver/wcs?service=WCS&version=2.0.1&request=getcoverage&coverageid=%s&subset=E(%%22%f%%22,%%22%f%%22)&subset=N(%%22%f%%22,%%22%f%%22)&outputCrs=http://www.opengis.net/def/crs/EPSG/0/3857' % (
            layer_name, min_x, max_x, min_y, max_y)
        print(req_url)
        fname = str(uuid.uuid4())
        urlretrieve(req_url, filename='%s.tif' % fname)
        with rio.open("%s.tif" % fname) as src:
            out_image, out_transform = mask.mask(src, [to_geojson(coords_poly)],
                                                 crop=False, nodata=-9999)
            masked_image = ma.masked_equal(out_image, -9999)
        bounds2 = [[out_transform[2], out_transform[5]], [out_transform[2] + out_transform[0] * out_image.shape[2], out_transform[5] + out_image.shape[1] * out_transform[4]]]
        print(coords)
        min_x2, min_y2, max_x2, max_y2 = reproject_coordinates(bounds2, Proj(init='EPSG:3857'), Proj(init='EPSG:4326'),
                                                           flat=True)
        bounds = ((min_y2, min_x2), (max_y2, max_x2))
        print(bounds)
        sio = BytesIO()
        im = Image.fromarray(np.uint8(cm.Greens(masked_image[0]) * 255))
        im.save(sio, 'png')
        sio.seek(0)
        os.remove('%s.tif' % fname)
        return HttpResponse(json.dumps({'image': base64.b64encode(sio.read()).decode(), 'bounds': json.dumps(bounds)}))


class NDVIStatsView(GenericAPIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        print(data)
        layer_name = data['properties']['layer_name']
        feature = data['geometry']
        poly = Polygon(feature['coordinates'][0])
        coords_poly = reproject_coordinates(feature['coordinates'][0], Proj(init='EPSG:4326'), Proj(init='EPSG:32634'))
        coords = [[poly.bounds[0], poly.bounds[1]], [poly.bounds[2], poly.bounds[3]]]
        min_x, min_y, max_x, max_y = reproject_coordinates(coords, Proj(init='EPSG:4326'), Proj(init='EPSG:32634'),
                                                           flat=True)
        req_url = "http://127.0.0.1:8600/geoserver/wcs?service=WCS&version=2.0.1&request=getcoverage&coverageid=%s&subset=E(%%22%f%%22,%%22%f%%22)&subset=N(%%22%f%%22,%%22%f%%22)" % (
            layer_name, min_x, max_x, min_y, max_y)
        fname = str(uuid.uuid4())
        try:
            urlretrieve(req_url, filename='%s.tif' % fname)
        except:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND)
        with rio.open("%s.tif" % fname) as src:
            out_image, out_transform = mask.mask(src, [to_geojson(coords_poly)],
                                                 crop=True, nodata=-9999)
            masked_image = ma.masked_equal(out_image, -9999)
        os.remove('%s.tif' % fname)
        return HttpResponse(json.dumps({'Date': layer_name.split(':')[1], 'Mean NDVI': str(masked_image.mean()),
                                        'Median NDVI': str(ma.median(masked_image))}))


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

