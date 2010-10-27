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

bl_addon_info = {
    "name": "Cloud Generator",
    "author": "Nick Keeline(nrk)",
    "version": (0,7),
    "blender": (2, 5, 3),
    "api": 31965,
    "location": "Tool Shelf ",
    "description": "Creates Volumetric Clouds",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Object/Cloud_Gen",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=22015&group_id=153&atid=469",
    "category": "Object"}

"""
Place this file in the .blender/scripts/addons dir
You have to activated the script in the "Add-Ons" tab (user preferences).
The functionality can then be accessed via the Tool shelf when objects
are selected

Rev 0 initial release
Rev 0.1 added scene to create_mesh per python api change.
Rev 0.2 Added Point Density turbulence and fixed degenerate
Rev 0.3 Fixed bug in degenerate
Rev 0.4 updated for api change/changed to new apply modifier technique
Rev 0.5 made particle count equation with radius so radius increases with cloud volume
Rev 0.6 added poll function to operator, fixing crash with no selected objects
Rev 0.7 added particles option and Type of Cloud wanted selector
"""

import bpy
import mathutils
from math import *
from bpy.props import *


# This routine takes an object and deletes all of the geometry in it
# and adds a bounding box to it.
# It will add or subtract the bound box size by the variable sizeDifference.
def makeObjectIntoBoundBox(object, sizeDifference):
    # Deselect All
    bpy.ops.object.select_all(action='DESELECT')

    # Select the object
    object.select = True

    # Go into Edit Mode
    bpy.ops.object.mode_set(mode='EDIT')

    mesh = object.data
    verts = mesh.vertices

    #Set the max and min verts to the first vertex on the list
    maxVert = [verts[0].co[0], verts[0].co[1], verts[0].co[2]]
    minVert = [verts[0].co[0], verts[0].co[1], verts[0].co[2]]

    #Create Max and Min Vertex array for the outer corners of the box
    for vert in verts:
        #Max vertex
        if vert.co[0] > maxVert[0]:
            maxVert[0] = vert.co[0]
        if vert.co[1] > maxVert[1]:
            maxVert[1] = vert.co[1]
        if vert.co[2] > maxVert[2]:
            maxVert[2] = vert.co[2]

        #Min Vertex
        if vert.co[0] < minVert[0]:
            minVert[0] = vert.co[0]
        if vert.co[1] < minVert[1]:
            minVert[1] = vert.co[1]
        if vert.co[2] < minVert[2]:
            minVert[2] = vert.co[2]

    #Add the size difference to the max size of the box
    maxVert[0] = maxVert[0] + sizeDifference
    maxVert[1] = maxVert[1] + sizeDifference
    maxVert[2] = maxVert[2] + sizeDifference

    #subtract the size difference to the min size of the box
    minVert[0] = minVert[0] - sizeDifference
    minVert[1] = minVert[1] - sizeDifference
    minVert[2] = minVert[2] - sizeDifference

    #Create arrays of verts and faces to be added to the mesh
    addVerts = []

    #X high loop
    addVerts.append([maxVert[0], maxVert[1], maxVert[2]])
    addVerts.append([maxVert[0], maxVert[1], minVert[2]])
    addVerts.append([maxVert[0], minVert[1], minVert[2]])
    addVerts.append([maxVert[0], minVert[1], maxVert[2]])

    #x low loop
    addVerts.append([minVert[0], maxVert[1], maxVert[2]])
    addVerts.append([minVert[0], maxVert[1], minVert[2]])
    addVerts.append([minVert[0], minVert[1], minVert[2]])
    addVerts.append([minVert[0], minVert[1], maxVert[2]])

    # Make the faces of the bounding box.
    addFaces = []

    # Draw a box on paper and number the vertices.
    # Use right hand rule to come up with number orders for faces on
    # the box (with normals pointing out).
    addFaces.append([0, 3, 2, 1])
    addFaces.append([4, 5, 6, 7])
    addFaces.append([0, 1, 5, 4])
    addFaces.append([1, 2, 6, 5])
    addFaces.append([2, 3, 7, 6])
    addFaces.append([0, 4, 7, 3])

    # Delete all geometry from the object.
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.delete(type='ALL')

    # Must be in object mode for from_pydata to work
    bpy.ops.object.mode_set(mode='OBJECT')

    # Add the mesh data.
    mesh.from_pydata(addVerts, [], addFaces)

    # Update the mesh
    mesh.update()


def applyScaleRotLoc(scene, obj):
    # Deselect All
    bpy.ops.object.select_all(action='DESELECT')

    # Select the object
    obj.select = True
    scene.objects.active = obj

    #bpy.ops.object.rotation_apply()
    bpy.ops.object.location_apply()
    bpy.ops.object.scale_apply()


def totallyDeleteObject(scene, obj):
    scene.objects.unlink(obj)
    bpy.data.objects.remove(obj)


def makeParent(parentobj, childobj, scene):

    applyScaleRotLoc(scene, parentobj)

    applyScaleRotLoc(scene, childobj)

    childobj.parent = parentobj

    #childobj.location = childobj.location - parentobj.location


def addNewObject(scene, name, copyobj):
    '''
    Add an object and do other silly stuff.
    '''
    # Create new mesh
    mesh = bpy.data.meshes.new(name)

    # Create a new object.
    ob_new = bpy.data.objects.new(name, mesh)
    tempme = copyobj.data
    ob_new.data = tempme.copy()
    ob_new.scale = copyobj.scale
    ob_new.location = copyobj.location

    # Link new object to the given scene and select it.
    scene.objects.link(ob_new)
    ob_new.select = True

    return ob_new


def combineObjects(scene, combined, listobjs):
    # scene is the current scene
    # combined is the object we want to combine everything into
    # listobjs is the list of objects to stick into combined

    # Deselect All
    bpy.ops.object.select_all(action='DESELECT')

    # Select the new object.
    combined.select = True
    scene.objects.active = combined

    # Add data
    if (len(listobjs) > 0):
            for i in listobjs:
                # Add a modifier
                bpy.ops.object.modifier_add(type='BOOLEAN')

                union = combined.modifiers
                union[0].name = "AddEmUp"
                union[0].object = i
                union[0].operation = 'UNION'

                # Apply modifier
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier=union[0].name)


# Returns True if we want to degenerate
# and False if we want to generate a new cloud.
def degenerateCloud(obj):
    if not obj:
        return False

    if "CloudMember" in obj:
        if obj["CloudMember"] != None:
            if obj.parent:
               if "CloudMember" not in obj.parent:
                return False

            else:
                return True

    return False


class VIEW3D_PT_tools_cloud(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    bl_label = "Cloud Generator"
    bl_context = "objectmode"

    def draw(self, context):
        active_obj = context.active_object
        layout = self.layout
        col = layout.column(align=True)

        degenerate = degenerateCloud(active_obj)

        if active_obj and degenerate:

            col.operator("cloud.generate_cloud", text="DeGenerate")

        elif active_obj is None:

            col.label(text="Select one or more")
            col.label(text="objects to generate")
            col.label(text="a cloud.")

        elif "CloudMember" in  active_obj:

            col.label(text="Must select")
            col.label(text="bound box")
           
        elif active_obj and active_obj.type == 'MESH':

            col.operator("cloud.generate_cloud", text="Generate Cloud")

            col.prop(context.scene, "cloudparticles")
            col.prop(context.scene, "cloud_type")
        else:
            col.label(text="Select one or more")
            col.label(text="objects to generate")
            col.label(text="a cloud.")


class GenerateCloud(bpy.types.Operator):
    bl_idname = "cloud.generate_cloud"
    bl_label = "Generate Cloud"
    bl_description = "Create a Cloud."
    bl_register = True
    bl_undo = True

    @classmethod
    def poll(cls, context):
        if not context.active_object:
            return False
        else:
            return (context.active_object.type=='MESH')

    def execute(self, context):
        # Make variable that is the current .blend file main data blocks
        blend_data = context.blend_data

        # Make variable that is the active object selected by user
        active_object = context.active_object

        # Make variable scene that is current scene
        scene = context.scene

        # Parameters the user may want to change:
        # Number of points this number is multiplied by the volume to get
        # the number of points the scripts will put in the volume.
        numOfPoints = 1.0
        maxNumOfPoints = 100000
        scattering = 2.5
        pointDensityRadiusFactor = 1.0
        densityScale = 1.5

        # Should we degnerate?
        degenerate = degenerateCloud(active_object)

        if degenerate:
           # Degenerate Cloud
           mainObj = active_object

           cloudMembers = active_object.children

           createdObjects = []
           definitionObjects  = []
           for member in cloudMembers:
               applyScaleRotLoc(scene, member)
               if (member["CloudMember"] == "CreatedObj"):
                  createdObjects.append(member)
               else:
                  definitionObjects.append(member)

           for defObj in definitionObjects:
               #Delete cloudmember data from objects
               if "CloudMember" in defObj:
                  del(defObj["CloudMember"])

           for createdObj in createdObjects:
               totallyDeleteObject(scene, createdObj)

           # Delete the blend_data object
           totallyDeleteObject(scene, mainObj)

           # Select all of the left over boxes so people can immediately
           # press generate again if they want.
           for eachMember in definitionObjects:
               eachMember.draw_type = 'SOLID'
               eachMember.select = True
               eachMember.hide_render = False
        else:
            # Generate Cloud

            ###############Create Combined Object bounds##################
            # Make a list of all Selected objects.
            selectedObjects = bpy.context.selected_objects
            if not selectedObjects:
                selectedObjects = [bpy.context.active_object]

            # Create a new object bounds
            bounds = addNewObject(scene,
                    "CloudBounds",
                    selectedObjects[0])

            bounds.draw_type = 'BOUNDS'
            bounds.hide_render = False

            # Just add a Definition Property designating this
            # as the blend_data object.
            bounds["CloudMember"] = "MainObj"

            # Since we used iteration 0 to copy with object we
            # delete it off the list.
            firstObject = selectedObjects[0]
            del selectedObjects[0]

            # Apply location Rotation and Scale to all objects involved.
            applyScaleRotLoc(scene, bounds)
            for each in selectedObjects:
                applyScaleRotLoc(scene, each)

            # Let's combine all of them together.
            combineObjects(scene, bounds, selectedObjects)

            # Let's add some property info to the objects.
            for selObj in selectedObjects:
                selObj["CloudMember"] = "DefinitioinObj"
                selObj.name = "DefinitioinObj"
                selObj.draw_type = 'WIRE'
                selObj.hide_render = True
                makeParent(bounds, selObj, scene)

            # Do the same to the 1. object since it is no longer in list.
            firstObject["CloudMember"] = "DefinitioinObj"
            firstObject.name = "DefinitioinObj"
            firstObject.draw_type = 'WIRE'
            firstObject.hide_render = True
            makeParent(bounds, firstObject, scene)

            ###############Create Cloud for putting Cloud Mesh############
            # Create a new object cloud.
            cloud = addNewObject(scene, "CloudMesh", bounds)
            cloud["CloudMember"] = "CreatedObj"
            cloud.draw_type = 'WIRE'
            cloud.hide_render = True

            makeParent(bounds, cloud, scene)

            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.subdivide(number_cuts=2, fractal=0, smoothness=1)
            bpy.ops.object.location_apply()
            bpy.ops.mesh.vertices_smooth(repeat=20)
            bpy.ops.mesh.tris_convert_to_quads()
            bpy.ops.mesh.faces_shade_smooth()
            bpy.ops.object.editmode_toggle()

            ###############Create Particles in cloud obj##################
            # Turn off gravity.
            scene.use_gravity = False

            # Set time to 0.
            scene.frame_current = 0

            # Add a new particle system.
            bpy.ops.object.particle_system_add()

            #Particle settings setting it up!
            cloudParticles = cloud.particle_systems.active
            cloudParticles.name = "CloudParticles"
            cloudParticles.settings.frame_start = 0
            cloudParticles.settings.frame_end = 0
            cloudParticles.settings.emit_from = 'VOLUME'
            cloudParticles.settings.draw_method = 'DOT'
            cloudParticles.settings.render_type = 'NONE'
            cloudParticles.settings.normal_factor = 0
            cloudParticles.settings.distribution = 'RAND'
            cloudParticles.settings.physics_type = 'NO'

            ####################Create Volume Material####################
            # Deselect All
            bpy.ops.object.select_all(action='DESELECT')

            # Select the object.
            bounds.select = True
            scene.objects.active = bounds

            # Turn bounds object into a box.
            makeObjectIntoBoundBox(bounds, .6)

            # Delete all material slots in bounds object.
            for i in range(len(bounds.material_slots)):
                bounds.active_material_index = i - 1
                bpy.ops.object.material_slot_remove()

            # Add a new material.
            cloudMaterial = blend_data.materials.new("CloudMaterial")
            bpy.ops.object.material_slot_add()
            bounds.material_slots[0].material = cloudMaterial

            # Set Up the Cloud Material
            cloudMaterial.name = "CloudMaterial"
            cloudMaterial.type = 'VOLUME'
            mVolume = cloudMaterial.volume
            mVolume.scattering = scattering
            mVolume.density = 0
            mVolume.density_scale = densityScale
            mVolume.transmission_color = [3, 3, 3]
            mVolume.step_size = 0.1
            mVolume.use_light_cache = True
            mVolume.cache_resolution = 75

            # Add a texture
            vMaterialTextureSlots = cloudMaterial.texture_slots
            cloudtex = blend_data.textures.new("CloudTex", type='CLOUDS')
            cloudtex.noise_type = 'HARD_NOISE'
            cloudtex.noise_scale = 2
            mtex = cloudMaterial.texture_slots.add()
            mtex.texture = cloudtex
            mtex.texture_coords = 'ORCO'
            mtex.use_map_color_diffuse = True

            # Add a force field to the points.
            cloudField = bounds.field
            cloudField.type = 'TEXTURE'
            cloudField.strength = 2
            cloudField.texture = cloudtex

            # Set time
            #for i in range(12):
            #    scene.current_frame = i
            #    scene.update()
            scene.frame_current = 1

            #bpy.ops.ptcache.bake(bake=False)

            # Add a Point Density texture
            pDensity = blend_data.textures.new("CloudPointDensity", 'POINT_DENSITY')
            
            mtex = cloudMaterial.texture_slots.add()
            mtex.texture = pDensity
            mtex.texture_coords = 'GLOBAL'
            mtex.use_map_density = True
            mtex.use_rgb_to_intensity = True
            mtex.texture_coords = 'GLOBAL'

            pDensity.point_density.vertex_cache_space = 'WORLD_SPACE'
            pDensity.point_density.use_turbulence = True
            pDensity.point_density.noise_basis = 'VORONOI_F2'
            pDensity.point_density.turbulence_depth = 3

            pDensity.use_color_ramp = True
            pRamp = pDensity.color_ramp
            #pRamp.use_interpolation = 'LINEAR'
            pRampElements = pRamp.elements
            #pRampElements[1].position = .9
            #pRampElements[1].color = [.18,.18,.18,.8]
            bpy.ops.texture.slot_move(type='UP')


            # Estimate the number of particles for the size of bounds.
            volumeBoundBox = (bounds.dimensions[0] * bounds.dimensions[1]* bounds.dimensions[2])
            numParticles = int((2.4462 * volumeBoundBox + 430.4) * numOfPoints)
            if numParticles > maxNumOfPoints:
                numParticles = maxNumOfPoints
            if numParticles < 10000:
                numParticles = int(numParticles + 15 * volumeBoundBox)
            print(numParticles)
 
            # Set the number of particles according to the volume
            # of bounds.
            cloudParticles.settings.count = numParticles

            pDensity.point_density.radius = (.00013764 * volumeBoundBox + .3989) * pointDensityRadiusFactor

            # Set time to 1.
            scene.frame_current = 1

            if not scene.cloudparticles:
                ###############Create CloudPnts for putting points in#########
                # Create a new object cloudPnts
                cloudPnts = addNewObject(scene, "CloudPoints", bounds)
                cloudPnts["CloudMember"] = "CreatedObj"
                cloudPnts.draw_type = 'WIRE'
                cloudPnts.hide_render = True

                makeParent(bounds, cloudPnts, scene)

                bpy.ops.object.editmode_toggle()
                bpy.ops.mesh.select_all(action='SELECT')

                bpy.ops.mesh.delete(type='ALL')

                meshPnts = cloudPnts.data

                listCloudParticles = cloudParticles.particles

                listMeshPnts = []
                for pTicle in listCloudParticles:
                    listMeshPnts.append(pTicle.location)

                # Must be in object mode fro from_pydata to work.
                bpy.ops.object.mode_set(mode='OBJECT')

                # Add in the mesh data.
                meshPnts.from_pydata(listMeshPnts, [], [])

                # Update the mesh.
                meshPnts.update()

                # Add a modifier.
                bpy.ops.object.modifier_add(type='DISPLACE')

                cldPntsModifiers = cloudPnts.modifiers
                cldPntsModifiers[0].name = "CloudPnts"
                cldPntsModifiers[0].texture = cloudtex
                cldPntsModifiers[0].texture_coords = 'OBJECT'
                cldPntsModifiers[0].texture_coordinate_object = cloud
                cldPntsModifiers[0].strength = -1.4

                # Apply modifier
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier=cldPntsModifiers[0].name)

                pDensity.point_density.point_source = 'OBJECT'
                pDensity.point_density.object = cloudPnts

                # Deselect All
                bpy.ops.object.select_all(action='DESELECT')

                # Select the object.
                cloud.select = True
                scene.objects.active = cloud

                bpy.ops.object.particle_system_remove()

                # Deselect All
                bpy.ops.object.select_all(action='DESELECT')

            else:
    
                pDensity.point_density.point_source = 'PARTICLE_SYSTEM'
                pDensity.point_density.object = cloud
                pDensity.point_density.particle_system = cloudParticles

            if scene.cloud_type == '1':    #  Cumulous 
                print("Cumulous")
                mVolume.density_scale = 2.22
                pDensity.point_density.turbulence_depth = 10
                pDensity.point_density.turbulence_strength = 6.3
                pDensity.point_density.turbulence_scale = 2.9
                pRampElements[1].position = .606
                pDensity.point_density.radius = pDensity.point_density.radius + .1

            elif scene.cloud_type == '2':    #  Cirrus 
                print("Cirrus")
                pDensity.point_density.turbulence_strength = 22
                mVolume.transmission_color = [3.5, 3.5, 3.5]
                mVolume.scattering = .13

            # Select the object.
            bounds.select = True
            scene.objects.active = bounds

        return {'FINISHED'}


def register():
    bpy.types.Scene.cloudparticles = BoolProperty(
        name="Particles",
        description="Generate Cloud as Particle System",
        default=False)

    bpy.types.Scene.cloud_type = EnumProperty(
        name="Type",
        description="Select the type of cloud to create with material settings",
        items=[("0","Stratus","Generate Stratus_foggy Cloud"),
               ("1","Cumulous","Generate Cumulous_puffy Cloud"),
               ("2","Cirrus","Generate Cirrus_wispy Cloud"),
              ],
        default='0')


def unregister():
    del bpy.types.Scene.cloudparticles
    del bpy.types.Scene.cloud_type


if __name__ == "__main__":
    register()