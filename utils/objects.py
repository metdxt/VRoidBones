import bpy

def get_children(parent):
    if parent is None: return []
    l = []
    for obj in bpy.context.scene.objects:
        if obj.name == parent.name: continue
        if obj.parent is None: continue
        if obj.parent.name == parent.name:
            l.append(obj)
    return l