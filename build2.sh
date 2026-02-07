#!/bin/bash

rm -rf build/ dist/ safeeyes.egg-info/ .eggs/

python3 setup.py sdist bdist_wheel
# sajt. # twine upload --repository pypitest dist/safeeyes*.tar.gz
# sajt. # clear >$(tty)
# sajt. # twine upload --repository pypitest dist/safeeyes*.whl

read x;