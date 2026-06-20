#---------------------------------------------------
# File HairNet.py
# Written by Rhett Jackson April 1, 2013
# Some routines were copied from 'Curve Loop' by Crouch https://sites.google.com/site/bartiuscrouch/scripts/curveloop
# Some routines were copied from other sources
# Very limited at this time:
# NB 1) After running the script to create hair, the user MUST manually enter Particle Mode on the Head object and 'touch' each point of each hair guide. Using a large comb brish with very low strength is a good way to do this. If it's not done, the hair strands are likely to be reset to a default/straight-out position during editing.
# NB 2) All meshes must have the same number of vertices in the direction that corresponds to hair growth
#---------------------------------------------------
# Rewritten by Holo in June, 2026
# No routines have been copied, but may be copied by anyone who would like :)
# All proxy hair objects can now have a variable number of vertices (see readme for details)
# I'm writing this instead of finishing this damn plugin :P
#
#
#
#
#---------------------------------------------------


import bpy
import bmesh
import mathutils

from . import union_find_list, data, debug

# Pseudo code to fix this mess:
'''
Code flow:
Establish the hair system that will be used
Sort each object as a curve, fibermesh, or mesh object

Process curves
Process fibermesh
Process mesh

Recombine these lists

Build hair in the new hair system from these processed proxies

'''

class HAIRNET_OT_operator (bpy.types.Operator):
    bl_idname = 'hairnet.operator'
    bl_label = 'Hair Net'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = 'Turns proxy hair into particle hair.'
    
    @classmethod
    def poll(self, context):
        return(context.mode == 'OBJECT')
    
    #region Reporting

    #endregion
    
    def execute(self, context):
        
        # INIT
        self.curve_list = []
        self.beveled_curve_list = []
        self.fibermesh_list = []
        self.sheet_list = []
        self.other_type_list = []        
        self.hair_guide_list = []

        # SETUP
        if self.set_particle_system(context) == False: return {'CANCELLED'}
        self.sort_proxies(context)
        self.initial_user_report(context)

        # PROCESSING PROXIES INTO GUIDES
        self.process_curves()
        self.process_fibermesh()
        self.process_sheets()

        # BUILDING HAIR
        self.create_particle_hair(context)

        return {'FINISHED'}
    
    #region Setup

    def set_particle_system(self,context):
        '''Handles all of the logic for which particle system should be used'''
        if context.scene.hn_props.add_to_existing:
            return self.add_to_existing_system()           
            
        bpy.ops.object.particle_system_add()     
        self.set_particle_system_settings(context)

        return True
    
    def add_to_existing_system(self):
        if data.hair_source.particle_systems.active == None:
            self.report({'ERROR_INVALID_INPUT'}, 'You need to have an active particle system on the object to add to an existing hair system.')
            return False
        if data.hair_source.particle_systems.active.settings.type == 'EMITTER':
            self.report({'ERROR_INVALID_INPUT'}, 'The active particle system must be a hair system.')
            return False
        return True

    def set_particle_system_settings(self, context):

        if context.scene.hn_props.particle_settings == '':
            data.hair_source.particle_systems.active.settings.type = 'HAIR'
            data.hair_source.particle_systems.active.settings.count = 0
            return True

        for ps in bpy.data.particles:
            if ps.name == context.scene.hn_props.particle_settings:
                data.hair_source.particle_systems.active.settings = ps
                return True
    
    def sort_proxies(self, context):
        '''Sorts the input proxy hair guides. Returns fibermesh, curves, and sheet mesh lists'''
        for proxy in data.proxy_hair_guides:
            match proxy.data.id_type:
                case 'CURVE':
                    if (proxy.data.bevel_depth > 0.0):
                        self.beveled_curve_list.append(proxy)
                    else:
                        self.curve_list.append(proxy)
                case 'MESH':
                    if self.fiber_or_sheet(proxy.data):
                        self.fibermesh_list.append(proxy)
                    else:
                        self.sheet_list.append(proxy)
                case _:
                    self.other_type_list.append(proxy)
                    
    def fiber_or_sheet(self, proxy):
        '''Determines if the user intended a mesh object to be a fiber or a sheet by checking if any vertex has more than 2 edges attached'''

        proxy_bm = bmesh.new()
        proxy_bm.from_mesh(proxy)

        for vert in proxy_bm.verts:
            print(len(vert.link_edges))
            if len(vert.link_edges) > 2:
                proxy_bm.free()
                return False
        
        proxy_bm.free()
        return True
    
    def initial_user_report(self, context):
        '''Reports to the user in the info box. Names the hair system that will be used, then lists the proxy objects by type, and finally outputs warnings for invalid types.'''

        ps_report = ''.join(['Using ', context.scene.hn_props.particle_settings, ' as the particle settings.'])

        if context.scene.hn_props.particle_settings == '':
            ps_report = 'Using new particle settings.'

        self.report({'INFO'}, ps_report)
        proxies = []
        
        proxies.append('CURVES:')
        for proxy in self.curve_list:
            proxies.append(''.join([' --- ', proxy.name]))

        
        proxies.append('FIBERMESH:')
        for proxy in self.fibermesh_list:
            proxies.append(''.join([' --- ', proxy.name]))

        proxies.append('SHEETS:')
        for proxy in self.sheet_list:
            proxies.append(''.join([' --- ', proxy.name]))
        
        self.report({'INFO'}, ''.join(['Building particle hair with "', data.hair_source.name, '" as the hair source and the following as the hair guides:\n', '\n'.join(proxies)]))

        for proxy in self.beveled_curve_list:
            self.report({'WARNING'}, ''.join(['Curve ', proxy.name, ' is beveled and therefore excluded --- continuing']))

        for proxy in self.other_type_list:
            self.report({'WARNING'}, ''.join(['Object ', proxy.name, ' is invalid type ', proxy.type, ' --- continuing']))
    
    #endregion

    #region Processing Hair Guides

    def process_curves(self):
        return

    def process_fibermesh(self):
        return

    def process_sheets(self):
        return


    #endregion

    #region Building Particle Hair

    def create_particle_hair(self, context):
        '''Creates the hair using the indexed vertices from the proxy objects'''

        cd, cv, x, y = self.particle_creation_setup(context)
        


        bpy.ops.object.mode_set(mode = 'PARTICLE_EDIT')

        # PARTICLE TOOL SETTINGS
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Add")
        bpy.context.scene.tool_settings.particle_edit.brush.count = 1
        bpy.context.scene.tool_settings.particle_edit.use_emitter_deflect = False
        bpy.context.scene.tool_settings.particle_edit.use_preserve_root = False
        bpy.context.scene.tool_settings.particle_edit.use_preserve_length = False

        # From what I can work out there are 3 requirements for brush edit (for the purposes of adding particles). 
        # 1. The space must be view3d. 
        # 2. The add particle brush must be active. 
        # 3. The particle system must be a hair system (not an emitter).
        #bpy.ops.particle.brush_edit(stroke=[{"name":"", "location":(0, 0, 0), "mouse":(x, y), "mouse_event":(0, 0), "pressure":0, "size":1, "x_tilt":0, "y_tilt":0, "time":0, "is_start":False}], pen_flip=False)


        #match hair positions

        self.particle_creation_cleanup(context, cd, cv)

        return
    def particle_creation_setup(self, context):
        cam_view = context.region_data.view_matrix
        cam_dist = context.region_data.view_distance

        # Setup camera and object for creating brush edit
        self.frame_objects([data.hair_source])
        x, y = self.get_center_of_3d_view()

        return cam_dist, cam_view, x, y
    
    def frame_objects(self, objects):
        '''This method ensures the object will be centered in the screen for when the brush edit creates particles'''
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:
            obj.select_set(True)
        bpy.ops.view3d.view_selected()
    
    def get_center_of_3d_view(self):
        return bpy.context.area.width / 2, bpy.context.area.height / 2
    
    def particle_creation_cleanup(self, context, cam_dist, cam_view):
        '''sets back to object mode, resets view, and clears selection'''
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        context.region_data.view_distance = cam_dist
        context.region_data.view_matrix = cam_view

    
    #endregion

def register():
    bpy.utils.register_class(HAIRNET_OT_operator)

def unregister():
    bpy.utils.unregister_class(HAIRNET_OT_operator)