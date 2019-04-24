This repository is intended as an example of how quickly and easily it is to 
set up a Sentinel2 server for regional use cases (when data volume isn't really as issue)
but is large enough to justify downloading/caching the tiles (over partial reads of clips, for example)

It uses a DockerFile to wrap a simple django app (in hindsight, flash would have been
easier) and uses the [docker-geoserver](https://github.com/kartoza/docker-geoserver) image
to start geoserver. The demo (if still working) is hosted on a medium AWS instance.

![sample](sample.gif)

To do:

Add tests

Add more data
