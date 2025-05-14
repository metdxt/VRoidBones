import re
from functools import lru_cache

import bpy
from mathutils import Vector
from .objects import get_children

@lru_cache
def bone_has_effect(bone):
    '''Check if bone has vertex groups attached to it'''
    armature = bpy.context.object
    children = get_children(armature)
    for obj in children:
        if not hasattr(obj, 'vertex_groups'):
            continue
        vg = obj.vertex_groups.get(bone.name)
        if vg is None:
            continue
        # Check if any vertex has non-zero weight for this group
        for vertex in obj.data.vertices:
            for group in vertex.groups:
                if group.group == vg.index and group.weight > 0.001:
                    return True
    return False



def is_junk_bone(bone):
    """Check if a bone is useless."""
    return not bone_has_effect(bone)

def get_junk_bone_chain(bone) -> list:
    """Recursively collect bones in a chain if all are junk."""
    im_junk = is_junk_bone(bone)
    if not bone.children:
        return [bone] if im_junk else []

    collected_junk = []
    all_children_junk = True
    for child in bone.children:
        child_junk = get_junk_bone_chain(child)
        collected_junk.extend(child_junk)
        if not child_junk:  # If any child isn't junk
            all_children_junk = False

    if im_junk and all_children_junk:
        collected_junk.append(bone)

    return collected_junk


def delete_bones_and_cleanup(bone_names):
    """Delete selected bones and clean up vertex groups."""
    bpy.ops.armature.select_all(action='DESELECT')
    for name in bone_names:
        bone = bpy.context.active_object.data.edit_bones.get(name)
        if bone:
            bone.select = True
    bpy.ops.armature.delete()

    # Cleanup vertex groups
    armature = bpy.context.object
    for obj in get_children(armature):
        for name in bone_names:
            vg = obj.vertex_groups.get(name)
            if vg:
                obj.vertex_groups.remove(vg)

def simplify_symmetrize_names():
    '''Rename bones to blenders armature symmetry names'''
    j_sec_regex = re.compile(r"J_Sec_((?P<side>R|L)_)?(?P<name>[a-zA-Z]+)(?P<order>\d{1,2})?_(?P<leaf>end_)?(?P<id>\d{2})")
    j_bip_regex = re.compile(r"J_Bip_(?P<side>R|L|C)_(?P<name>\w+)")
    bones = bpy.context.active_object.data.edit_bones
    n = 1
    vg_remap = dict()
    for bone in bones[:]:
        original_name = bone.name
        if (rematch := j_sec_regex.match(bone.name)):
            name = rematch.group('name')
            id = rematch.group('id')
            order = rematch.group('order')
            order = f"_{order}" if order else ""
            side = rematch.group("side")
            side = f"_{side}" if side else ""
            vg_remap[original_name] = bone.name

            bone.name = f'{name}{id}{order}{side}'
            n += 1
        elif (rematch := j_bip_regex.match(bone.name)):
            name = rematch.group('name')
            side = rematch.group('side')
            side = f'_{side}' if side != 'C' else ''
            bone.name = f'{name}{side}'
            vg_remap[original_name] = bone.name


    # Need to make sure all vertex groups are properly renamed
    # they are not renamed automaticaly all the times for some reason
    armature = bpy.context.object
    children = get_children(armature)
    for obj in children:
        vgs = obj.vertex_groups
        for orig, new in vg_remap.items():
            group = vgs.get(orig)
            if group is not None:
                group.name = new


def fix_bones_chains():
    '''Put tails of bones in chain to the head of child bone
       And connect them properly...'''

    finger_last_re = re.compile(r"(?P<finger>Thumb|Index|Middle|Ring|Little)3_(?P<side>R|L)")
    toe_base_re = re.compile(r"ToeBase_(?P<side>L|R)")

    def disconnect_child(bone):
        bone.use_connect = False

    bpy.ops.armature.select_all(action='DESELECT')
    bones = bpy.context.active_object.data.edit_bones
    exceptions = ['Sleeve','Skirt','Bust','FaceEye',
                  'HairJoint', 'Tops', 'Food', 'Hood']

    limb_hierarchy = {
        'UpperLeg': 'LowerLeg',
        'LowerLeg': 'Foot',
        'UpperArm': 'LowerArm',
        'LowerArm': 'Hand'
    }

    for bone in bones:
        children = bone.children
        if not children:
            continue
        if bone.name == "Head":
            continue
        # Check if this bone is part of a limb hierarchy
        is_limb_bone = False
        expected_child = None
        for prefix in limb_hierarchy:
            if bone.name.startswith(prefix):
                expected_child = limb_hierarchy[prefix]
                is_limb_bone = True
                break

        target = None
        if is_limb_bone:
            # First try to find the expected child bone
            for child in children:
                if child.name.startswith(expected_child):
                    target = child
                    break
            # If not found, proceed with normal selection
            if not target:
                target = children[0]
        else:
            target = children[0]

        # Skip if we couldn't find a target
        if not target:
            continue

        # Handle cases where there are multiple children
        if len(children) > 1 and not is_limb_bone:
            for candidate in children:
                valid = True
                for ex in exceptions:
                    if ex in candidate.name:
                        disconnect_child(candidate)
                        valid = False
                        break
                if valid:
                    target = candidate
                    break


        bone.select_tail = True
        offset = target.head - bone.tail
        bpy.ops.transform.translate(value=offset)
        bone.select_tail = False

        if bone.name.lower() == 'root':
            bone.select_tail = True
            bpy.ops.transform.translate(value=(0,0,-bone.length * 0.8))
            bone.select_tail = False
            continue

        # Connect bones
        bones.active = bone
        target.select = True
        bpy.ops.armature.parent_set(type='CONNECTED')
        bpy.ops.armature.select_all(action='DESELECT')

    for bone in bones:
        children = bone.children
        if len(children) != 1: continue
        if finger_last_re.match(children[0].name):
            # Fix last falangs of fingers being directed upwards
            direction = (bone.tail - bone.head).normalized()
            last_finger = children[0]
            length = last_finger.length
            finger_end = last_finger.head + (direction * length)
            last_finger.tail = finger_end
        elif toe_base_re.match(children[0].name):
            direction = ((bone.tail - bone.head) * Vector((1.0, 1.0, 0.0))).normalized()
            toe_base = children[0]
            length = toe_base.length
            toe_base_end = toe_base.head + (direction * length) / 2
            toe_base.tail = toe_base_end



def clear_leaf_bones():
    junk_bones = set()
    for bone in bpy.context.active_object.data.edit_bones:
        if not bone.children and is_junk_bone(bone):
            junk_bones.add(bone.name)
    delete_bones_and_cleanup(junk_bones)
