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
    
    root_object: StringProperty(
        name='Root Object',
        description='Select an object to use as an indicator for which side of the hair should be the root.',
        default='')
    
    add_to_existing: BoolProperty(
        name='Add To Existing Hair System',
        description='Add the guide hairs to the active particle system. Requires an existing particle system to be active.',
        default=False)
    
    hide_proxies: BoolProperty(
        name='Hide Proxies',
        description='Hide proxy hair after conversion into particle hair.',
        default=False)
    
    root_select_mode: BoolProperty(
        name='Root Select Mode',
        description='This is a tool to fix reversed roots. When checked, selected vertices on hairs will be prioritized for determining roots. Seams on sheet mesh override this.',
        default=False)
    
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