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
# Unbent unbroken
# See README for details
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
    
    def execute(self, context):
        
        # INIT
        self.hair_root_loc = object
        self.hair_source_matrix_inverted = object
        self.fibermesh_list = []
        self.curve_list = []
        self.sheetmesh_list = []
        self.hair_guides = []

        # SETUP
        if self.init_check(): return {'CANCELLED'}
        invalid_mesh_list, beveled_curve_list, other_type_list = self.sort_proxies()
        if self.no_valid_proxies(invalid_mesh_list, beveled_curve_list, other_type_list): return {'CANCELLED'}
        if self.set_particle_system(context): return {'CANCELLED'}
        self.set_hair_root_locator(context)
        self.set_hair_source_matrix_inverted()
        self.initial_user_report(context, invalid_mesh_list, beveled_curve_list, other_type_list)
        if context.scene.hn_props.configuration_mode: return {'FINISHED'}

        # PROCESSING PROXIES INTO GUIDES
        self.process_fibermesh(context, self.fibermesh_list)
        self.process_curves(context)
        self.process_sheets(context)

        # BUILDING HAIR
        self.create_particle_hair(context)

        return {'FINISHED'}
    
    #region Setup

    def init_check(self):
        if len(data.proxy_hair_guides) == 0:
            self.report({'ERROR_INVALID_INPUT'}, 'Please select at least one valid hair proxy object.')
            return True
        if data.hair_source.type != "MESH":
            self.report({'ERROR_INVALID_INPUT'}, 'Please ensure the active object is capable of hosting a particle system.')
            return True
        else:
            if len(data.hair_source.data.polygons) == 0:
                self.report({'ERROR_INVALID_INPUT'}, 'Please ensure the active object has at least one face.')
                return True
        return False
    
    def sort_proxies(self):
        '''Sorts the input proxy hair guides. Returns fibermesh, curves, sheet mesh, beveled curves, and "other" type lists'''
        
        invalid_mesh_list = []
        beveled_curve_list = []
        other_type_list = []

        for proxy in data.proxy_hair_guides:
            match proxy.type:
                case "CURVES":
                        self.curve_list.append(proxy)    
                case "CURVE":
                    if proxy.data.bevel_depth > 0.0 or\
                        proxy.data.bevel_object != None:
                        beveled_curve_list.append(proxy)
                    else:
                        self.curve_list.append(proxy)
                case "MESH":
                    if self.is_valid_mesh(proxy):
                        continue
                    else:
                        invalid_mesh_list.append(proxy)
                case _:
                    other_type_list.append(proxy)

        return invalid_mesh_list, beveled_curve_list, other_type_list
                    
    def is_valid_mesh(self, proxy):
        '''Determines if the mesh is valid by first checking for a face to determine fibermesh status, then checking for a seam if there are faces. Otherwise, it's an invalid mesh.'''
        if len(proxy.data.polygons) == 0:
            self.fibermesh_list.append((proxy, proxy.name))
            return True
        for edge in proxy.data.edges:
            if edge.use_seam:
                self.sheetmesh_list.append(proxy)
                return True
        return False
    
    def no_valid_proxies(self, invalid_mesh_list, beveled_curve_list, other_type_list):
        if len(self.fibermesh_list) + len(self.curve_list) + len(self.sheetmesh_list) == 0:
            self.report_invalid_proxy_warnings(invalid_mesh_list, beveled_curve_list, other_type_list)
            self.report({'ERROR_INVALID_INPUT'}, 'No valid proxy objects selected.')
            return True
        return False
                    
    def seam_exists(self, mesh):
        '''Determines if the user intended a mesh object to be a fiber or a sheet by checking if there is a face in the mesh'''
        if len(mesh.polygons) == 0:
            return True        
        return False

    def set_particle_system(self,context):
        '''Handles all of the logic for which particle system should be used'''

        if context.scene.hn_props.add_to_existing:
            if data.hair_source.particle_systems.active == None:
                self.report({'ERROR_INVALID_INPUT'}, 'You need to have an active particle system on the object to add to an existing hair system.')
                return True
        else:
            bpy.ops.object.particle_system_add()
            self.set_particle_system_settings(context)

        if data.hair_source.particle_systems.active.settings.type == 'EMITTER':
            self.report({'ERROR_INVALID_INPUT'}, 'The active particle system must be a hair system.')
            return True
        
        return False

    def set_particle_system_settings(self, context):
        '''Sets the particle settings for a new particle system'''

        if context.scene.hn_props.particle_settings == '':
            data.hair_source.particle_systems.active.settings.type = 'HAIR'
            data.hair_source.particle_systems.active.settings.count = 0
            return

        data.hair_source.particle_systems.active.settings = bpy.data.particles[context.scene.hn_props.particle_settings]
        data.hair_source.particle_systems.active.settings.count = 0
    
    def set_hair_root_locator(self, context):
        '''Sets what object will be used when determing which vert of a fiber or curve to set as the root.'''
        if context.scene.hn_props.root_locator != '':
            self.hair_root_loc = bpy.data.objects[context.scene.hn_props.root_locator].location
            return
        self.hair_root_loc = self.get_object_center(data.hair_source)
    
    def get_object_center(self, object):
        # from https://blender.stackexchange.com/questions/62040/get-center-of-geometry-of-an-object
        x, y, z = [ sum( [v.co[i] for v in object.data.vertices] ) for i in range(3)]

        count = float(len(object.data.vertices))

        return object.matrix_world @ (Vector( (x, y, z ) ) / count )

    def set_hair_source_matrix_inverted(self):
        self.hair_source_matrix_inverted = data.hair_source.matrix_world.inverted()
    
    def initial_user_report(self, context, invalid_mesh_list, beveled_curve_list, other_type_list):
        '''Reports to the user in the info box. Names the hair system that will be used, then lists the proxy objects by type, and finally outputs warnings for invalid objects.'''

        if context.scene.hn_props.add_to_existing == True:
            ps_report = ''.join(['Using existing particle system ', data.hair_source.particle_systems.active.name])
        else:
            ps_report = ''.join(['Using ', context.scene.hn_props.particle_settings, ' as the particle settings.'])
            if context.scene.hn_props.particle_settings == '':
                ps_report = 'Using new particle settings.'

        self.report({'INFO'}, ps_report)
        
        proxies = []

        proxies.append('FIBERMESH:')
        for proxy in self.fibermesh_list:
            proxies.append(''.join([' --- ', proxy[1]]))
        
        proxies.append('CURVES:')
        for proxy in self.curve_list:
            proxies.append(''.join([' --- ', proxy.name]))        

        proxies.append('SHEETS:')
        for proxy in self.sheetmesh_list:
            proxies.append(''.join([' --- ', proxy.name]))

        self.report({'INFO'}, ''.join(['Building particle hair with "', data.hair_source.name, '" as the hair source and the following as the hair guides:\n', '\n'.join(proxies)]))

        self.report_invalid_proxy_warnings(invalid_mesh_list, beveled_curve_list, other_type_list)

    def report_invalid_proxy_warnings(self, invalid_mesh_list, beveled_curve_list, other_type_list):

        for proxy in invalid_mesh_list:
            self.report({'WARNING'}, ''.join(['Mesh ', proxy.name, ' has faces but no seams, and is therefore excluded --- continuing']))

        for proxy in beveled_curve_list:
            self.report({'WARNING'}, ''.join(['Curve ', proxy.name, ' is beveled and therefore excluded --- continuing']))

        for proxy in other_type_list:
            self.report({'WARNING'}, ''.join(['Object ', proxy.name, ' is invalid type ', proxy.type, ' --- continuing']))

    
    #endregion

    #region Processing Hair Guides

    #region Fibermesh

    def process_fibermesh(self, context, fibermesh_list):
        '''Turns fibermesh input into vert coordinates for particle hair. mesh_list is a tuple of (proxy object, proxy name)'''

        for i in range(0, len(fibermesh_list)):
            
            proxies = self.separate_mesh(context, fibermesh_list[i][0])

            for proxymesh in proxies:

                proxy_bm = bmesh.new()
                proxy_bm.from_mesh(proxymesh.data)
                proxy_bm.verts.ensure_lookup_table()

                end_verts = self.get_end_verts(proxy_bm)

                if len(end_verts) == 0:
                    self.report({'WARNING'}, ''.join(['A mesh in ', fibermesh_list[i][1], ' has no end verts and is therefore excluded --- continuing']))
                    continue

                root_vert = self.decide_root(context, fibermesh_list[i][0], end_verts)
                root_co, guide = self.fibers_to_vert_co(context, fibermesh_list[i][0], root_vert)
                guide = self.co_space_conversion(context, fibermesh_list[i][0], guide)

                self.hair_guides.append(root_co + guide)

                proxy_bm.free()
                
            self.cleanup_meshes(proxies)

    def get_end_verts(self, proxy_bm):
        '''Return any vert on a fibermesh that has only one edge attached'''

        end_verts = []

        for current_vert in proxy_bm.verts:
            if len(current_vert.link_edges) == 1:
                end_verts.append(current_vert)

        return end_verts

    def decide_root(self, context, proxy, end_verts):
        '''This function takes in verts with only one edge and decides which of these will become the root.'''
        if context.scene.hn_props.root_select_mode:
            for vert in end_verts:
                if vert.select == True:
                    return vert
                
        world_vert_co = [proxy.matrix_world @ vert.co for vert in end_verts]

        closest_vert = end_verts[0]
        closest_vert_index = 0
        for i in range(0,len(world_vert_co)):
            if world_vert_co[i] - self.hair_root_loc < world_vert_co[closest_vert_index] - self.hair_root_loc:
                closest_vert = end_verts[i]
                closest_vert_index = i

        return closest_vert
    
    def fibers_to_vert_co(self, context, proxy, root_vert):
        '''Adds vert coordinates to guide list in order of edge connections'''

        guide = []
        root_co = []

        if context.scene.hn_props.root_snap_mode:
            root_co.append(self.root_snap(root_vert.co, proxy))
        else:
            guide.append(root_vert.co)

        current_vert = root_vert
        current_edge = root_vert.link_edges[0]

        inf_block = 1
        while(True):
            for v in current_edge.verts:
                if v != current_vert:
                    guide.append(v.co)
                    current_vert = v
                    break
            prev_edge = current_edge
            for e in current_vert.link_edges:
                if e != current_edge:
                    current_edge = e
                    break
            if prev_edge == current_edge:
                break
            inf_block += 1
            if inf_block == context.scene.hn_props.max_keys:
                self.report({'WARNING'}, ''.join(['Object ', proxy.name, ' hit max key amount. --- continuing']))
                break
        return root_co, guide
    
    #endregion

    #region Curve
    
    def process_curves(self, context):
        '''Turns curve input into vert coordinates for particle hair'''

        curve_meshes = []
        curve_data = []

        # It's less efficient to duplicate and convert the objects in the for loop rather than all at once, but it's necessary for speeding up the comparison of the root select.
        for curve in self.curve_list:
            bpy.ops.object.select_all(action='DESELECT')
            curve.select_set(True)
            self.set_curve_resolution(context, curve)
            bpy.ops.object.duplicate(linked=False)
            bpy.ops.object.convert(target='MESH', keep_original=False)
            curve_meshes.append((bpy.context.selected_objects[0]))
            curve_data.append((bpy.context.selected_objects[0], curve.name))

        self.select_curve_mesh_root(context, curve_meshes)
        self.process_fibermesh(context, curve_data)
        self.cleanup_meshes(curve_meshes)
            
    def set_curve_resolution(self, context, curve):
        if context.scene.hn_props.curve_resolution == 0 or \
            curve.type == "CURVES":
            return
        curve.data.resolution_u = context.scene.hn_props.curve_resolution

    def select_curve_mesh_root(self, context, curve_meshes):
        '''Transfers root selection to newly created curve mesh'''

        if not context.scene.hn_props.root_select_mode:
            return

        for i in range(0,len(self.curve_list)):

            if self.curve_list[i].type == "CURVES":
                continue

            selected_point_coords = self.get_og_selected_curve_points(i)

            for j in range(0,len(selected_point_coords)):
                self.select_curve_mesh_verts(selected_point_coords[j], curve_meshes[i])

    def get_og_selected_curve_points(self, i):
        '''Gets the coordinates of the selected points of the original curve'''

        selected_coords = []

        if self.curve_list[i].data.splines[0].type == "BEZIER":
            for point in self.curve_list[i].data.splines[0].bezier_points:
                if point.select_control_point:
                    selected_coords.append(point.co)
        else:
            for point in self.curve_list[i].data.splines[0].points:
                if point.select:
                    selected_coords.append(point.co)
        
        return selected_coords

    def select_curve_mesh_verts(self, s_co, curve_mesh):
        '''Select vert if within a tolerance of the selected point on the curve'''

        for vert in curve_mesh.data.vertices:
            if self.same_vert_location(s_co, vert.co):
                vert.select = True

    def same_vert_location(self, vert1_co, vert2_co, rel_tol=1e-09, abs_tol=0.001):
        if abs(vert2_co - vert1_co) < max(rel_tol * max(abs(vert1_co), abs(vert2_co), abs_tol)):
            return True
                
    #endregion

    #region Sheet Mesh

    def process_sheets(self, context):
        '''Turns sheet mesh input into vert coordinates for particle hair'''

        for proxy in self.sheetmesh_list:

            proxies = self.separate_mesh(context, proxy)

            for proxy_mesh in proxies:

                proxy_bm = bmesh.new()
                proxy_bm.from_mesh(proxy_mesh.data)
                proxy_bm.verts.ensure_lookup_table()

                bm_loops = self.get_seams(proxy_bm)            

                if len(bm_loops) == 0:
                        self.report({'WARNING'}, ''.join(['No fibers along the seam(s) of sheetmesh ', proxy.name, ' and therefore excluded --- continuing']))
                        continue

                self.fibers_from_sheet_mesh(context, proxy, bm_loops)

                proxy_bm.free()

            self.cleanup_meshes(proxies)

    def get_seams(self, proxy_bm):
        '''Returns the loops attached to the edges perpendicular to marked seams'''

        seam_verts = []
        
        for edge in proxy_bm.edges:
            if edge.seam == True:
                for vert in edge.verts:
                    if vert not in seam_verts:
                        seam_verts.append(vert)

        bm_loops = []

        for vert in seam_verts:
            for edge in vert.link_edges:
                if edge.seam == False:
                    bm_loops.append(edge.link_loops[0])

        return bm_loops
    
    def fibers_from_sheet_mesh(self, context, proxy, loops):
        '''Retrieves vert coordinates of an edge loop from an input edge'''
        
        for loop in loops:
            # I don't think there's a way to anonymize backward and forward walking :(            
            if loop.link_loop_prev.link_loop_radial_prev.link_loop_prev.edge.seam == True or loop.link_loop_prev.edge.seam == True:
                if loop.link_loop_next.edge.seam == True or loop.link_loop_next.link_loop_radial_next.link_loop_next.edge.seam == True:
                    continue
                root_co, guide = self.forward_edge_walk(context, proxy, loop)
            else:
                root_co, guide = self.backward_edge_walk(context, proxy, loop)
                
            guide = self.co_space_conversion(context, proxy, guide)

            self.hair_guides.append(root_co + guide)

    def backward_edge_walk(self, context, proxy, loop):
        '''Walks backward along an edge storing vertices until it hits a seam or a new edge'''

        vert_comparison = len(loop.vert.link_edges)

        if vert_comparison > 4: 
            vert_comparison == 4

        guide = []
        root_co = []

        if context.scene.hn_props.root_snap_mode:
            root_co.append(self.root_snap(loop.link_loop_next.vert.co, proxy))
        else: 
            guide.append(loop.link_loop_next.vert.co)

        guide.append(loop.vert.co)
        
        inf_block = 2
        while loop.link_loop_prev != loop.link_loop_prev.link_loop_radial_prev and \
            len(loop.vert.link_edges) >= vert_comparison:
            
            loop = loop.link_loop_prev.link_loop_radial_prev.link_loop_prev

            guide.append(loop.vert.co)

            inf_block +=1
            if inf_block == context.scene.hn_props.max_keys:
                self.report({'WARNING'}, ''.join(['Fiber on ', proxy.name, ' Sheetmesh hit max key amount. --- continuing']))
                break
            
        return root_co, guide

    def forward_edge_walk(self, context, proxy, loop):
        '''Walks forward along an edge storing vertices until it hits a seam or a new edge'''
        
        vert_comparison = len(loop.link_loop_next.vert.link_edges)

        if vert_comparison > 4: 
            vert_comparison = 4
        
        guide = []
        root_co = []

        if context.scene.hn_props.root_snap_mode:
            root_co.append(self.root_snap(loop.vert.co, proxy))
        else: 
            guide.append(loop.vert.co)

        guide.append(loop.link_loop_next.vert.co)

        inf_block = 2
        while loop.link_loop_next != loop.link_loop_next.link_loop_radial_next and \
            len(loop.link_loop_next.vert.link_edges) >= vert_comparison:
            
            loop = loop.link_loop_next.link_loop_radial_next.link_loop_next

            guide.append(loop.link_loop_next.vert.co)
            
            inf_block +=1
            if inf_block == context.scene.hn_props.max_keys:
                self.report({'WARNING'}, ''.join(['Fiber on ', proxy.name, ' Sheetmesh hit max key amount. --- continuing']))
                break
        
        return root_co, guide
    
    #endregion
    
    #region helpers
    
    def separate_mesh(self, context, proxy):
        bpy.ops.object.select_all(action='DESELECT')
        proxy.select_set(True)
        bpy.ops.object.duplicate(linked=False)
        bpy.ops.mesh.separate(type="LOOSE")
        return context.selected_objects
    
    def root_snap(self, root_co, proxy):
        '''Sets the root coordinate to the closest point on the hair source'''
        # from here: https://blender.stackexchange.com/questions/58409/how-do-i-find-the-closest-point-on-another-mesh-to-a-vertex-with-python
        
        world_root_co = proxy.matrix_world @ root_co
        local_root_co = self.hair_source_matrix_inverted @ world_root_co

        hit, loc, norm, face_index = data.hair_source.closest_point_on_mesh(local_root_co)
        if hit:
            return loc
        else: 
            self.report({'WARNING'}, ''.join(['Failed to snap root on ', proxy.name, ' --- continuing']))
            return root_co

    def co_space_conversion(self, context, proxy, guide):
        '''Converts the vertex coordinates into the space of the hair source mesh'''
        
        converted_guide = []
        proxy_matrix = proxy.matrix_world

        for i in range(0,len(guide)):
            world_co = proxy_matrix @ guide[i]
            obj_co = self.hair_source_matrix_inverted @ world_co
            converted_guide.append(obj_co)

        return converted_guide
    
    def cleanup_meshes(self, proxies):
        scene_meshes = bpy.data.meshes
        for proxymesh in proxies:
            scene_meshes.remove(proxymesh.data, do_unlink=True)

    #endregion

    #endregion

    #region Building Particle Hair
    
    def particle_creation_setup(self, context):
        '''Handles camera, screen, mode, and particle settings for particle creation'''
        # unfortunately whenever you use particle brush edit it becomes impossible (afaik) to reset the camera. I have no idea why, but I'm leaving this camera reset in the code in case this changes in the future (and so that people are aware of the issue)
        cam_view, cam_dist, xray_val = self.set_camera(context)
        self.frame_objects()
        x, y = self.get_center_of_3d_view()

        self.setup_particle_brush(context)

        return cam_dist, cam_view, x, y, xray_val
    
    def set_camera(self, context):
        # brush edit fails in x ray mode
        xray_val = bpy.context.area.spaces.active.shading.show_xray
        bpy.context.area.spaces.active.shading.show_xray = False

        return context.region_data.view_matrix, context.region_data.view_distance, xray_val
    
    def frame_objects(self):
        '''This method ensures the object will be centered in the screen for when the brush edit creates particles'''
        bpy.context.view_layer.objects.active = data.hair_source
        bpy.ops.object.select_all(action='DESELECT')
        data.hair_source.select_set(True)
        bpy.ops.view3d.view_selected()
    
    def get_center_of_3d_view(self):
        return bpy.context.area.width / 2, bpy.context.area.height / 2
    
    def setup_particle_brush(self, context):
        bpy.ops.object.mode_set(mode = 'PARTICLE_EDIT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Add")
        context.scene.tool_settings.particle_edit.brush.count = 1
        context.scene.tool_settings.particle_edit.use_emitter_deflect = False
        context.scene.tool_settings.particle_edit.use_preserve_root =  False
        context.scene.tool_settings.particle_edit.use_preserve_length = False

    def create_particle_hair(self, context):
        '''Creates the new hair using the vertex coordinates from the proxy objects'''

        cd, cv, x, y, xray_val = self.particle_creation_setup(context)

        for i in range(0,len(self.hair_guides)):

            guide = self.hair_guides[i]

            self.create_new_particle(context, x, y, len(self.hair_guides[i]))
            try:
                self.set_new_particle(context, guide)
                self.set_hair_keys(context, guide)
            except: 
                self.report({'ERROR'}, 'Could not create particle. Please see the Troubleshooting section of the README')
                bpy.ops.object.mode_set(mode = 'OBJECT')
                return

        self.particle_creation_cleanup(context, x, y, cd, cv, xray_val)

        return 
    
    def create_new_particle(self, context, x, y, keys):

        bpy.context.scene.tool_settings.particle_edit.default_key_count = keys
        self.evaluate_dependency_graph(context) # this probably doesn't absolutely have to be here, but given how finnicky the particle system is I'm leaving it
            
            # From what I can work out there are 3 requirements for brush edit to complete successfully. 
            # 1. The space must be view3d. 
            # 2. A particle brush must be active. 
            # 3. The particle system must be a hair system (not an emitter (and only when using the add brush)).
        bpy.ops.particle.brush_edit(stroke=[{"name":"", "location":(0, 0, 0), "mouse":(x, y), "mouse_event":(0, 0), "pressure":0, "size":0, "x_tilt":0, "y_tilt":0, "time":0, "is_start":False}], pen_flip=False)
    
    def set_new_particle(self, context, guide):
        ps = self.evaluate_dependency_graph(context)
        new_particle = ps.particles[-1]
        new_particle.location = guide[0]

    def set_hair_keys(self, context, guide):
        for j in range(0, len(guide)):
            ps = self.evaluate_dependency_graph(context)
            ps.particles[-1].hair_keys[j].co = guide[j]
    
    def evaluate_dependency_graph(self, context):
        '''Grabs the most recent data from the scene to evaluate'''
        depsgraph = context.evaluated_depsgraph_get()
        return data.hair_source.evaluated_get(depsgraph).particle_systems.active
    
    def particle_creation_cleanup(self, context, x, y, cam_dist, cam_view, xray_val):
        '''sets back to object mode, clears selection, hides proxies if applicable, and resets camera view'''

        self.final_particle_system_cleanup(context, x, y)

        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        #proxies = self.fibermesh_list + self.curve_list + self.sheetmesh_list
        self.link_proxies_to_collection(context, [*[fibermesh[0] for fibermesh in self.fibermesh_list], *self.curve_list, *self.sheetmesh_list])
        self.hide_proxy_objects(context)

        self.camera_reset(context, cam_dist, cam_view, xray_val)

    def final_particle_system_cleanup(self, context, x, y):
        '''A FINAL EXTRA PARTICLE MUST BE CREATED TO MAKE THE KEY CHANGES TO THE LAST PARTICLE STICK. I don't know why, and I don't ask questions of the machine gods who rule us'''
        
        # things I've tried to remove this particle after creating it/not create it in the first place:
        # Looked for a relevant command in bpy.ops.particle --- there's a delete function but it requires selection, and there's no way to select the particle through code that I'm aware of.
        # Change the mouse location so it's never created --- The mouse lining up with the object seems to only be required every x particles
        # Look for a way to directly remove it in bpy.types.particle --- setting alive state to dead has no effect (i think that property is just for emitters)
        # Switch to object mode, then back to particle edit mode and bpy.ops.particle.edited_clear()
        # Tried deleting directly from the particles list
        # Added bpy.ops.ed.undo() --- this undoes the entirety of HairNet
        # Switch to object mode, flush edits, switch to edit mode, create particle and undo. This messed up the final particle again.
        # Tried .delete() and .remove() on the particle (even though I knew those weren't commands, I was desperate)
        # Set the brush edit parameters to random values
        # Duplicate the particle system and remove it instead of creating a new particle
        # Switching to the cut brush and use it after creating the particle (even at very large size values it has no effect on any particles)
        # Switching to every other type of brush to see if it would mimic the effect

        # This is the best way I've found to get rid of the final particle. If you have a better solution please pull request it :D

        # This function can't solely be contained in the loop when we make the hair in case the user is adding to an existing system. I'm adding 10 because I'm superstitious of some small error in the particle system API with adding only 1        
        longest_particle = self.get_longest_particle(context)
        bpy.context.scene.tool_settings.particle_edit.default_key_count = longest_particle + 10

        self.evaluate_dependency_graph(context)
        bpy.ops.particle.brush_edit(stroke=[{"name":"", "location":(0, 0, 0), "mouse":(x, y), "mouse_event":(0, 0), "pressure":0, "size":0, "x_tilt":0, "y_tilt":0, "time":0, "is_start":False}], pen_flip=False)#
        self.evaluate_dependency_graph(context)

        bpy.ops.particle.select_roots(action='SELECT')

        # This could be longest particle - 1, but once again, superstitious with the particle system API
        for i in range(0,longest_particle):
            bpy.ops.particle.select_more()

        bpy.ops.particle.select_all(action='INVERT')
        bpy.ops.particle.select_linked()
        bpy.ops.particle.delete(type='PARTICLE')

    def get_longest_particle(self, context):
        '''Returns the number of keys of the particle in the hair system that contains the most hair keys'''
        ps = self.evaluate_dependency_graph(context)
        longest_particle = 0
        for i in range(0, len(ps.particles)):
            if longest_particle < len(ps.particles[i].hair_keys): longest_particle = len(ps.particles[i].hair_keys)

        return longest_particle
    
    def link_proxies_to_collection(self, context, proxies):
        '''Link proxies to designated collection and unlinks from other collections. Creates the collection if needed'''
        if context.scene.hn_props.link_to_collection:
            hair_net_collection = self.set_hair_net_collection(context)
            for proxy in proxies:
                for obj_collection in proxy.users_collection:
                    obj_collection.objects.unlink(proxy)
                hair_net_collection.objects.link(proxy)

    def set_hair_net_collection(self, context):
            '''Retrieves the appropriate name, creates (if needed), and links to the scene (if needed) a hair net collection.'''

            if context.scene.hn_props.proxy_collection_name == '':
                context.scene.hn_props.proxy_collection_name = "Hair_Net_Proxies"       
            collection_name =  context.scene.hn_props.proxy_collection_name     

            if bpy.data.collections.get(collection_name) == None:
                hair_net_collection = bpy.data.collections.new(name=collection_name)
            else:
                hair_net_collection = bpy.data.collections.get(collection_name)

            if not context.scene.user_of_id(hair_net_collection):
                context.scene.collection.children.link(hair_net_collection)
            return hair_net_collection

    def hide_proxy_objects(self, context):
        if context.scene.hn_props.hide_proxies:
            for proxy in data.proxy_hair_guides:
                proxy.hide_viewport = True

    def camera_reset(self, context, cam_dist, cam_view, xray_val):
        '''Unfortunately whenever you use particle brush edit it becomes impossible (afaik) to reset the camera. I have no idea why, but I'm leaving this camera reset in the code in case this changes in the future (and so that people are aware of the issue)'''
        bpy.context.area.spaces.active.shading.show_xray = xray_val
        context.region_data.view_distance = cam_dist
        context.region_data.view_matrix = cam_view

    #endregion

def register():
    bpy.utils.register_class(HAIRNET_OT_operator)

def unregister():
    bpy.utils.unregister_class(HAIRNET_OT_operator)