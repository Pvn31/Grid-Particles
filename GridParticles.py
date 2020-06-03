bl_info = {
    "name": "Grid Particles",
    "author": "Pvn31",
    "version": (0, 1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar(N-panel) > GridParticles",
    "description": "Simulates particles in grid like manner.",
    "warning": "Might not properly work with other add-on which uses handlers.",
    "wiki_url": "",
    "category": "Simulation",
}


import bpy
import random as r

import gpu
from gpu_extras.batch import batch_for_shader

global VGobj
VGobj = None

global vizHandler
vizHandler = None

global batch
batch = None

global shader
shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')

coords=[]
indices=[]

def opposite(a,b):
#    return (a*c+b*d)<0
    return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]<0


#----------------------------------------
#----Functions for Drawing/Visulizing----
#----------------------------------------
def setCoordIndices():
    resX = VGobj.resX
    resY = VGobj.resY
    resZ = VGobj.resZ
    
#    print(VGobj.dimX)
    voxelsizeX = VGobj.voxelsizeX
#    print("setCoordX",voxelsizeX)
    voxelsizeY = VGobj.voxelsizeY
#    print("setCoordY",voxelsizeY)
    voxelsizeZ = VGobj.voxelsizeZ
#    print("setCoordZ",voxelsizeZ)
    
    global coords
    global indices
    
    coords = []
    indices = []

    for k in range(resZ+1):
        for j in range(resY+1):
            for i in range(resX+1):
                coords.append((i*voxelsizeX,j*voxelsizeY,k*voxelsizeZ))
    coords = tuple(coords)
    
    
    max_2d = (resX+1) * (resY+1)
    max_1d = resX+1
    
    for k in range(resZ+1):
        for j in range(resY+1):
            for i in range(resX+1):
                if(i == resX and j == resY and k == resZ):
                    pass
                elif(i == resX and j == resY):
                    indices.append(((k*max_2d + j*max_1d + i),(((k+1)*max_2d) + (j*max_1d) + (i)))) ##Z axis line
                elif(j == resY and k == resZ):
                    indices.append(((k*max_2d + j*max_1d + i),(k*max_2d + j*max_1d + i+1))) ##x axis line
                elif(k == resZ and i == resX):
                    indices.append(((k*max_2d + j*max_1d + i),((k*max_2d) + ((j+1)*max_1d) + i))) ##Y axis line        
                elif(i == resX):
                    indices.append(((k*max_2d + j*max_1d + i),((k*max_2d) + ((j+1)*max_1d) + i))) ##Y axis line
                    indices.append(((k*max_2d + j*max_1d + i),(((k+1)*max_2d) + (j*max_1d) + (i))))##Z axis line
                elif(j == resY):
                    indices.append(((k*max_2d + j*max_1d + i),(k*max_2d + j*max_1d + i+1))) ##x axis line
                    indices.append(((k*max_2d + j*max_1d + i),(((k+1)*max_2d) + (j*max_1d) + (i)))) ##Z axis line
                elif(k == resZ):    
                    indices.append(((k*max_2d + j*max_1d + i),(k*max_2d + j*max_1d + i+1))) ##x axis line
                    indices.append(((k*max_2d + j*max_1d + i),((k*max_2d) + ((j+1)*max_1d) + i))) ##Y axis line
                else:  
                    indices.append(((k*max_2d + j*max_1d + i),(k*max_2d + j*max_1d + i+1))) ##x axis line
                    indices.append(((k*max_2d + j*max_1d + i),((k*max_2d) + ((j+1)*max_1d) + i))) ##Y axis line
                    indices.append(((k*max_2d + j*max_1d + i),(((k+1)*max_2d) + (j*max_1d) + (i)))) ##Z axis line
 
#---------------
def createBatch():
    setCoordIndices()
    global batch
    batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
#---------------
def draw():
    global batch
    global shader
    shader.bind()
    color = bpy.context.scene.VG.color
    shader.uniform_float("color", (color[0],color[1],color[2],1.0))
    batch.draw(shader)    

#--------------------------
#----IMPORTANT FUNCTIONS----
#--------------------------
def particleSetter(scene,degp):
    
    if not (VGobj):
        return
    #EmitterObject
    object = scene.emitter
    if not (object):
        return
    # Evaluate the depsgraph (Important step)
    particle_systems = object.evaluated_get(degp).particle_systems
    if(len(particle_systems) == 0):
        return
    # All particles of first particle-system which has index "0"
    particles = particle_systems[0].particles
    # Total Particles
    totalParticles = len(particles)

    scene = bpy.context.scene
    cFrame = scene.frame_current
    sFrame = scene.frame_start
    
    #at start-frame, clear the particle cache
    if cFrame == sFrame:
        psSeed = object.particle_systems[0].seed 
        object.particle_systems[0].seed  = psSeed

    # length of 1D array or list = 3*totalParticles, "3" due to XYZ in vector/location.
    # If the length is wrong then it will give you an error "internal error setting the array"
    flatLocation = [0]*(3*totalParticles)
    flatVelocity = [0]*(3*totalParticles)
    # To get the loaction,velocity of all particles
    particles.foreach_get("location", flatLocation)
    particles.foreach_get("velocity", flatVelocity)


    for i in range(0,len(flatVelocity),3):
        if not(flatLocation[i]<0 or flatLocation[i]>VGobj.dimX or 
            flatLocation[i+1]<0 or flatLocation[i+1] > VGobj.dimY or 
            flatLocation[i+2]<0 or flatLocation[i+2] > VGobj.dimZ):        

            I = int(flatLocation[i]//VGobj.voxelsizeX)
            J = int(flatLocation[i+1]//VGobj.voxelsizeY)
            K = int(flatLocation[i+2]//VGobj.voxelsizeZ)
            
            flatVelocity[i] = VGobj.grid[K][J][I].dirvec[0]
            flatVelocity[i+1] = VGobj.grid[K][J][I].dirvec[1] 
            flatVelocity[i+2] = VGobj.grid[K][J][I].dirvec[2]   
    particles.foreach_set("velocity", flatVelocity)        

def remove_handler():
    global vizHandler
    if(vizHandler):
        bpy.types.SpaceView3D.draw_handler_remove(vizHandler,'WINDOW')
        vizHandler = None


#---------------------------------------    
#----Update Functions for Properties----
#---------------------------------------
def updateProp_viz(self,context):
    viz = context.scene.VG.viz
    global vizHandler
    if(viz):
        if(VGobj):
        #Adding handler---
            createBatch()
            vizHandler = bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'PRE_VIEW')
    else:
        #Removing Handler
        remove_handler()
            
def updateProp_dimX(self,context):
    if(VGobj):
        VGobj.update_dimX(context.scene.VG.dimX)
#        print(VGobj.dimX)
    if(context.scene.VG.viz):
        createBatch()
    
def updateProp_dimY(self,context):
    if(VGobj):
        VGobj.update_dimY(context.scene.VG.dimY)
#        print(VGobj.dimY)
    if(context.scene.VG.viz):
        createBatch()

def updateProp_dimZ(self,context):
    if(VGobj):
        VGobj.update_dimZ(context.scene.VG.dimZ)
#        print(VGobj.dimZ)
    if(context.scene.VG.viz):
        createBatch()

def updateProp_resX(self,context):
    if(VGobj):
        VGobj.update_resX(context.scene.VG.resX)
        VGobj.generate()
        VGobj.populate()
#        print(VGobj.resX)
    if(context.scene.VG.viz):
        createBatch()

def updateProp_resY(self,context):
    if(VGobj):
        VGobj.update_resY(context.scene.VG.resY)
        VGobj.generate()
        VGobj.populate()
#        print(VGobj.resY)
    if(context.scene.VG.viz):
        createBatch()
    
def updateProp_resZ(self,context):
    if(VGobj):
        VGobj.update_resZ(context.scene.VG.resZ)
        VGobj.generate()
        VGobj.populate()
#        print(VGobj.resZ)
    if(context.scene.VG.viz):
        createBatch()

#-----------------------------
#--------CUSTOM-CLASSES-------
#-----------------------------
class VoxelGrid:
    
    def __init__(self, dimX=5, dimY=5, dimZ=5 ,locX=0, locY=0, locZ=0, resX=5, resY=5, resZ=5):
        self.dimX = dimX
        self.dimY = dimY
        self.dimZ = dimZ
        
        self.locX = locX
        self.locY = locY
        self.locZ = locZ
        
        self.resX = resX
        self.resY = resY
        self.resZ = resZ
        
        self.voxelsizeX = dimX/resX
        self.voxelsizeY = dimY/resY
        self.voxelsizeZ = dimZ/resZ
        print("Intialzed")

#Generating the 3d list containing voxel objects 
    def generate(self):
        self.grid = []
        
        for k in range(0,self.resZ):
            sheet=[]
            for j in range(0,self.resY):
                row=[]
                for i in range(0,self.resX):
                    row.append(Voxel((k,j,i),i*self.voxelsizeX,j*self.voxelsizeY,k*self.voxelsizeZ))
                sheet.append(row)            
            self.grid.append(sheet)
        print("Generared")

#Assigning direction vector to each voxel object in the list that is generated by "generate()"
    def populate(self):
        self.availDirection = [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
        
        for k in range(self.resZ):
            for j in range(self.resY):
                for i in range(self.resX):
                    assigned = self.assign(k,j,i)
                    assX,assY,assZ = assigned[0],assigned[1],assigned[2]
#                    print(k+assZ,j+assY,i+assX)
                    if (k+assZ >= 0 and j+assY >= 0 and i+assX >= 0 and k+assZ < self.resZ and j+assY < self.resY and i+assX < self.resX): # check if it is boundary and assigned vector is pointing inside
                        neighbour = self.grid[k+assZ][j+assY][i+assX].dirvec
                        # first check if neighbour vector has assigned or not then 
                        #check if assigned and neighbour vec are opposite or not
                        if(neighbour and opposite(assigned,neighbour)): 
                            self.assign(k,j,i)
        print("Populated")                    

    def assign(self,k,j,i):
        self.grid[k][j][i].dirvec = r.choice(self.availDirection)
        return self.grid[k][j][i].dirvec
    
    def update_dimX(self,dimX):
        self.dimX = dimX
        self.voxelsizeX = self.dimX/self.resX
    
    def update_dimY(self,dimY):
        self.dimY = dimY
        self.voxelsizeY = self.dimY/self.resY
    
    def update_dimZ(self,dimZ):
        self.dimZ = dimZ
        self.voxelsizeZ = self.dimZ/self.resZ
            
    def update_resX(self,resX):
        self.resX = resX
        self.voxelsizeX = self.dimX/self.resX
    
    def update_resY(self,resY):
        self.resY = resY
        self.voxelsizeY = self.dimY/self.resY
    
    def update_resZ(self,resZ):
        self.resZ = resZ
        self.voxelsizeZ = self.dimZ/self.resZ
                
class Voxel:
#index --> index in list
#x --> x position
#y --> y position
    def __init__(self,index,x,y,z):
        self.index = index
        self.x = x
        self.y = y
        self.z = z
        self.dirvec = None


#-----------------------------
#----------OPERATORS----------
#-----------------------------

class VGRID_OT_newvoxelgrid(bpy.types.Operator):
    """Create a new VoxelGrid. Needs a Emitter."""
    bl_idname = "vgrid.newvoxelgrid"
    bl_label = "New VoxelGrid"
    
    @classmethod 
    def poll(cls, context): 
        ob = context.scene.emitter
        return ob and ob.type == 'MESH'
    
    def execute(self, context):
        global VGobj
        VG = context.scene.VG
        
        VGobj = VoxelGrid(VG.dimX,VG.dimY,VG.dimZ,VG.locX,VG.locY,VG.locZ,VG.resX,VG.resY,VG.resZ)
        VGobj.generate()
        VGobj.populate()
        
        #clear the post frame handler
        print("---Clear handler---newvoxelgrid---")
        bpy.app.handlers.frame_change_post.clear() 
        #run the function on each frame
        print("---Append handler---newvoxelgrid---")
        bpy.app.handlers.frame_change_post.append(particleSetter)
        return {'FINISHED'}

class VGRID_OT_delvoxelgrid(bpy.types.Operator):
    """Delete a VoxelGrid"""
    bl_idname = "vgrid.delvoxelgrid"
    bl_label = "Delete VoxelGrid"
    
    @classmethod 
    def poll(cls, context): 
        return VGobj
    
    def execute(self, context):
        global VGobj
        VGobj = None
        #clear the post frame handler
        print("---Clear handler---delvoxelgrid---")
        remove_handler()
        return {'FINISHED'}

#-----------------------------
#-----------PANELS------------
#-----------------------------
class VGRID_PT_voxelgridMain(bpy.types.Panel):
    """Creates a Panel in the VIEW_3D n-panel"""
    bl_label = "Voxel Grid Main"
    bl_idname = "VGRID_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Grid Particles"

    def draw(self, context):
        layout = self.layout
        emitter = context.scene.emitter
        if(emitter):
            if context.scene.objects.get(emitter.name) == None:
                # That means that the object has been deleted from the
                # scene graph, therefore remove it explicitly
                bpy.data.objects.remove(emitter)
                print("---removing handle---panel")
                remove_handler()
        
        row = layout.row()
        row.prop(context.scene,"emitter")
        
        row = layout.row()
        row.operator("vgrid.newvoxelgrid")
        
        row = layout.row()
        row.operator("vgrid.delvoxelgrid")

class VGRID_PT_voxelgridProps(bpy.types.Panel):
    """Creates a Panel in the VIEW_3D n-panel"""
    bl_label = "Voxel Grid Properties"
    bl_idname = "VGRID_PT_props"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Grid Particles"

    def draw(self, context):
        VG = bpy.context.scene.VG
        
        layout = self.layout
        
        if(VGobj):
            row = layout.row()
            row.label(text="Dimension : ")
            col = layout.column(align=True)
            col.prop(VG, "dimX",text="X")
            col.prop(VG, "dimY",text="Y")
            col.prop(VG, "dimZ",text="Z")
        
#           row = layout.row()
#           row.label(text="Location : ")
#           col = layout.column(align=True)
#           col.prop(VG, "locX",text="X")
#           col.prop(VG, "locY",text="Y")
#           col.prop(VG, "locZ",text="Z")
        
            row = layout.row()
            row.label(text="Resolution : ")
            col = layout.column(align=True)
            col.prop(VG, "resX",text="X")
            col.prop(VG, "resY",text="Y")
            col.prop(VG, "resZ",text="Z")
        
            row = layout.row(align=True)
            row.label(text="Seed: ")
            row.prop(VG,"seed",text="")
        
            col = layout.column(align=True)
            col.prop(VG, "viz")
            col.prop(VG, "color")
        else:
            row = layout.row()
            row.label(text="--- No VoxelGrid Object Avail ---")

#-----------------------------
#----------PROPERTIES----------
#-----------------------------
class VoxelGridProperties(bpy.types.PropertyGroup):
    #Dimension Properties
    dimX : bpy.props.FloatProperty(
        name="DimensionX",
        description = "Dimension of the virtual grid in X direction",
        default = 5,
        min = 0.1,
        max = 1000,
        soft_max = 100,
        update = updateProp_dimX,
    )
    dimY : bpy.props.FloatProperty(
        name="DimensionY",
        description = "Dimension of the virtual grid in Y direction",
        default = 5,
        min = 0.1,
        max = 1000,
        soft_max = 100,
        update = updateProp_dimY,
    )
    dimZ : bpy.props.FloatProperty(
        name="DimensionZ",
        description = "Dimension of the virtual grid in Z direction",
        default = 5,
        min = 0.1,
        max = 1000,
        soft_max = 100,
        update = updateProp_dimZ,
    )
    #Location Properties
    locX : bpy.props.FloatProperty(
        name="LocationX",
        description = "Location of the virtual grid on X Axis",
        default = 0,
    )
    locY : bpy.props.FloatProperty(
        name="LocationY",
        description = "Location of the virtual grid on Y Axis",
        default = 0,
    )
    locZ : bpy.props.FloatProperty(
        name="LocationZ",
        description = "Location of the virtual grid on Z Axis",
        default = 0,
    )
    #Rotation Properties
    resX : bpy.props.IntProperty(
        name="ResolutionX",
        description = "Resolution of virtual grid in X axis.",
        default = 8,
        min = 1,
        max = 1000,
        soft_max = 25,
        update = updateProp_resX,
    )
    resY : bpy.props.IntProperty(
        name="ResolutionY",
        description = "Resolution of virtual grid in Y axis.",
        default = 8,
        min = 1,
        max = 1000,
        soft_max = 25,
        update = updateProp_resY,
    )
    resZ : bpy.props.IntProperty(
        name="ResolutionZ",
        description = "Resolution of virtual grid in Z axis.",
        default = 8,
        min = 1,
        max = 1000,
        soft_max = 25,
        update = updateProp_resZ,
    )
    #seed for the randomiztion
    seed : bpy.props.IntProperty(
        name="Seed",
        description = "Seed for the direction vectors in virtual grid. Need to create new VoxelGrid to take actual effect.",
        default = 0,
    )
    viz : bpy.props.BoolProperty(
        name="Visulization",
        description = "Visulization of virtual grid.",
        default = False,
        update = updateProp_viz,
    )
    color : bpy.props.FloatVectorProperty(
        name="Color",
        description = "Color of visulization grid",
        default=(0.0 ,0.0, 0.0),
        subtype='COLOR',
        min=0.0,
        max=1.0,
    )
        
classes=(
    VoxelGridProperties,
    VGRID_OT_newvoxelgrid,
    VGRID_OT_delvoxelgrid,
    VGRID_PT_voxelgridMain,
    VGRID_PT_voxelgridProps,
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.VG = bpy.props.PointerProperty(type = VoxelGridProperties)
    bpy.types.Scene.emitter = bpy.props.PointerProperty(name="emitter",description="Object that emits paticles",type = bpy.types.Object)
    

def unregister():
    remove_handler()
    del bpy.types.Scene.VG
    del bpy.types.Scene.emitter
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
if __name__ == "__main__":
    register()