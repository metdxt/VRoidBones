import bpy

from ..utils.constraints import setup_ik

class VRoidIKOperator(bpy.types.Operator):
    '''Auto setup inverse kinematics for arms and legs'''
    bl_idname = "bones.vroid_ik"
    bl_label = "Setup IK"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'ARMATURE'

    def execute(self, context):
        mode = context.mode
        if mode != 'EDIT_ARMATURE':
            bpy.ops.object.editmode_toggle()
        
        setup_ik()

        if mode != 'EDIT_ARMATURE':
            bpy.ops.object.editmode_toggle()
        self.report({'INFO'}, 'IK was setup!')
        return {'FINISHED'}