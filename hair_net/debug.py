class Debug:
    def print_vertedges(vert_edges):
        print('vert_edges: ')
        for vert in vert_edges:
            print(vert, ': ', vert_edges[vert])

    def print_edgefaces(edge_faces):
        print('edge_faces: ')
        for edge in edge_faces:
            print(edge, ': ', edge_faces[edge])

    def print_edgekeys(edges):
        for edge in edges:
            print(edge, ' : ', edge.key)

    def sortedges(edgesList):
        sorted = []
        print_edgekeys(edgesList)

        return edgesList

    def print_hairguides(hairGuides):
        print('Hair Guides:')
        guideN=0

        for group in hairGuides:
            print('Guide #',guideN)
            i=0
            for guide in group:
                print(i, ' : ', guide)
                i += 1
            guideN+=1

    def print_seams(seamVerts, seamEdges):
        print('Verts in the seam: ')
        for vert in seamVerts:
            print(vert)
        print('Edges in the seam: ')
        for edge in seamEdges:
            print(edge.key)

    def print_loc(func=''):
        obj = bpy.context.object
        print(obj.name, ' ', func)
        print('Coords', obj.data.vertices[0].co)

    def get_edgefromkey(mesh,key):
        v1 = key[0]
        v2 = key[1]
        theEdge = 0
        for edge in mesh.edges:
            if v1 in edge.vertices and v2 in edge.vertices:
                #print('Found edge :', edge.index)
                return edge
        return 0