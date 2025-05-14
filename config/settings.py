import bpy


class VRoidSettings(bpy.types.PropertyGroup):
    bone_chains: bpy.props.BoolProperty(
        name="Fix bone chains",
        default=True,
        description="Connect bones in chains, i.e. arms, legs, fingers, etc..",
    )  # type: ignore
