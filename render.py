import bpy

scene = bpy.context.scene
fr_start = scene.frame_start
fr_end = scene.frame_end
for i in range(fr_start,fr_end+1):
    scene.frame_set(i)
    scene.render.filepath = "//Render/" + str(i)
    bpy.ops.render.render(write_still =True)