"""
Grab most recent releases tagged on Github for PySAL subpackages

"""
import os
import json
import yaml
import requests
import tarfile

with open('packages.yml') as package_file:
    packages = yaml.load(package_file)

def get_release_info():
    """
    Get information about subpackage releases that have been tagged on github
    """
    no_release = []
    release = {} 

    for package in packages:
        subpackages = packages[package].split()
        for subpackage in subpackages:
            pkstr = "curl --silent \"https://api.github.com/repos/pysal/{subpackage}/releases/latest\"".format(subpackage=subpackage)
            result = os.popen(pkstr).read()
            d = json.loads(result)
            if 'message' in d:
                if d['message']== 'Not Found':
                    print("{subpackage} has no latest release".format(subpackage=subpackage))
                    no_release.append(subpackage)
                else:
                    print('Something else happened')
            else:
                #print("{subpackage} has a latest release".format(subpackage=subpackage))
                tag_name = d['tag_name']
                tarball_url = d['tarball_url']
                release[subpackage] = (tag_name, tarball_url)
                #print(tag_name)
                #print(tarball_url)

    """
    print("The following {count} packages have a git release:\n\t".format(count=len(release.keys())))
    print(release.keys())

    print("\n\nThe following {count} packages do not have a git release:\n\t".format(count=len(no_release)))
    print(no_release)
    """

    with open('tarballs.json', 'w') as fp:
        json.dump(release, fp)

    return release

def get_tarballs():
    """
    Grab tarballs for releases and put in a temporary directory for further processing
    """
    with open('tarballs.json', 'r') as infile:
        sources = json.load(infile)
    if os.path.exists('tarballs'):
        os.system('rm -rf tarballs')
    os.system('mkdir tarballs')
    if not os.path.exists('tmp'):
        os.makedirs('tmp')

    for subpackage in sources.keys():
        print(subpackage)
        url = sources[subpackage][-1]
        print(url)
        target = "tarballs/{pkg}.tar.gz".format(pkg=subpackage)
        print(target)
        resp = requests.get(url)
        with open(target, 'wb') as target_file:
            target_file.write(resp.content)
        tar = tarfile.open(target, "r:gz")
        members = tar.getmembers()
        path = members[0].path
        cmd = "tar xzvf tarballs/{pkg}.tar.gz".format(pkg=subpackage)
        print(cmd)
        os.system(cmd)
        cmd = "cp -R {path} tmp/{pkg}".format(path=path, pkg=subpackage)
        print(cmd)
        os.system(cmd)
        cmd = "rm -rf {path}".format(path=path)
        os.system(cmd)

    return sources

def clone_releases():
    """
    Clone the releases in tmp
    """
    with open('newtags.json', 'r') as file_name:
        sources = json.load(file_name)
    os.system('rm -rf tmp')
    os.system('mkdir tmp')
    for subpackage in sources.keys():
        tag = sources[subpackage]
        pkgstr = "git clone --branch {tag} ".format(tag=tag)
        pkgstr = "{pkgstr} https://github.com/pysal/{subpackage}.git".format(pkgstr=pkgstr,
                                                                             subpackage=subpackage)
        pkgstr = "{pkgstr} tmp/{subpackage}".format(pkgstr=pkgstr, subpackage=subpackage)

        print(pkgstr)
        os.system(pkgstr)

def get_tags():
    """
    Get the tags of the packages that are going into this releases
    """
    with open('subtags', 'r') as tag_name:
        tags = tag_name.readlines()

    pkgs = [tag.split() for tag in tags]

    tags = {}
    for pkg in pkgs:
        name, url = pkg
        tag = url.split("/")[-1]
        tags[name] = tag

    with open('tags.json', 'w') as fp:
        json.dump(tags, fp)

    # check if there have been updated releases and alert if so
    releases = get_release_info()
    new_tags = dict([(key,releases[key][0]) for key in releases])
    with open('newtags.json', 'w') as fp:
        json.dump(new_tags, fp)
    

    new_releases = []
    for package in new_tags:
        new_tag = new_tags[package]
        old_tag = tags[package]
        if new_tag != old_tag:
            new_releases.append([package, new_tag, old_tag])
    if new_releases:
        print("There are more recent releases to consider:\n\n")
        for release in new_releases:
            package, new_tag, old_tag = release
            print(package, new_tag, old_tag)
        print("\n\n Be sure to update the file subtags in the next release.")

    return tags


if __name__ == "__main__":
    get_tags()
    clone_releases()
