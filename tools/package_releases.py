"""
Grab most recent releases tagged on Github for PySAL subpackages


TODO
 - parse the highlights for each release and build up change log highlights for meta
 - build up detailed changes for meta
 - decide if this becomes a workflow
 - consider cron logic to handle release candidate sequence (1-4)
 - consolidate common tooling from releases.py and pakcage_releases.py

"""
import json
import os
import re
import subprocess
import urllib
from datetime import datetime, timedelta
from urllib.request import urlopen

import pandas
import requests
import yaml

packages = [
    "access",
    "esda",
    "giddy",
    "inequality",
    "libpysal",
    "mapclassify",
    "mgwr",
    "momepy",
    "pointpats",
    "segregation",
    "spaghetti",
    "spglm",
    "spint",
    "splot",
    "spopt",
    "spreg",
    "spvcm",
    "tobler",
]


def get_releases():
    """Return information on all pysal package releases.


    Returns
    -------
    dfs : pandas DataFrame
    """
    dfs = {}
    logs = {}
    for package in packages:
        fout = f"{package}.txt"
        cmd = f"gh release list -R pysal/{package} > {fout}"
        print(cmd)
        subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
            check=True,
        )
        df = pandas.read_csv(
            fout, sep="\t", header=None, names=["Name", "Type", "Label", "Date"]
        )
        df["Date"] = pandas.to_datetime(df["Date"])

        dfs[package] = df

        # gh release view -R pysal/segregation
        logfile = f"{package}.chglog"
        cmd = f"gh release view -R pysal/{package} > {logfile}"
        subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
            check=True,
        )
        with open(logfile, "r") as lf:
            logs[package] = lf.read()
    dfs = pandas.concat(dfs)
    dfs = dfs.reset_index()
    dfs.rename(columns={"level_0": "Package"}, inplace=True)
    return dfs


def releases_since_date(date_string, df, exclude=["r"]):
    """Return releases since a specified date.

    Parameters
    ----------
    date_string : str
                Date to filter releases by
    df : DataFrame
          See get_releases
    exclude : list
          Exclude any release with a name containing specified strings

    Returns
    -------
    df : DataFrame
    """
    for token in exclude:
        dfs = df[~ds.Label.str.contains(token)]
    date_string = pandas.to_datetime(date_string).tz_localize("UTC")
    return df[df["Date"] >= date_string]
