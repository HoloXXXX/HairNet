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
        self.headObj = context.object


        #Get a list of hair objects
        self.hairObjList = context.selected_objects
        if self.headObj in self.hairObjList:
            self.hairObjList.remove(self.headObj)

        layout = self.layout

        row = layout.row()
        #row.label(text = "Objects Start here")

        '''Is this a hair object?'''

        row = layout.row()
        try:
            row.prop(self.headObj.hn_cfg, 'isEmitter', text = "Emit Hair on Self")
        except:
            pass

        #Draw this if this is a head object
        if not self.headObj.hn_cfg.isEmitter:
            box = layout.box()
            row = box.row()
            row.label(text = "Hair Object:")
            row.label(text = "Use Settings:")
            for thisHairObject in self.hairObjList:
                config=thisHairObject.hn_cfg
                row = box.row()
                row.prop_search(config, 'masterHairSystem',  bpy.data, "particles", text = thisHairObject.name)
                row = box.row()
                row.label(text = "Add Guides:")
                row.prop(config, 'sproutHairs', text = "SubD")
#                 row.prop(thisHairObject, 'hnSubdivideHairSections', text = "Subdivide V")

        #Draw this if it's a self-emitter object
        else:
            box = layout.box()
            try:
                row = box.row()
                row.label(text = "Use Settings")
                
                row = box.row()
                row.prop_search(self.headObj.hn_cfg, 'masterHairSystem',  bpy.data, "particles", text = self.headObj.name)

            except:
                pass
            row = box.row()
            row.label(text = "Guide Subdivisions:")
            row.prop(self.headObj.hn_cfg, 'sproutHairs', text = "SubD")

def register():
    bpy.utils.register_class(HAIRNET_PT_view_panel)

def unregister():
    bpy.utils.unregister_class(HAIRNET_PT_view_panel)

