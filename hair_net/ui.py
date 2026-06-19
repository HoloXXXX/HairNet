# This class handles the creation of the 3d viewport side panel

import bpy

from . import data


class HAIRNET_PT_view_panel(bpy.types.Panel):
    '''Handles the display of the hair net panel in the 3d viewport'''
    bl_label = 'Hair Net'
    bl_idname = 'HAIRNET_PT_view_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Hair Net'
    bl_context = 'objectmode'  

    def draw(self, context):
        
        data.update_hair_data() # I think this is the best place for this unfortunately :( Msg bus can't be used to update on selection

        layout = self.layout 

        # HAIR SOURCE LABEL DISPLAY
        box = layout.box()
        row = box.row()
        row.label(text='Hair Source:')
        if data.hair_source is not None:
            row.label(text=data.hair_source.name)

        # HAIR PARTICLE SYSTEM   
        row = box.row()
        row.prop_search(data.scene.hn_props, 'hair_system',  bpy.data, 'particles')

        # ADD GUIDES PROPERTY
        row = box.row()
        row.label(text = 'Add Guides:')
        row.prop(data.scene.hn_props, 'additional_guides', text = 'SubD')

        # CONVERT TO PARTICLES BUTTON
        row = layout.row()
        row.scale_y = 2.0
        row.operator('hairnet.operator', text='Convert to Hair Particles')

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
        sub = row.row()
        sub.scale_x = .5
        sub.prop(data.scene.hn_props, 'info', text = '', icon='QUESTION')




def register():
    bpy.utils.register_class(HAIRNET_PT_view_panel)

def unregister():
    bpy.utils.unregister_class(HAIRNET_PT_view_panel)

