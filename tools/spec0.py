"""spec 0
Tooling to check for compliance with spec 0 across the pysal ecosystem


Spec 0 recommends

- Support for Python versions be dropped 3 years after intial release
- Support for core package dependences be dropped 2 years after their initial
  release
"""

import pandas

tables = pandas.read_html("https://scientific-python.org/specs/spec-0000/")

# 25Q2 minimum dependencies
core = {'ipython': '8.15.0',
        'networkx': '3.2',
        'numpy': '1.26.0',
        'pandas': '2.1.0',
        'python': '3.11',
        'scikit-learn': '1.4.0',
        'scipy': '1.12.0',
        'xarray': '2023.7.0',
        'zarr': '2.16.0'
        }

