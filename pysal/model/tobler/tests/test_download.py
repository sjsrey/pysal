from pysal.model.tobler.data import store_rasters
import pytest


@pytest.mark.slow
def test_raster_download():
    store_rasters()
