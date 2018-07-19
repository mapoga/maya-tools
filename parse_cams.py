import re


def _lookup_filename(string):
    pattern = r'(.+\.[a-zA-Z]+)'

    matchObj = re.search(pattern, string)
    if matchObj:
        return matchObj.group(1)
    return


def _lookup_pos(string):
    pattern = r'\s(-*\d+\.*\d*)'

    matchObj = re.findall(pattern, string)
    if matchObj:
        m = matchObj[0:3]
        return [float(i) for i in m]
    return


def _lookup_rot(string):
    pattern = r'\s(-*\d+\.*\d*)'

    matchObj = re.findall(pattern, string)
    if matchObj:
        m = matchObj[3:6]
        return [float(i) for i in m]
    return


def cams(filepath):

    # Open file
    try:
        file_ = open(filepath, 'r')
    except OSError as error:
        print('Error reading file: {0}'.format(error))
        file_.close()

    cameras = []
    camera_default = {'filename': '',
              'pos': [],
              'rot': []
              }

    # Lines loop
    for idx, line in enumerate(file_):
        camera = dict(camera_default)

        # filename
        fn = _lookup_filename(line)
        if fn:
            camera['filename'] = fn

        # pos
        pos = _lookup_pos(line)
        if pos:
            camera['pos'] = pos

        # rot
        rot = _lookup_rot(line)
        if rot:
            camera['rot'] = rot

        # End of file
        if fn and pos and rot:
            cameras.append(camera)
    file_.close()

    return cameras

"""
import maya.cmds as cmds
import os

c = cams(r'Z:\TMP\dump\antoine-haireyesopen.txt')
dir = 'wrong'
for i in c:
    print i['filename']
    print i['pos']
    print i['rot']
    cameraName = cmds.camera(name = i['filename'], position = i['pos'], rotation = i['rot'], focalLength = 24, horizontalFilmAperture = 1.5, verticalFilmAperture = 1)
    ip = cmds.imagePlane(camera = cameraName[0], fileName = os.path.join(dir, i['filename']), showInAllViews = False)
"""