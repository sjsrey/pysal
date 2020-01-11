import yaml
import os
import subprocess
import sys
import json

# TARGETROOT ="pysal/"

os.system("rm pysal/*.py")
os.system("rm -rf notebooks")

with open("packages.yml") as package_file:
    packages = yaml.load(package_file)

# only tagged packages go in release
with open("tags.json") as tag_file:
    tags = json.load(tag_file)

tagged = list(tags.keys())

print(tagged)

com = "mkdir notebooks"
os.system(com)

for package in packages:
    com = f"rm -fr pysal/{package}"
    os.system(com)
    com = f"mkdir pysal/{package}"
    os.system(com)
    com = f"mkdir notebooks/{package}"
    os.system(com)

    subpackages = packages[package].split()
    for subpackage in subpackages:
        if subpackage == "libpysal":
            com = f"cp -rf tmp/{subpackage}/{subpackage}/*  pysal/{package}/"
        else:
            com = f"cp -rf tmp/{subpackage}/{subpackage} "\
                  f"pysal/{package}/{subpackage}"
        if subpackage in tagged:
            print(com)
            os.system(com)
        else:
            print("skipping: ", subpackage)

        #############
        # notebooks #
        #############
        com = f"mkdir notebooks/{package}/{subpackage}"
        os.system(com)
        com = f"cp -rf tmp/{subpackage}/notebooks/* "\
              f"notebooks/{package}/{subpackage}/"
        os.system(com)

###################
# Rewrite Imports #
###################
cache = {}


def replace(targets, string, replacement, update_cache=True):

    c = f"find {targets} -name '*.py' -print | xargs sed -i -- "\
        f"'s/{string}/{replacement}/g'"
    if update_cache:
        if targets in cache:
            cache[targets].append([string, replacement])
        else:
            cache[targets] = [[string, replacement]]
    os.system(c)


replace("pysal/.", "libpysal", "pysal\.lib")
replace("pysal/explore/.", "esda", "pysal\.explore\.esda")
replace("pysal/viz/mapclassify/.", "mapclassify", "pysal\.viz\.mapclassify")
replace("pysal/explore/.", "mapclassify", "pysal\.viz\.mapclassify")
replace("pysal/.", "pysal\.spreg", "pysal\.model\.spreg")
replace("pysal/model/spglm/.", "spreg\.", "pysal\.model\.spreg\.")
replace("pysal/model/spglm/.", "from spreg import", "from pysal\.model\.spreg import")
replace("pysal/model/spint/.", "from spreg import", "from pysal\.model\.spreg import")
replace("pysal/model/spint/.", " spreg\.", " pysal\.model\.spreg\.")
replace(
    "pysal/model/spglm/.",
    "import spreg\.user_output as USER",
    "from pysal\.model\.spreg import user_output as USER",
)
replace(
    "pysal/model/spglm/.",
    "import pysal\.model\.spreg\.user_output as USER",
    "from pysal\.model\.spreg import user_output as USER",
)
replace(
    "pysal/model/spint/.",
    "import pysal\.model\.spreg\.user_output as USER",
    "from pysal\.model\.spreg import user_output as USER",
)
replace(
    "pysal/model/mgwr/.",
    "import pysal\.model\.spreg\.user_output as USER",
    "from pysal\.model\.spreg import user_output as USER",
)
replace("pysal/.", "spglm", "pysal\.model\.spglm")
replace("pysal/.", "spvcm", "pysal\.model\.spvcm")
replace("pysal/model/spvcm/.", "def test_val", "\@ut\.skip\\n    def test_val")
replace("pysal/model/spvcm/.", "from spreg", "from pysal\.model\.spreg")
replace("pysal/.", " giddy\.api", "pysal\.explore\.giddy\.api")
replace("pysal/.", "import giddy", "import pysal\.explore\.giddy")
replace("pysal/.", "from giddy", "from pysal\.explore\.giddy")
replace(
    "pysal/explore/giddy/tests/.",
    "class Rose_Tester",
    '@unittest\.skip("skipping")\\nclass Rose_Tester',
)
replace("pysal/model/mgwr/.", "pysal\.open", "pysal\.lib\.open")
replace("pysal/model/mgwr/.", "pysal\.examples", "pysal\.lib\.examples")
replace("pysal/model/spreg/.", "from spreg", "from pysal\.model\.spreg")
replace("pysal/model/spreg/.", "import spreg", "import pysal\.model\.spreg")
replace("pysal/model/spreg/.", " spreg", " pysal\.model\.spreg")
replace("pysal/model/spvcm/.", "pysal\.examples", "pysal\.lib\.examples")
replace("pysal/model/spvcm/.", "pysal\.queen", "pysal\.lib\.weights\.user\.queen")
replace(
    "pysal/model/spvcm/.", "pysal\.w_subset", "pysal\.lib\.weights\.Wsets\.w_subset"
)
replace("pysal/viz/splot/.", "from splot\.libpysal", "from pysal\.viz\.splot\.libpysal")
replace("pysal/viz/splot/.", "from splot\.bk", "from pysal\.viz\.splot\.bk")
replace(
    "pysal/viz/splot/.",
    "from pysal\.viz\.splot\.pysal\.explore\.esda",
    "from pysal\.viz\.splot\.esda",
)
replace(
    "pysal/viz/splot/.",
    "from splot\.pysal\.explore\.esda",
    "from pysal\.viz\.splot\.pysal\.explore\.esda",
)


# for giddy and splot mapclassify breakage

old_new = {"Box_Plot": "BoxPlot",
           "Equal_Interval": "EqualInterval",
           "Fisher_Jenks": "FisherJenks",
           "Jenks_Caspall": "JenksCaspall",
           "JenksCaspall_Forced": "JenksCaspallForced",
           "Max_P_Classifier": "MaxP",
           "Maximum_Breaks": "MaximumBreaks",
           "Natural_Breaks": "NaturalBreaks",
           "Std_Mean": "StdMean",
           "User_Defined": "UserDefined",
           "HeadTail_Breaks": "HeadTailBreaks"
}

for old, new in old_new.items():
    replace("pysal/viz/splot", old, new)
    replace("pysal/explore/giddy", old, new)



replace("pysal/viz/splot/.", "import pysal as ps", "import pysal")
replace("pysal/viz/splot/.", "ps\.spreg", "pysal\.model\.spreg")
replace(
    "pysal/viz/splot/.",
    "ps\.lag_spatial",
    "pysal\.lib\.weights\.spatial_lag\.lag_spatial",
)
replace("pysal/viz/splot/.", "from esda", "from pysal\.explore\.esda")
replace("pysal/viz/splot/.", "import esda", "import pysal\.explore\.esda as esda")
replace(
    "pysal/viz/splot/.", "import pysal\.esda", "import pysal\.explore\.esda as esda"
)
replace("pysal/viz/splot/.", "from splot\.esda", "from pysal\.viz\.splot\.esda")
replace("pysal/viz/splot/.", "from spreg", "from pysal\.model\.spreg")
replace(
    "pysal/viz/splot/.", "from splot\.pysal\.lib", "from pysal\.viz\.splot\.libpysal"
)
replace("pysal/viz/splot/.", "from splot\.giddy", "from pysal\.viz\.splot\.giddy")
replace("pysal/viz/splot/.", "_viz_pysal\.lib_mpl", "_viz_libpysal_mpl")
replace("pysal/viz/splot/.", "import mapclassify", "import pysal\.viz\.mapclassify")
replace("pysal/viz/splot/.", "from splot\.mapping", "from pysal\.viz\.splot\.mapping")
replace("pysal/viz/splot/.", "from splot\._", "from pysal\.viz\.splot\._")
replace("pysal/viz/splot/.", "import spreg", "from pysal\.model import spreg")
replace(
    "pysal/explore/inequality/.", "from inequality", "from pysal\.explore\.inequality"
)
replace("pysal/model/mgwr/.", "from spreg", "from pysal\.model\.spreg")
replace("pysal/model/mgwr/.", "import spreg", "import pysal\.model\.spreg")
replace("pysal/explore/spaghetti/.", "from spaghetti", "from pysal\.explore\.spaghetti")
replace(
    "pysal/explore/spaghetti/.", "import spaghetti", "import pysal\.explore\.spaghetti"
)
replace("pysal/explore/spaghetti/tests/test_network_api.py",
        "import pysal\.explore\.spaghetti",
        "from  pysal\.explore import spaghetti")

replace(
    "pysal/explore/segregation/.",
    "from segregation",
    "from pysal\.explore\.segregation",
)
replace(
    "pysal/explore/segregation/.",
    "import segregation",
    "import pysal\.explore\.segregation",
)
replace("pysal/explore/segregation/.", "w_pysal\.lib", "w_libpysal")

# tobler
replace("pysal/model/tobler/.", "import tobler",
        "import pysal\.model import tobler")
replace("pysal/model/tobler/.", "from tobler",
        "from pysal\.model\.tobler")



#####################
# Rewrite notebooks #
#####################


with open("packages.yml") as package_file:
    packages = yaml.load(package_file)


mappings = []
for package in ["explore", "viz", "model"]:
    for subpackage in packages[package].split():
        left = f"from {subpackage}"
        right = f"from pysal\.{package}\.{subpackage}"
        mappings.append([left, right])
        left = f"import {subpackage}"
        right = f"from pysal\.{package} import {subpackage}"
        mappings.append([left, right])
        left = "libpysal"
        right = "pysal\.lib"
        mappings.append([left, right])


def replace_nb(targets, string, replacement, update_cache=True):
    c = f"find {targets} -type f -print0 | xargs -0 sed -i -- " \
        f"'s/{string}/{replacement}/g'"
    os.system(c)


for package in ["explore", "viz", "model"]:
    for subpackage in packages[package].split():
        targets = f'notebooks/{package}/{subpackage}'
        for mapping in mappings:
            left, right = mapping
            replace_nb(targets, left, right)

# should automate version bump
# or take an arg

init_lines = ["__version__='2.1.0rc'"]
for package in packages:
    os.system(f'touch pysal/{package}/__init__.py')
    subpackages = packages[package].split()
    if package == "lib":
        pass
    else:
        subpackage_lines = [f'from . import {s}' for s in subpackages]
        with open(f'pysal/{package}/__init__.py', 'w') as f:
            f.write("\n".join(subpackage_lines))
    init_lines.append(f'from . import {package}')

lines = "\n".join(init_lines)

with open("pysal/__init__.py", "w") as outfile:
    outfile.write(lines)
