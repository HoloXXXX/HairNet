# This class handles the creation of the 3d viewport side panel

import bpy

from . import hair_net


class HAIRNET_PT_view_panel(bpy.types.Panel):
    '''Handles the display of the hair net panel in the 3d viewport'''
    bl_label = 'Hair Net'
    bl_idname = 'HAIRNET_PT_view_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Hair Net'
    bl_context = 'objectmode'
    hair_source = None
    proxy_hair_guides = None
    scene = None

    def update_selected_hair(self, context):
        '''Splits the current selection into a list of hair objects to be turned into particle hair, and the object that will host the particle system'''
        self.scene = context.scene
        
        self.hair_source = context.active_object
        
        self.proxy_hair_guides = [ obj for obj in context.selected_objects if obj is not self.hair_source]

    def draw(self, context):
        self.update_selected_hair(context)

        self.draw_core(self.layout)
    
    def draw_core(self, layout):
        layout = self.layout 

        # HAIR SOURCE LABEL DISPLAY
        box = layout.box()        
        row = box.row()
        row.label(text='Hair Source:')
        if self.hair_source is not None:
            row.label(text=self.hair_source.name)

        # HAIR PARTICLE SYSTEM   
        row = box.row()
        row.prop_search(self.scene.hn_props, 'hair_system',  bpy.data, 'particles')

        # ADD GUIDES PROPERTY
        row = box.row()
        row.label(text = 'Add Guides:')
        row.prop(self.scene.hn_props, 'additional_guides', text = 'SubD')

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
        for proxy_hair in self.proxy_hair_guides:
            col.label(text = proxy_hair.name)

        # VERSION
        vbox = layout.box()
        row = vbox.row()
        row.label(text= hair_net.version, icon='PARTICLE_PATH')
        sub = row.row()
        sub.scale_x = .5
        sub.prop(self.scene.hn_props, 'info', text = '', icon='QUESTION')




def register():
    bpy.utils.register_class(HAIRNET_PT_view_panel)

def unregister():
    bpy.utils.unregister_class(HAIRNET_PT_view_panel)

