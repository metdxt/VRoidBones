import bpy
from .operators import *
from .config.settings import VRoidSettings
from .ui import VRoidBonesPanel

bl_info = {
    "name": "VRoid Bones",
    "description": "Make it pretty button for VRoid skeletons.",
    "author": "Crystal Melting Dot",
    "version": (1, 6),
    "blender": (2, 80, 0),
    "category": "Rigging",
    "tracker_url": "https://github.com/cmd410/VRoidBones/issues",
}

classes = [
    #VRoidSettings,
    VRoidCleanerOperator,
    VRoidFixChainsOperator,
    VRoidIKOperator,
    VRoidBonesPanel
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
