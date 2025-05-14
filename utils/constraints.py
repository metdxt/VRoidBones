from itertools import product

import bpy

from ..config.ik_config import IK_CONFIG
from ..config.rotation_limits import ROTATION_LIMITS

FINGERS = ["Thumb", "Index", "Middle", "Ring", "Little"]


def unique_constraint(bone, t):
    for constraint in bone.constraints:
        if constraint.type == t:
            return constraint
    constraint = bone.constraints.new(type=t)
    return constraint


def get_pose_bone(bone_name):
    pose_bones = bpy.context.object.pose.bones
    bone = None
    if bone_name in pose_bones:
        bone = pose_bones[bone_name]
    elif "_" not in bone_name:
        for b in pose_bones:
            if b.name.endswith(f"_{bone_name}"):
                bone = b
                break
    else:
        name, side = bone_name.split("_")
        if side not in {"L", "R"}:
            for b in pose_bones:
                if b.name.endswith(f"_{name}"):
                    bone = b
                    break
        for b in pose_bones:
            if b.name.endswith(f"_{side}_{name}"):
                bone = b
                break
    return bone


def apply_edit_bones():
    bpy.ops.object.posemode_toggle()  # This lines needed to "apply" bones from edit mode
    bpy.ops.object.editmode_toggle()  # or else constraints won't appear for some reason


def setup_ik():
    apply_edit_bones()

    pose_bones = bpy.context.object.pose.bones
    for bone_name, params in IK_CONFIG.items():

        bone = get_pose_bone(bone_name)
        if bone is None:
            continue

        constraint = unique_constraint(bone, "IK")
        constraint.chain_count = params.get("chain_count", 0)

        bone.lock_ik_x = params.get("lock_ik_x", False)
        bone.lock_ik_y = params.get("lock_ik_y", False)
        bone.lock_ik_z = params.get("lock_ik_z", False)

        bone.use_ik_limit_x = params.get("use_ik_limit_x", False)
        bone.use_ik_limit_y = params.get("use_ik_limit_y", False)
        bone.use_ik_limit_z = params.get("use_ik_limit_z", False)

        bone.ik_max_x = params.get("ik_max_x", 3.14159)
        bone.ik_min_x = params.get("ik_min_x", -3.14159)
        bone.ik_max_y = params.get("ik_max_y", 3.14159)
        bone.ik_min_y = params.get("ik_min_y", -3.14159)
        bone.ik_max_z = params.get("ik_max_z", 3.14159)
        bone.ik_min_z = params.get("ik_min_z", -3.14159)


def add_finger_constraitns():
    apply_edit_bones()
    for finger, num, side in product(FINGERS, [2, 3], ["L", "R"]):
        bone = get_pose_bone(f"{finger}{num}_{side}")
        if bone is None:
            continue
        constraint = unique_constraint(bone, "COPY_ROTATION")
        constraint.target = bpy.context.object
        constraint.subtarget = bone.parent.name
        constraint.mix_mode = "ADD"
        constraint.target_space = "LOCAL"
        constraint.owner_space = "LOCAL"
        constraint.use_y = False
        if finger == "Thumb":
            constraint.use_x = False
        else:
            constraint.use_z = False


def add_rotation_limits():
    apply_edit_bones()
    for bone_name, params in ROTATION_LIMITS.items():
        if bone_name == "<fingers>":
            for finger, num, side in product(FINGERS, [1], ["L", "R"]):
                if finger == "Thumb":
                    continue
                bone = get_pose_bone(f"{finger}{num}_{side}")
                if bone is None:
                    continue
                constraint = unique_constraint(bone, "LIMIT_ROTATION")
                constraint.owner_space = "LOCAL"
                constraint.use_transform_limit = True
                for p_name, p_value in params.items():
                    setattr(constraint, p_name, p_value)
                    axis = p_name.split("_")[1]
                    setattr(constraint, f"use_limit_{axis}", True)
        bone = get_pose_bone(bone_name)
        if bone is None:
            continue
        constraint = unique_constraint(bone, "LIMIT_ROTATION")
        constraint.owner_space = "LOCAL"
        constraint.use_transform_limit = True
        for p_name, p_value in params.items():
            setattr(constraint, p_name, p_value)
            axis = p_name.split("_")[1]
            setattr(constraint, f"use_limit_{axis}", True)
