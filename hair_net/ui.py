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
        
        # VERSION / INFO
        vbox = layout.box()
        row = vbox.row()
        row.label(text= data.version, icon='PARTICLE_PATH')
        row.operator('hairnet_readme.operator', icon='QUESTION', text='')

        # CONVERT TO PARTICLES BUTTON
        row = layout.row()
        row.scale_y = 2.0
        row.operator('hairnet.operator', text='Convert to Hair Particles')

        # ADD TO EXISTING HAIR SYSTEM
        box = layout.box()
        row = box.row()
        row.prop(data.scene.hn_props, 'add_to_existing')

        # HAIR PARTICLE SYSTEM   
        if data.scene.hn_props.add_to_existing == False:
            row = box.row()
            row.label(text='Particle Settings:')
            sub = row.row()
            sub.scale_x = 1.475
            sub.prop_search(data.scene.hn_props, 'particle_settings',  bpy.data, 'particles', text='')

class HAIRNET_PT_advanced_panel(bpy.types.Panel):
    bl_label = 'Advanced Features'
    bl_idname = 'HAIRNET_PT_advanced_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Hair Net'
    bl_context = 'objectmode'  
    bl_parent_id = "HAIRNET_PT_view_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout        

        # GENERAL BOX
        box = layout.box()
        split = box.split(factor=0.3)
        col = split.column()
        col.label(text='General Settings:')

        # LINK TO COLLECTION
        col = split.column()
        col.prop(data.scene.hn_props, 'link_to_collection')

        # PROXY COLLECTION NAME
        if data.scene.hn_props.link_to_collection:
            col.prop_search(data.scene.hn_props, 'proxy_collection_name', bpy.data, 'collections', text='', results_are_suggestions=True)

        # CONFIG MODE
        col.prop(data.scene.hn_props, 'configuration_mode')

        # HIDE PROXIES
        col.prop(data.scene.hn_props, 'hide_proxies')        

        # MAX KEYS
        col.prop(data.scene.hn_props, 'max_keys')

        # ROOT BOX
        box = layout.box()
        split = box.split(factor=0.3)
        col = split.column()
        col.label(text='Root Settings:')

        # ROOT SNAP MODE
        col = split.column()
        col.prop(data.scene.hn_props, 'root_snap_mode')

        # ROOT SELECT MODE
        col.prop(data.scene.hn_props, 'root_select_mode')

        # ROOT LOCATOR
        col.prop_search(data.scene.hn_props, 'root_locator', bpy.data, 'objects', text='')

        # CURVE BOX
        box = layout.box()
        split = box.split(factor=0.3)
        col = split.column()
        col.label(text='Curve Settings:')

        # CURVE RESOLUTION
        col = split.column()
        col.prop(data.scene.hn_props, 'curve_resolution')

        layout.use_property_split = True

class HAIRNET_PT_hair_objects_panel(bpy.types.Panel):
    bl_label = 'Hair Objects'
    bl_idname = 'HAIRNET_PT_hair_objects_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Hair Net'
    bl_context = 'objectmode'  
    bl_parent_id = "HAIRNET_PT_view_panel"

    def draw(self, context):
        layout = self.layout
        
        # HAIR Labels
        box = layout.box()
        split = box.split()
        col = split.column()
        col.label(text='Hair Source:')
        col.label(text = 'Guide Hairs:')

        # HAIR OBJECTS
        col = split.column()
        if data.hair_source is not None:
            col.label(text=data.hair_source.name)
        for proxy_hair in data.proxy_hair_guides:
            col.label(text = proxy_hair.name)

class HAIRNET_OT_readme(bpy.types.Operator):
    bl_idname = 'hairnet_readme.operator'
    bl_label = 'Hair Net README'
    bl_description = 'Links to Hair Net README.'

    def execute(self, context):

        webbrowser.open(readme_url, new = 0, autoraise = True)

        return {'FINISHED'}
    
classes = (HAIRNET_PT_view_panel, HAIRNET_PT_advanced_panel, HAIRNET_PT_hair_objects_panel, HAIRNET_OT_readme)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)