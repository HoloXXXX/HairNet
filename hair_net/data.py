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
    
    add_to_existing: BoolProperty(
        name='Add To Existing Hair System',
        description='Add the guide hairs to the active particle system. Requires an existing particle system to be active',
        default=False)

    additional_guides: IntProperty(
            name='Additional Hair Guides',
            description='Number of additional hairs to add.',
            default=0)
    
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