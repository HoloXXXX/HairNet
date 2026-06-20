# This class handles the creation of the 3d viewport side panel

import bpy
import webbrowser

from . import data

readme_url = 'https://github.com/HoloXXXX/HairNet/blob/master/README.md'

class HAIRNET_PT_view_panel(bpy.types.Panel):
    '''Handles the display of the hair net panel in the 3d viewport'''
    bl_label = 'Hair Net'
    bl_idname = 'HAIRNET_PT_view_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Hair Net'
    bl_context = 'objectmode'  

    def draw(self, context):
        
        data.update_hair_data() # I think this is the best place for this unfortunately :( Msg bus can't be used to update on selection. Maybe modal, but doesn't look like there's an apporpriate event

        layout = self.layout 

        # ADD TO EXISTING HAIR SYSTEM
        box = layout.box()
        row = box.row()
        row.prop(data.scene.hn_props, 'add_to_existing')

        # HAIR PARTICLE SYSTEM   
        if data.scene.hn_props.add_to_existing == False:
            row = box.row()
            row.label(text='Particle Settings:')
            row = box.row()
            row.prop_search(data.scene.hn_props, 'particle_settings',  bpy.data, 'particles', text='')

        # CONVERT TO PARTICLES BUTTON
        row = layout.row()
        row.scale_y = 2.0
        row.operator('hairnet.operator', text='Convert to Hair Particles')

        # HAIR SOURCE LABEL DISPLAY
        row = layout.row()
        row.label(text='Hair Source:')
        if data.hair_source is not None:
            row.label(text=data.hair_source.name)

        # HAIR OBJECT LIST
        split = layout.split()

        col = box.column()
        col = split.column()
        col.label(text = 'Guide Hairs:')

        col = split.column()
        for proxy_hair in data.proxy_hair_guides:
            col.label(text = proxy_hair.name)

        # VERSION / INFO
        vbox = layout.box()
        row = vbox.row()
        row.label(text= data.version, icon='PARTICLE_PATH')
        row.operator('hairnet_readme.operator', icon='QUESTION', text='')

class HAIRNET_OT_readme(bpy.types.Operator):
    bl_idname = 'hairnet_readme.operator'
    bl_label = 'Hair Net Readme Link'
    bl_description = 'Links to Hair Net readme.'

    def execute(self, context):

        webbrowser.open(readme_url, new = 0, autoraise = True)

        return {'FINISHED'}

def register():
    bpy.utils.register_class(HAIRNET_PT_view_panel)
    bpy.utils.register_class(HAIRNET_OT_readme)

def unregister():
    bpy.utils.unregister_class(HAIRNET_PT_view_panel)
    bpy.utils.unregister_class(HAIRNET_OT_readme)

