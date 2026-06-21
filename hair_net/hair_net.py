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
# All proxy hair objects can now have a variable number of vertices (see readme for details)
# I'm writing this instead of finishing this damn plugin :P
#
#
#
#
#---------------------------------------------------


import bpy
import bmesh
from mathutils import Vector

from . import data


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
        self.hair_root_loc = object
        self.curve_list = []
        self.beveled_curve_list = []
        self.fibermesh_list = []
        self.sheet_list = []
        self.other_type_list = []        
        self.hair_guides = []

        # SETUP
        if self.set_particle_system(context) == False: return {'CANCELLED'}
        data.hair_source.particle_systems.active.settings.display_step = 7
        self.set_hair_root_object(context)
        self.sort_proxies(context)
        self.initial_user_report(context)

        # PROCESSING PROXIES INTO GUIDES
        self.process_fibermesh(context, self.fibermesh_list)
        self.process_curves(context)
        self.process_sheets(context)

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
    
    def set_hair_root_object(self, context):
        if context.scene.hn_props.root_object == True:
            self.hair_root_loc = bpy.data.objects[context.scene.hn_props.root_object]
        self.hair_root_loc = self.get_object_center(data.hair_source)
    
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

    def process_curves(self, context):
        new_fibermesh = []
        for curve in self.curve_list:
            # Conversion code from https://blender.stackexchange.com/questions/265215/how-can-i-convert-a-curve-to-a-mesh-object
            fiber = curve.to_mesh()
            new_fiber = bpy.data.objects.new(curve.name + "Mesh", fiber.copy())
            new_fiber.matrix_world = curve.matrix_world
            bpy.context.collection.objects.link(new_fiber)
            new_fibermesh.append(new_fiber)

        self.process_fibermesh(context, new_fibermesh)
        
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.evaluated_depsgraph_get()

        for obj in new_fibermesh:
            obj.select_set(True)
        bpy.ops.object.delete()

    def process_fibermesh(self, context, mesh_list):       

        for proxy in mesh_list:

            proxy_bm = bmesh.new()
            proxy_bm.from_mesh(proxy.data)
            end_verts = []
            
            for current_vert in proxy_bm.verts:
                if len(current_vert.link_edges) == 1:
                    end_verts.append(current_vert)

            if len(end_verts) == 0:
                self.report({'WARNING'}, ''.join(['Fibermesh ', proxy.name, ' has no end verts and therefore excluded --- continuing']))
                continue
                            
            root_vert = self.decide_root(context, end_verts)
            self.edge_walk_new_guide(root_vert)

            proxy_bm.free()

        return

    def process_sheets(self, context):
        self.get_seams()
        # get non seam edges attached to seam
        # loop select them
        # dupe, del everything not the edge
        # send to fibermesh pipe
        # del mesh
        return

    def get_seams(self):
        for proxy in self.sheet_list:

            proxy_bm = bmesh.new()
            proxy_bm.from_mesh(proxy.data)
            seam_verts = []
            
            # gets all of the seam verts
            for edge in proxy_bm.edges:
                if edge.seam == True:
                    for vert in edge:
                        if vert not in seam_verts:
                            seam_verts.append(edge)

            # gets the non seam edges attached
            #for vert in seam_verts:
            #    for edge in vert.link_edges:
            #return
    
    def decide_root(self, context, end_verts):
        '''This function takes in verts with only one edge and decides which of these will become the root.'''

        # RETURN BASED ON THE ROOT SELECTION
        if context.scene.hn_props.root_select_mode:
            for vert in end_verts:
                if vert.select == True:
                    return vert

        # RETURN BASED ON THE DISTANCE TO DEFINED OBJECT
        closest_vert = end_verts[0]
        for vert in end_verts:
            if vert.co - self.hair_root_loc < closest_vert.co - self.hair_root_loc:
                vert = closest_vert

        return closest_vert
    
    def edge_walk_new_guide(self, root_vert):
            guide = []
            guide.append(root_vert.co)
            current_vert = root_vert
            current_edge = root_vert.link_edges[0]

            while(True):
                for v in current_edge.verts:
                    if v != current_vert:
                        guide.append(v.co)
                        current_vert = v
                        break
                prev_e = current_edge
                for e in current_vert.link_edges:
                    if e != current_edge:
                        current_edge = e
                        break
                if prev_e == current_edge:
                    break
            
            self.hair_guides.append(guide)
    
    def get_object_center(self, object):
        # from https://blender.stackexchange.com/questions/62040/get-center-of-geometry-of-an-object
        x, y, z = [ sum( [v.co[i] for v in object.data.vertices] ) for i in range(3)]

        count = float(len(object.data.vertices))

        return object.matrix_world @ (Vector( (x, y, z ) ) / count )

    #endregion

    #region Building Particle Hair

    def create_particle_hair(self, context):
        '''Creates the hair using the indexed vertices from the proxy objects'''

        bpy.context.view_layer.objects.active = data.hair_source
        cd, cv, x, y = self.particle_creation_setup(context)

        bpy.ops.object.mode_set(mode = 'PARTICLE_EDIT')
#
        # PARTICLE TOOL SETTINGS
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Add")
        bpy.context.scene.tool_settings.particle_edit.brush.count = 1
        bpy.context.scene.tool_settings.particle_edit.use_emitter_deflect = False
        bpy.context.scene.tool_settings.particle_edit.use_preserve_root =  False
        bpy.context.scene.tool_settings.particle_edit.use_preserve_length = False

        ps_name = data.hair_source.particle_systems.active.name
        ps = data.hair_source.particle_systems.active

        for i in range(0,len(self.hair_guides)):

            guide = self.hair_guides[i]
            bpy.context.scene.tool_settings.particle_edit.default_key_count = len(guide)

            # From what I can work out there are 3 requirements for brush edit to complete successfully. 
            # 1. The space must be view3d. 
            # 2. A particle brush must be active. 
            # 3. The particle system must be a hair system (not an emitter).
            bpy.ops.particle.brush_edit(stroke=[{"name":"", "location":(0, 0, 0), "mouse":(x, y), "mouse_event":(0, 0), "pressure":0, "size":0, "x_tilt":0, "y_tilt":0, "time":0, "is_start":False}], pen_flip=False)  

            depsgraph = bpy.context.evaluated_depsgraph_get()
            depObj = data.hair_source.evaluated_get(depsgraph)
            ps = depObj.particle_systems[ps_name]

            new_particle = ps.particles[i]
            new_particle.location = guide[0]

            for j in range(0, len(guide)):
                h = new_particle.hair_keys[j]
                h.co = guide[j]
                print(guide[j], new_particle.hair_keys[j].co)
        # THIS IS NEEDED TO MAKE THE CHANGES TO PARTICLES STICK. I don't know why, and I don't ask questions of the machine guides who rule us
        bpy.ops.particle.brush_edit(stroke=[{"name":"", "location":(0, 0, 0), "mouse":(0,0), "mouse_event":(0, 0), "pressure":0, "size":0, "x_tilt":0, "y_tilt":0, "time":0, "is_start":False}], pen_flip=False)

        self.particle_creation_cleanup(context, cd, cv)

        return
    
    def particle_creation_setup(self, context):
        '''Handles camera and screen for particle creation'''
        cam_view = context.region_data.view_matrix
        cam_dist = context.region_data.view_distance

        # Setup camera and object for creating brush edit
        self.frame_objects()
        x, y = self.get_center_of_3d_view()

        return cam_dist, cam_view, x, y
    
    def frame_objects(self):
        '''This method ensures the object will be centered in the screen for when the brush edit creates particles'''
        bpy.ops.object.select_all(action='DESELECT')
        data.hair_source.select_set(True)
        bpy.ops.view3d.view_selected()
    
    def get_center_of_3d_view(self):
        return bpy.context.area.width / 2, bpy.context.area.height / 2
    
    def particle_creation_cleanup(self, context, cam_dist, cam_view):
        '''sets back to object mode, clears selection, hides proxies if applicable, and resets camera view'''
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        if context.scene.hn_props.hide_proxies == True:
            self.hide_proxy_hair()
        # unfortunately whenever you use particle brush edit it becomes impossible (afaik) to reset the camera. I have no idea why, but I'm leaving this camera reset in the code in case this changes in the future
        context.region_data.view_distance = cam_dist
        context.region_data.view_matrix = cam_view

    def hide_proxy_hair(self):
        for proxy in data.proxy_hair_guides:
            proxy.hide_viewport = True    

    #endregion

def register():
    bpy.utils.register_class(HAIRNET_OT_operator)

def unregister():
    bpy.utils.unregister_class(HAIRNET_OT_operator)