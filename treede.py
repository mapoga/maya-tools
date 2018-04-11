import os.path
import re
import pymel.core as pm


SHAPE_ATTR = ['horizontalFilmAperture',
              'verticalFilmAperture',
              'focalLength',
              'lensSqueezeRatio',
              'fStop',
              'focusDistance',
              'shutterAngle',
              'centerOfInterest',
              'aiUseGlobalShutter',
              'aiEnableDOF',
              'motionBlurOverride',
              'horizontalFilmOffset',
              'verticalFilmOffset',
              'filmFit',
              'overscan',]


def ls_shape(lst, shape_type):
    """ Returns a list of shapes from transform filtered by type """
    shapes = []
    for s in lst:
        rel = pm.listRelatives(s, type=shape_type, children=True)
        for r in rel:
            shapes.append(r)
    return shapes


def get_attr_values_dict(node, attr_list):
    """ Returns dict of (attr, value) pair """
    attrs = {}
    for a in attr_list:
        attr_str = '.'.join([node.longName(), a])
        try:
            attrs[a] = pm.getAttr(attr_str)
        except:
            'Error: Could not get attr: {0}'.format(attr_str)
    return attrs


def set_attr_values(node, attrs):
    """ Sets values from dict of (attr, value) pair """
    for key, val in attrs.items():
        attr_str = '.'.join([node.longName(), key])
        try:
            node.setAttr(attr_str, val)
        except:
            'Error: Could not set attr: {0}'.format(attr_str)


def make_camera(parent, cams_attr, over_x, over_y):
    time = pm.currentTime()
    if len(cams_attr):
        trans, cam = pm.camera()
        image_planes = []
        for idx, attrs in enumerate(cams_attr):
            frame = idx+1
            pm.setCurrentTime(frame)
            # trans
            matrix = attrs['matrix']
            pm.xform(trans, matrix=matrix, worldSpace=True)
            pm.setKeyframe(trans)
            # camera
            for key, val in attrs['shape'].items():
                if key == 'horizontalFilmAperture':
                    val = val * over_x
                elif key == 'verticalFilmAperture':
                    val = val * over_y
                pm.setKeyframe(cam, v=val, attribute=key)
            # image planes
            image_planes.extend(attrs['image_planes'])
        if image_planes:
            ip = image_planes[0]
            fp = pm.getAttr('.'.join([ip.longName(), 'imageName']))
            img_trs, img_shp = pm.imagePlane(camera=cam, fileName=fp)
            # frames
            filename = os.path.basename(fp)
            pattern = r'(\d+)'
            matchObjs = re.findall(pattern, filename)
            if matchObjs:
                pm.setAttr('.'.join([img_shp.longName(),
                                     'useFrameExtension']), True)
                frame = matchObjs[-1]
                print(frame)
                pm.setAttr('.'.join([img_shp.longName(),
                                     'frameOffset']), + int(frame) - 1)
                offsetX = pm.getAttr('.'.join([ip.longName(), 'offsetX']))
                offsetY = pm.getAttr('.'.join([ip.longName(), 'offsetY']))
                pm.setAttr('.'.join([img_shp.longName(),
                                     'offsetX']), offsetX)
                pm.setAttr('.'.join([img_shp.longName(),
                                     'offsetY']), offsetY)

        # lock attributes
        for key in cams_attr[0]['shape'].keys():
            pm.setAttr('.'.join([cam.longName(), key]), l=True)

        trans_attr = pm.listAttr(trans, keyable=True)
        for t in trans_attr:
            pm.setAttr('.'.join([trans.longName(), t]), l=True)




def cameras_to_frames(over_fact_x=1, over_fact_y=1):
    sel = pm.ls(selection=True)
    cams = ls_shape(sel, 'camera')
    cams.sort()
    cams_attr = []
    parent = None
    for c in cams:
        shape = c
        trans = pm.listRelatives(c, parent=True)[0]
        p = pm.listRelatives(c, parent=True)
        if p:
            parent = p
        cam_data = get_attr_values_dict(shape, SHAPE_ATTR)
        matrix = pm.xform(trans, matrix=True, worldSpace=True, query=True)
        image_planes = pm.listConnections(shape, shapes=True,
                                          type='imagePlane')
        cams_attr.append({'shape': cam_data,
                          'matrix': matrix,
                          'image_planes': image_planes})

    make_camera(parent, cams_attr, over_fact_x, over_fact_y)
