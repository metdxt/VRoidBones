import bpy

class VRoidBonesPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_vroid_panel"
    bl_label = "VRoid Bones"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    #bl_context = "armature_edit"

    def draw(self, context):
        big_box = self.layout.box()
        big_box.operator('bones.vroid_fix')
        big_box.operator('bones.vroid_ik')
        big_box.operator('bones.vroid_cleanup')