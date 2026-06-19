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
    hair_system: StringProperty(
        name='Hair Net Particle System',
        description='Name of the hair system to be copied by this proxy object. If you want to generate a new particle system, leave this blank.',
        default='')

    additional_guides: IntProperty(
            name='Hair Net Additional Hair Guides',
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