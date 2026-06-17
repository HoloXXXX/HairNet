# This class handles the creation of the 3d viewport side panel

import bpy

from . import hairNet

versionString = "0.7.1"

class HAIRNET_PT_view_panel(bpy.types.Panel):
    bl_label = "Hair Net"
    bl_idname = "HAIRNET_PT_view_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Hair Net"
    bl_context = "objectmode"

    def draw(self, context):
        object = context.active_object
        if object is not None:
            self.drawButtons(self.layout)
            self.drawDetails(self.layout, context)
    
    def drawButtons(self, layout):
        col = layout.box().column(align = True)
        
        row = col.row(align = True)
        row.label(text="Make Hair")
        
        row = col.row()
        row.label(text ="Add Hair From:")
        
        row = col.row(align = True)
        for kind in hairNet.mesh_kinds:
            row = col.row(align = True)
            row.operator("hairnet.operator", text=kind[1]).meshKind=kind[0]
        

    def drawDetails(self, layout, context):
        self.hairSource = context.object
        print(self.hairSource)


        #Get a list of hair objects
        self.proxyHairObjects = context.selected_objects
        if self.hairSource in self.proxyHairObjects:
            self.proxyHairObjects.remove(self.hairSource)

        layout = self.layout

        row = layout.row()

        box = layout.box()
        row = box.row()
        row.label(text = "Hair Object:")
        row.label(text = "Use Settings:")
        for thisHairObject in self.proxyHairObjects:
            config=thisHairObject.hn_cfg
            row = box.row()
            row.prop_search(config, 'masterHairSystem',  bpy.data, "particles", text = thisHairObject.name)
            row = box.row()
            row.label(text = "Add Guides:")
            row.prop(config, 'sproutHairs', text = "SubD")

def register():
    bpy.utils.register_class(HAIRNET_PT_view_panel)

def unregister():
    bpy.utils.unregister_class(HAIRNET_PT_view_panel)

