"""
subpackages

inventories the latest github releases of all pysal subpackages

"""
import yaml
import os
import subprocess
import json
import zipfile
import sys


TARGETROOT ="pysal/"

def get_url(package):
    url = "https://api.github.com/repos/pysal/{}/releases/latest".format(package)
    cmd = "curl -s {}".format(url)
    info = subprocess.getoutput(cmd)
    return json.loads(info)['zipball_url']

def download_package(package):
    url = get_url(package)
    info = subprocess.getoutput("wget {}".format(url))
    return url.split("/")[-1]

def unpack(filename, pth='tmp/'):
    zf = zipfile.ZipFile(filename)
    zf.extractall(path=pth)
    return(zf)

def move(zf, package, pth='tmp/'):
    fd = zf.namelist()[0].split('/')[0]
    origin = os.path.join(pth, fd)
    destination = os.path.join(pth, package)
    os.remove(zf.filename)
    os.rename(origin, destination)

def grab_package(package):
    zf = unpack(download_package(package))
    move(zf, package)


with open('packages.yml') as package_file:
    packages = yaml.load(package_file)


def get_tags():

    versions = {}
    for package in packages:
        #print(package)
        subpackages = packages[package].split()
        for subpackage in subpackages:

            # get latest github release version number
            url = "https://api.github.com/repos/pysal/{}/releases/latest".format(subpackage)
            #print(url)
            cmd = "curl --silent \"{}\"".format(url)
            #print(cmd)
            cmd = "{} | grep -Po \'\"tag_name\": \"\\K.*?(?=\")\'".format(cmd)
            #print(cmd)
            tag = subprocess.getoutput(cmd)
            print("{}: {}".format(subpackage, tag))
            versions[subpackage] = tag
            grab_package(subpackage)
    return versions

