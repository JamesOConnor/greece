This repository is intended as an example of how quickly and easily it is to 
set up a Sentinel2 server for regional use cases (when data volume isn't really as issue)
but is large enough to justify downloading/caching the tiles (over partial reads from s3 using gdal, for example).

It uses a DockerFile to wrap a simple django app (in hindsight, flask would have been
easier) and uses the [docker-geoserver](https://github.com/kartoza/docker-geoserver) image
to start geoserver without any setup. The demo (if still working) is hosted on a medium AWS instance.

![sample](sample.gif)

To do:

Add tests

Add more data
