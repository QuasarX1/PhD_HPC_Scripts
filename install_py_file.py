# credit: https://stackoverflow.com/a/70032188

import setuptools
import sys
import os

build_folder_exists = os.path.exists("./build")
dist_folder_exists = os.path.exists("./dist")
pycache_folder_exists = os.path.exists("./__pycache__")

module_name = sys.argv[2].replace(".py", "")
sys.argv = sys.argv[:2]
setuptools.setup(name = module_name, py_modules = [module_name])

if not build_folder_exists:
    os.system("rm -rf build")
if not dist_folder_exists:
    os.system("rm -rf dist")
os.system(f"rm -rf {module_name}.egg-info")
if not pycache_folder_exists:
    os.system("rm -rf __pycache__")
