## wxpython in linux
https://stackoverflow.com/questions/29290011/using-travis-ci-with-wxpython-tests/45665364#45665364
```
language: python
python:
  - "3.5.3"

addons:
  apt:
    packages:
    - libwebkitgtk-dev
    - libjpeg-dev
    - libtiff-dev
    - libgtk2.0-dev
    - libsdl1.2-dev
    - libgstreamer-plugins-base0.10-dev
    - freeglut3
    - freeglut3-dev
    - libnotify-dev

# command to install dependencies
install: 
  - sudo apt-get update
  - wget "https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-14.04/wxPython-4.0.0b1-cp35-cp35m-linux_x86_64.whl"
  - pip install wxPython-4.0.0b1-cp35-cp35m-linux_x86_64.whl 

script: nosetests -v --with-id  --with-coverage --with-html --cover-package=./
```
https://extras.wxpython.org/wxPython4/extras/linux/
https://wxpython.org/Phoenix/snapshot-builds/linux