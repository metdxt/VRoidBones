import bpy
from ..utils.bones import get_junk_bone_chain, delete_bones_and_cleanup

class VRoidCleanerOperator(bpy.types.Operator):
    '''Remove all bones that dont have effect'''
    bl_idname = "bones.vroid_cleanup"
    bl_label = "Clean skeleton"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'ARMATURE'

    def execute(self, context):
        mode = context.mode
        if mode != 'EDIT_ARMATURE':
            bpy.ops.object.editmode_toggle()

        junk_bones = set()
        for bone in context.active_object.data.edit_bones:
            print(f"Checking bone: {bone.name}")  # Debug
            chain = get_junk_bone_chain(bone)
            if chain:
                print(f"Marked as junk: {[b.name for b in chain]}")  # Debug
                junk_bones.update(b.name for b in chain)


        return {'FINISHED'}
