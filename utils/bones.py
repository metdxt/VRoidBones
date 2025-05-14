import re
from functools import lru_cache

import bpy
from mathutils import Vector
from .objects import get_children


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
    return not bone.constraints and not bone_has_effect(bone)

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
    '''Put tails of bones in chain to the head of child bone and connect them properly.'''
    # Regex patterns for identifying special bone types
    finger_last_re = re.compile(r"(?P<finger>Thumb|Index|Middle|Ring|Little)3_(?P<side>R|L)")
    toe_base_re = re.compile(r"ToeBase_(?P<side>L|R)")

    # Get all bones in current armature
    bones = bpy.context.active_object.data.edit_bones

    # List of bone names that should be excluded from automatic connection
    exceptions = ['Sleeve','Skirt','Bust','FaceEye','HairJoint','Tops','Food','Hood']

    # Mapping of limb bone prefixes to their natural child prefixes
    limb_hierarchy = {'UpperLeg':'LowerLeg','LowerLeg':'Foot','UpperArm':'LowerArm','LowerArm':'Hand'}

    def _get_target_child(bone):
        """Determine which child bone should be connected to the current bone."""
        # Skip processing for Head bone or bones without children
        if bone.name == "Head" or not bone.children:
            return None

        # Limb hierarchy handling - find matching child bone based on naming convention
        for prefix, child_prefix in limb_hierarchy.items():
            if bone.name.startswith(prefix):
                for child in bone.children:
                    if child.name.startswith(child_prefix):
                        return child
                return bone.children[0]  # Fallback to first child if no match

        # Default to first child when no special cases apply
        target = bone.children[0]

        # Handle cases where bone has multiple children
        if len(bone.children) > 1:
            for child in bone.children:
                # Skip children that match exception patterns
                if not any(ex in child.name for ex in exceptions):
                    target = child
                    break
                # Disconnect any exception bones
                child.use_connect = False
        return target

    def _process_bone_chain(bone):
        """Process an individual bone to connect it to its appropriate child."""
        target = _get_target_child(bone)
        if not target:
            return

        # Move current bone's tail to match target's head position
        bone.select_tail = True
        offset = target.head - bone.tail
        bpy.ops.transform.translate(value=offset)
        bone.select_tail = False

        # Special handling for root bone - adjust its tail downward
        if bone.name.lower() == 'root':
            bone.select_tail = True
            bpy.ops.transform.translate(value=(0, 0, -bone.length * 0.8))
            bone.select_tail = False
            return

        # Establish parent-child connection between bones
        bones.active = bone
        target.select = True
        bpy.ops.armature.parent_set(type='CONNECTED')
        bpy.ops.armature.select_all(action='DESELECT')

    def _adjust_special_bones():
        """Apply special adjustments to finger and toe bones."""
        for bone in bones:
            # Only process bones with exactly one child
            if len(bone.children) != 1:
                continue

            child = bone.children[0]
            # Adjust finger tip bones to extend in same direction as parent
            if finger_last_re.match(child.name):
                direction = (bone.tail - bone.head).normalized()
                child.tail = child.head + direction * child.length
            # Adjust toe base bones to extend horizontally from parent
            elif toe_base_re.match(child.name):
                direction = ((bone.tail - bone.head) * Vector((1.0, 1.0, 0.0))).normalized()
                child.tail = child.head + (direction * child.length) / 2

    # Main processing sequence
    bpy.ops.armature.select_all(action='DESELECT')  # Clear any existing selections
    for bone in bones:
        _process_bone_chain(bone)  # Process each bone in the armature
    _adjust_special_bones()  # Apply special adjustments to finger/toe bones



def clear_leaf_bones():
    junk_bones = set()
    for bone in bpy.context.active_object.data.edit_bones:
        if not bone.children and is_junk_bone(bone):
            junk_bones.add(bone.name)
    delete_bones_and_cleanup(junk_bones)
