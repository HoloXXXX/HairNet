import bpy

from bpy.types import PropertyGroup

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       CollectionProperty,
                       )

# update the bl_info in __init__ and blender_manifest.toml when changing this
version = "1.0.0"

class HairNetProperties(PropertyGroup):
    particle_settings: StringProperty(
        name='Particle Settings',
        description='Particle settings to be copied to the new particle system. If you want to generate new settings, leave this blank.',
        default='')
    
    proxy_collection_name: StringProperty(
        name='Proxy Collection Name',
        description='The name of the collection that proxies should be added to.',
        default='Hair_Net_Proxies')
    
    root_locator: StringProperty(
        name='Root Locator',
        description='Select an object to use as an indicator for which side of the hair should be the root. This is the location of the transform in the viewport when "bounding box center" is selected as the objects transform pivot point. This is overridden by root select mode when it applies.',
        default='')
    
    add_to_existing: BoolProperty(
        name='Add To Existing Hair System',
        description='Add the guide hairs to the active particle system. Requires an existing particle system to be active.',
        default=False)
    
    link_to_collection: BoolProperty(
        name='Link Proxies To Collection',
        description='When selected, only the initial report phase of HairNet will execute. It will output if the active object is valid, which particle system will be used, and valid and invalid proxy objects in the info box. This is useful if you have a slow computer and a lot of objects to convert.',
        default=False)
    
    configuration_mode: BoolProperty(
        name='Configuration Mode',
        description='When selected, only the initial report phase of HairNet will execute. It will output if the active object is valid, which particle system will be used, and valid and invalid proxy objects in the info box. This is useful if you have a slow computer and a lot of objects to convert.',
        default=False)
    
    hide_proxies: BoolProperty(
        name='Hide Proxies',
        description='Hide proxy hair after conversion into particle hair.',
        default=False)
    
    root_snap_mode: BoolProperty(
        name='Root Snap Mode',
        description='When enabled the particle roots will be snapped to the mesh of the hair source object.',
        default=False)
    
    root_select_mode: BoolProperty(
        name='Root Select Mode',
        description='This is a tool to fix reversed roots. When checked, selected vertices on hairs will be prioritized for determining roots. Seams on sheet mesh override this. Doesn\'t support objects with multiple meshes or curves with multiple splines.',
        default=False)
    
    curve_resolution: IntProperty(
        name='Curve Resolution',
        description='This is number is 1 less than the number of hair keys the tool will set the particle as. If it\'s set to 0, the resolution on each individual curve will be used. Does not affect "Curves" objects.',
        default=0,
        min=0,
        max=64,
        options = set())
    
    max_keys: IntProperty(
        name='Max Hair Keys',
        description='This prevents the tool from getting stuck in an endless iteration. Set this value to a little above what you would expec the maximum number of keys to be for any given particle',
        default=100,
        min=2,
        options = set()
        )
    
    info: StringProperty(
        name='Hair Net Info',
        description='In order to use the add-on, select all of the objects you want to use as hair guides, then select the object you want the hair to grow from.' \
        'For more info, please see the ReadMe',
        default=''
        )
    

def update_hair_data():
    '''Splits the current selection into a list of hair objects to be turned into particle hair, and the object that will host the particle system'''
    global hair_source
    global proxy_hair_guides
    global scene

    scene = bpy.context.scene
    
    hair_source = bpy.context.active_object
    
    proxy_hair_guides = [ obj for obj in bpy.context.selected_objects if obj is not hair_source]
    
def register():
    bpy.utils.register_class(HairNetProperties)
    bpy.types.Scene.hn_props=PointerProperty(type=HairNetProperties)

def unregister():
    bpy.utils.unregister_class(HairNetProperties)
    del bpy.types.Scene.hn_props