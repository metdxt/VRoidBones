import bpy
from ..utils.bones import simplify_symmetrize_names, fix_bones_chains, clear_leaf_bones

class VRoidFixChainsOperator(bpy.types.Operator):
    """Rename symmetrical VRoid bones to blender convention."""

    bl_idname = "bones.vroid_fix"
    bl_label = "Fix Armature"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'ARMATURE'

    def execute(self, context):
        mode = context.mode
        if mode != 'EDIT_ARMATURE':
            bpy.ops.object.editmode_toggle()
        
        simplify_symmetrize_names()
        fix_bones_chains()
        clear_leaf_bones()
        
        if mode != 'EDIT_ARMATURE':
            bpy.ops.object.editmode_toggle()
        
        self.report({"INFO"}, "Armature was fixed!")
        
        return {"FINISHED"}
