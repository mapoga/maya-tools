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
        return {'x': matchObj[0],
                'y': matchObj[1],
                'z': matchObj[2]
                }
    return


def _lookup_rot(string):
    pattern = r'\s(-*\d+\.*\d*)'

    matchObj = re.findall(pattern, string)
    if matchObj:
        return {'x': matchObj[3],
                'y': matchObj[4],
                'z': matchObj[5]
                }
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
                      'pos': {'x': 0,
                              'y': 0,
                              'z': 0},
                      'rot': {'x': 0,
                              'y': 0,
                              'z': 0}
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
