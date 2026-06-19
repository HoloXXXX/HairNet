# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

#TODO: UPDATE LINK TO DOCS IN MANIFEST (and create them)

bl_info = {
        'name':'Hair Net',
        'author': 'Holo, Rhett Jackson',
        'version': (1,0,0), # Update data.py version string when updating version #
        'blender': (5,0,0),
        'location': '3dView',
        'category': 'Particle',
        'description': 'Converts mesh and curves into hair guides for the particle hair system',
        }

if 'bpy' in locals():
    import importlib
    importlib.reload(data)
    importlib.reload(hair_net)
    importlib.reload(ui)
    print('Hair Net successfully reloaded!')
else:
    import bpy
    from . import data
    data.init()
    from . import (
        hair_net,
        ui,
    )


# ### REGISTER ###

def register():
    data.register()
    hair_net.register()
    ui.register()


def unregister():
    data.unregister()
    hair_net.unregister()
    ui.unregister()

if __name__ == '__main__':
    register()
    print('registering')