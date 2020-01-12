import pytest
from pysal.model.tobler.data import store_rasters


@pytest.mark.slow
def test_raster_download():
    store_rasters()
