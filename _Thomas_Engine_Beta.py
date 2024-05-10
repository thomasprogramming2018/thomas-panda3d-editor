import sys
import os
from multiprocessing import Process, Pipe

import wx

from direct.task import Task
from pandac.PandaModules import WindowProperties
from pandac.PandaModules import loadPrcFileData
from direct.showbase.ShowBase import ShowBase
from panda3d.core import PandaNode, Vec3, Vec4, CollisionRay, CollisionTraverser #CollisionVisualizer
from panda3d.core import *
from panda3d.core import CollisionHandlerQueue
from panda3d.core import GeomLines, GeomVertexData, GeomVertexFormat, Geom, GeomNode
from panda3d.core import Mat4
import complexpbr 



from direct.actor.Actor import Actor

from direct.filter.FilterManager import FilterManager

from panda3d.core import Vec3, Shader

import drag_and_drop_properties

import ast

import subprocess

from pathlib import Path


import wx.lib.scrolledpanel


import json





import panda3d.core

import random

class PandaViewport(wx.Panel):
    """A special Panel which holds a Panda3d window."""
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        # See __doc__ of initialize() for this callback
        self.loaded_models = {"environment.egg(0000)" : "environment.egg(0000)"}
        self.GetTopLevelParent().Bind(wx.EVT_SHOW, self.onShow)

    def onShow(self, event):
        
        if event.IsShown() and self.GetHandle():
            # Windows can't get it right from here. Call it after this function.
            if os.name == "nt":
                wx.CallAfter(self.initialize)
            # All other OSes should be okay with instant init.
            else:
                self.initialize()
        event.Skip()

    def initialize(self):
        """
        This method requires the top most window to be visible, i.e. you called Show()
        on it. Call initialize() after the whole Panel has been laid out and the UI is mostly done.
        It will spawn a new process with a new Panda3D window and this Panel as parent.
        """
        assert self.GetHandle() != 0
        self.pipe, remote_pipe = Pipe()
        w, h = self.ClientSize.GetWidth(), self.ClientSize.GetHeight()
        
        self.panda_process = Process(target=Panda3dApp, args=(w, h, self.GetHandle(), remote_pipe))
        self.panda_process.start()

        self.objectL = Process(target=objectslist, args=(100, 100, self.GetHandle(), remote_pipe))
        
        self.objectL.start()

        self.gfx = ""


        self.create_arrow = ""

        self.Arrow_color = ""

        self.Arrow_direction = ""
        
        self.Arrow_parent = ""

        self.model_name = {}
        
        self.filepathdel = ""

        self.filepath = ""

        

        
        
        # Bind the click event to the function
        
        self.Bind(wx.EVT_SIZE, self.onResize)
        
        self.Bind(wx.EVT_KILL_FOCUS, self.onDefocus)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)
        if isinstance(self.panda_process, wx.Panel):
            self.Bind(wx.EVT_MOUSE_EVENTS, self.panda_process.onMouse)  # If panda_process has onMouse
        else:
            pass
        self.SetFocus()

        # We need to check the pipe for requests frequently
        self.pipe_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.checkPipe, self.pipe_timer)
        
        # Start the timer with an interval of 16 milliseconds (60 times per second)
        self.pipe_timer.Start(16)  # Corrected interval

        

    def onResize(self, event):
        # when the wx-panel is resized, fit the panda3d window into it
        w, h = event.GetSize().GetWidth(), event.GetSize().GetHeight()
        self.pipe.send(["resize", w, h])



    def setObjPos(self, x, y, z, object):
        try:
            self.pipe.send(["setPos", x, y, z, object])
            print("sending")
        except Exception:
            pass
    def setObjRot(self, h, p, r, object):
        self.pipe.send(["setHpr", r, p, h, object])
    
    def setObjScale(self, x, y, z, object):
        self.pipe.send(["setScale", x, y, z, object])



    def createArrowX(self):
        self.pipe.send([self.create_arrow, self.Arrow_color, "x", self.Arrow_parent])
        self.create_arrow = ""
        self.Arrow_color = ""
        self.Arrow_direction = ""
        self.Arrow_parent = ""
    def createArrowY(self):
        self.pipe.send([self.create_arrow, self.Arrow_color, "y", self.Arrow_parent])
        self.create_arrow = ""
        self.Arrow_color = ""
        self.Arrow_direction = ""
        self.Arrow_parent = ""
    def createArrowZ(self):
        self.pipe.send([self.create_arrow, self.Arrow_color, "z", self.Arrow_parent])
        self.create_arrow = ""
        self.Arrow_color = ""
        self.Arrow_direction = ""
        self.Arrow_parent = ""
    
    def onGFX(self):
        self.pipe.send([self.gfx])
        self.gfx = ""
    def onLoad(self):
        self.pipe.send(["filepath", self.filepath, h.model_name])
        print([self.filepath])
        self.filepath = ""

    def onDel(self):
        self.pipe.send(["filepathdel", self.filepathdel])#, self.model_name[self.filepathdel]])
        print([self.filepathdel])
        self.filepathdel = ""

    def onDefocus(self, event):
        f = wx.Window.FindFocus()
        if f:
            # This makes Panda lose keyboard focus
            f.GetTopLevelParent().Raise()

    def onDestroy(self, event):
        self.pipe.send(["close",])
        # Give Panda a second to close itself and terminate it if it doesn't
        self.panda_process.join(1)
        if self.panda_process.is_alive():
            self.panda_process.terminate()

    def checkPipe(self, event):
        # Panda requested focus (and probably already has keyboard focus), so make wx
        # set it officially. This prevents other widgets from being rendered focused.
        
        if self.create_arrow == "models/Arrow.objX":
            self.createArrowX()
        elif self.create_arrow == "models/Arrow.objY":
            self.createArrowY()
        elif self.create_arrow == "models/Arrow.objZ":
            self.createArrowZ()
        elif self.filepathdel != "":
            print("IT WORKS")
            self.onDel()
        elif self.filepath != "":
            self.onLoad()
        elif self.gfx != "":
            self.onGFX()
        if self.pipe.poll():
            
            
            
            request = self.pipe.recv()
            if request == "focus":
                self.SetFocus()
            #if not None in request:
            elif request[0] == "Load":
                model_name = request[1]
                # Update your data structure (e.g., a list or dictionary)
                # in PandaViewport to reflect the loaded model
                self.loaded_models = model_name

                h.model_name[request[2]] = request[3]
                self.model_name[request[3]] = request[2]
                h.refresh_list()
            elif request[0] == "Delete":
                model_name = request[1]

                self.loaded_models = model_name
                h.model_name = self.loaded_models
                for key, value in self.model_name.items():
                    if os.path.basename(key) == model_name:
                        del self.model_name[model_name]
                        del self.loaded_models[model_name]
                h.refresh_list()


class Panda3dApp(object):
    def __init__(self, width, height, handle, pipe):
        """Arguments:
        width -- width of the window
        height -- height of the window
        handle -- parent window handle
        pipe -- multiprocessing pipe for communication
        """
        self.loaded_models = {}
        self.pipe = pipe

        loadPrcFileData("", "window-type none")
        loadPrcFileData("", "audio-library-name null")

        ShowBase()


        wp = WindowProperties()
        wp.setOrigin(0, 0)
        wp.setSize(width, height)
        # This causes warnings on Windows
        #wp.setForeground(True)
        wp.setParentWindow(handle)
        base.openDefaultWindow(props=wp, gsg=None)

        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.myTraverser = CollisionTraverser()
        self.myHandler = CollisionHandlerQueue()
        self.myTraverser.addCollider(self.pickerNP, self.myHandler)

        self.oldmpos = (0,0)

        self.x = False
        self.y = False
        self.z = False


        self.task_done = False


        self.selected = None


        self.arrowx = None


        self.arrowy = None
        self.arrowz = None
        
        
        


        self.Arrows = {}

        self.num = 1

        self.walking = False

        self.w_pressed = False
        self.a_pressed = False
        self.s_pressed = False
        self.d_pressed = False

        self.camRX = base.camera.getR()
        self.camRY = base.camera.getP()
        
        self.mouse_down = False
        self.mouse_down2 = False
        
        self.velocity = Vec3(0, 0, 0)
        self.acceleration = 300.0
        self.maxSpeed = 15.0
        self.friction = 50.0
        self.turnSpeed = 200.0
        
        self.complexpbrPipeline = complexpbr.apply_shader(base.render)


        base.camLens.setNear(0.00001)

        self.loadSmiley()
        
        self.keyMap = {
            "up" : False,
            "down" : False,
            "left" : False,
            "right" : False,
        }
        

        
        
        #self.complexpbrinit = complexpbr.screenspace_init() 
        #
#
        ## make the cubemap rendering dynamic (this is the default state)
        #complexpbr.set_cubebuff_active()


        base.taskMgr.add(self.checkPipe, "check pipe")
        ## Start the update task
        taskMgr.add(self.update_camera, "cameraUpdateTask")
#
        ## def printA():
        ##     print "'a' key recieved by panda"
        ## base.accept("a", printA)
        base.accept("mouse1-up", self.getFocus)
        #
        #
        #
        #self.screen_quad = base.screen_quad
        #
        #bloom_intensity = 0.5  # bloom defaults to 0.0 / off
        #bloom_blur_width = 10
        #bloom_samples = 6
        #bloom_threshold = 0.7
#
        #self.screen_quad.set_shader_input("bloom_intensity", bloom_intensity)
        #self.screen_quad.set_shader_input("bloom_threshold", bloom_threshold)
        #self.screen_quad.set_shader_input("bloom_blur_width", bloom_blur_width)
        #self.screen_quad.set_shader_input("bloom_samples", bloom_samples)
        #
        ## example of how to customize SSR
        #ssr_intensity = 0.5  
        #ssr_step = 4.0
        #ssr_fresnel_pow = 3.0
        #ssr_samples = 128  # ssr_samples defaults to 0 / off
        #
        #self.screen_quad.set_shader_input("ssr_intensity", ssr_intensity)
        #self.screen_quad.set_shader_input("ssr_step", ssr_step)
        #self.screen_quad.set_shader_input("ssr_fresnel_pow", ssr_fresnel_pow)
        #self.screen_quad.set_shader_input("ssr_samples", ssr_samples)
#
#
        ## example of how to customize SSAO
        #ssao_samples = 32  # ssao_samples defaults to 8
        #
        #self.screen_quad.set_shader_input("ssao_samples", ssao_samples)
        #
        ## example of how to HSV adjust the final image
        #.screen_quad.set_shader_input("hsv_g", 1.3)  # hsv_g (saturation factor) defaults to 1.0

        # Step 1: Set up Cubemap Rendering
        #cubemap_size = 512 * 2  # Adjust as needed
        #cubemap_texture = Texture()
        #cubemap_texture.setup_cube_map(cubemap_size, Texture.T_unsigned_byte, Texture.F_rgba)
#
#
        ## Step 2: Create a camera for capturing the environment
        #self.cubemap_camera = base.makeCamera(base.win)
#
        ## Step 3: Render the Scene to Cubemap
        #cubemap_faces = [
        #    (Vec3(1, 0, 0), Vec3(0, -1, 0), "cubemap_right"),
        #    (Vec3(-1, 0, 0), Vec3(0, -1, 0), "cubemap_left"),
        #    (Vec3(0, -1, 0), Vec3(0, 0, -1), "cubemap_up"),
        #    (Vec3(0, 1, 0), Vec3(0, 0, 1), "cubemap_down"),
        #    (Vec3(0, 0, 1), Vec3(0, -1, 0), "cubemap_front"),
        #    (Vec3(0, 0, -1), Vec3(0, -1, 0), "cubemap_back")
        #]
#
        #
#
        #
#
        ## Step 3: Update Cubemap Texture
        ## The cubemap_texture now contains the captured environment data.
#
        #
        #
        ## example of how to modify the specular contribution
        #render.set_shader_input("specular_factor", 10.0)  # the specular_factor defaults to 1.0
        
        #self.complexpbrPipeline = complexpbr.apply_shader(base.render, 1.0, env_res=1024, lut_fill=[1.0,0.0,0.0])
        

        #print(cube_map_faces)
        ## Load each texture separately
        #cube_map_faces_textures = []
        #for file_path in cube_map_faces:
        #    texture = loader.loadTexture(file_path)
        #    if texture:
        #        cube_map_faces_textures.append(texture)
        #    else:
        #        print(f"Failed to load texture: {file_path}")
        #if cube_map_faces_textures:
        #    # Combine the textures into a cube map texture
        #    cube_map_texture = loader.loadCubeMap(*cube_map_faces_textures)



        # Load the skybox texture
        skybox_texture = loader.loadCubeMap("shaders/clouds1_#.bmp")

        # Set up a camera for rendering the reflection texture
        #reflection_cam = base.makeCamera(base.win, sort=-1, lens=base.cam.node().getLens())
        #reflection_cam.node().set_scene(render)
        #reflection_cam.setHpr(0, 0, 20)
        #
        ## Render the scene to a texture
        #reflection_texture = self.render_to_texture(reflection_cam, "reflection_texture")
#
        ## Create and configure the reflection material
        #reflection_material = Material()
        #reflection_material.set_roughness(0.0)  # Set roughness to 0 for a reflective surface
#
        #
        ## Create a depth texture
        #depth_tex = Texture()
        #depth_tex.setup_2d_texture(width, height, Texture.T_unsigned_byte, Texture.F_depth_component)
#
        ## Create a depth buffer and attach the depth texture
        #depth_buffer = base.win.make_texture_buffer("Depth Buffer", width, height, depth_tex, True)
        #depth_cam = base.makeCamera(depth_buffer)
        #depth_cam.node().set_scene(render)
        #depth_cam.setHpr(0, -90, 0)
        

        ambient_light = AmbientLight("AmbientLight")
        ambient_light.setColor(Vec4(Vec3(100), 10))  # Set ambient light color
        ambient_light_np = base.render.attachNewNode(ambient_light)
        
        # Enable lighting in the scene
        base.render.setLight(ambient_light_np)
    
        slight_1 = Spotlight('slight_1')
        slight_1.set_color(Vec4(Vec3(1),1))
        slight_1.set_shadow_caster(True, 4096, 4096)
    
        lens = PerspectiveLens()
        slight_1.set_lens(lens)
        slight_1.get_lens().set_fov(120)
        slight_1_node = render.attach_new_node(slight_1)
        slight_1_node.set_pos(50, 50, 90)
        slight_1_node.look_at(0,0,0.5)
        render.set_light(slight_1_node)
        slight_2 = Spotlight('slight_2')
        slight_2.set_color(Vec4(Vec3(5),1))
        
        slight_2.set_attenuation((0.5,0,0.0005))
        lens = PerspectiveLens()
        slight_2.set_lens(lens)
        slight_2.get_lens().set_fov(100)
        slight_2_node = base.render.attach_new_node(slight_2)
        slight_2_node.set_pos(-82, -79, 50)
        slight_2_node.look_at(0,0,0.5)
        base.render.set_light(slight_2_node)
        env_light_1 = PointLight('env_light_1')
        env_light_1.set_color(Vec4(Vec3(6),1))#vec3(6),1
        env_light_1 = base.render.attach_new_node(env_light_1)
        env_light_1.set_pos(0,0,0)


        # Define the colors
    #    zenithColor = Vec4(0.5, 0.8, 1.0, 0)  # Light blue
    #    horizonColor = Vec4(0.2, 0.4, 0.6, 0)  # Dark blue
    #    #terrain = loader.load_model('DemoModels/terrain.bam')
    #    # Create the sky shader
    #    sky_shader = Shader.load(Shader.SL_GLSL, vertex="sky-vertex.glsl", fragment="sky-frag.glsl")
    #    
#
    #    
    #    #base_env.clear_texture()
    #    #terrain.setScale(500, 500, 500)
##
##
    #    ##base_env.set_shader(sky_shader)
##
    #    ## Set the shader inputs
    #    #base_env.set_shader_input("zenithColor", zenithColor)
    #    #base_env.set_shader_input("horizonColor", horizonColor)
#
#
    #    island = loader.loadModel("DemoModels/terrain.bam")
#
#
#
#
    #    # Load the skybox model
    #    
#
    #    # Reparent the skybox to the render node
    #    
    #    #terrain.reparent_to(base.render)
#
##
    #    
    #    ## Set the scale and position of the skybox
    #    
    #    #terrain.set_scale(1)
    #    
    #    #terrain.set_pos(0, 0, 0)
#
    #    # Set the light for the skybox
    #    #base_env.set_light(env_light_1)
#
    #    #env_light_1.set_light_off(base.render.find('**/slight_1'))
#
    #    # Apply the sky shader to the skybox model
    #    
#
#
    #    
    #    # Apply the reflection texture to your reflective surface
    #    self.reflective_surface = loader.loadModel("shaders/my-models/plane_with_multiple_verts.egg")
    #    self.skybox2 = loader.loadModel("models/daytime_skybox.bam")
    #    #self.reflective_surface.set_material(reflection_material)
    #    self.reflective_surface.set_tex_gen(TextureStage.getDefault(), TexGenAttrib.MEyeCubeMap)
    #    #self.reflective_surface.setTexture(reflection_texture)
    #    self.reflective_surface.set_scale(30, 30, 30)
    #    self.reflective_surface.set_pos(0, 0, 7)
    #    
#
    #    # Load shader
    #    my_shader = Shader.load(Shader.SL_GLSL, vertex="ocean-vert.vert", fragment="test-ocean.glsl")
#
    #    
#
    #    # Set shader inputs
    #    self.reflective_surface.set_shader(my_shader)
    #    
#
    #    base.taskMgr.add(self.update, "update")
    #    ft = globalClock.getFrameTime()
    #    self.reflective_surface.set_shader_input("iTime", ft)
#
    #    #reflection_vector_eye_space = self.calculate_reflection_vector()
#
    #    # Set the reflection vector as a shader input
    #    #self.reflective_surface.set_shader_input("reflectionVector", reflection_vector_eye_space)
    #    # Step 4: Apply Cubemap Texture to Reflective Object
    #    self.cubeimages = []
    #    #self.camera.reparentTo(base.render)  # Reparent the main camera to the rig
#
    #    # Load and set up the skybox
    #    #self.setup_skybox()
#
    #    ## Create a temporary folder to save individual camera views
    #    #self.temp_folder = "temp/"
    #    #os.makedirs(self.temp_folder, exist_ok=True)
##
    #    ## Create a NodePath representing the camera rig
    #    #rig = NodePath("rig")
    #    #rig.setPos(0, 0, 0)  # Set the position of the camera rig
    #    ##self.camera.reparentTo(rig)  # Reparent the main camera to the rig
##
    #    ## Create individual cameras for each face of the cube map
    #    #cube_map_faces = []
    #    #for i in range(6):
    #    #    cam = base.makeCamera(base.win, lens=base.cam.node().getLens())
    #    #    cam.reparentTo(rig)
    #    #    # Set the orientation of each camera to face a different direction
    #    #    if i == 0:  # Positive X
    #    #        cam.setHpr(90, 0, 0)
    #    #        filename = "pos0.png"
    #    #    elif i == 1:  # Negative X
    #    #        cam.setHpr(-90, 0, 0)
    #    #        filename = "pos1.png"
    #    #    elif i == 2:  # Positive Y
    #    #        cam.setHpr(0, 90, 0)
    #    #        filename = "pos2.png"
    #    #    elif i == 3:  # Negative Y
    #    #        cam.setHpr(0, -90, 0)
    #    #        filename = "pos3.png"
    #    #    elif i == 4:  # Positive Z (forward)
    #    #        cam.setHpr(0, 0, 0)
    #    #        filename = "pos4.png"
    #    #    elif i == 5:  # Negative Z (backward)
    #    #        cam.setHpr(180, 0, 0)
    #    #        filename = "pos5.png"
    #    #    self.save_camera_view(cam, filename)
    #    #    cube_map_faces.append(self.temp_folder + filename)
##
    #    #sampler = SamplerState()
    #    #sampler.setMinfilter(Texture.FT_linear)
    #    #sampler.setMagfilter(Texture.FT_linear)
#
    #    #Load the cube map texture with the specified sampler state
    #    # Load the cube map texture with linear filtering
    #    
    #    # Create a secondary camera for rendering reflections
    #    #reflection_cam = base.makeCamera(base.win, sort=-1, lens=base.cam.node().getLens())
##
    #    ## Create a texture to render reflections
    #    #self.reflection_texture = Texture("reflection_texture")
    #    #reflection_buffer = base.win.makeTextureBuffer("reflection_buffer", 512 * 2, 512 * 2, self.reflection_texture)
    #    #reflection_cam.node().setScene(render)
##
    #    ## Attach the reflection buffer to the secondary camera
    #    #reflection_cam.node().setCameraMask(BitMask32.bit(1))
    #    #reflection_cam.node().getLens().setNearFar(0.000001, 1000000)
    #    ##reflection_cam.setP(-90)
#
    #    #base.taskMgr.add(self.update, "update")
#
    #    
#
    #    # Pass the reflection texture to your water shader
    #    # Create a texture to render the scene
    #    self.scene_texture = Texture()
#
    #    # Create a buffer to render the scene into the texture
    #    #scene_buffer = base.win.makeTextureBuffer("sceneBuffer", 512 * 2, 512 * 2, self.scene_texture, True)
    #    #scene_buffer.addRenderTexture(self.scene_texture, GraphicsOutput.RTMCopyRam, GraphicsOutput.RTPDepthStencil)
    #    ## Create a camera to render the scene
    #    #scene_camera = base.makeCamera(scene_buffer)
    #    #scene_camera.reparentTo(render)
    #    #scene_camera.setPos(0, 0, 100)
    #    #scene_camera.setHpr(0, -90, 0)
    #    #
##
    #    ## Create a texture to store the depth information
    #    #self.scene_depth = Texture()
##
    #    ## Create a buffer to render the scene with depth information
    #    #self.depth_buffer = base.win.makeTextureBuffer("depthBuffer", 512 * 2, 512 * 2, self.scene_depth, to_ram=True)
##
    #    #self.depth_buffer.addRenderTexture(self.scene_depth, GraphicsOutput.RTMCopyRam, GraphicsOutput.RTPDepthStencil)
    #    ## Configure the depth buffer properties
    #    #depth_camera = base.makeCamera(self.depth_buffer, lens=OrthographicLens())
    #    #depth_camera.reparentTo(render)
    #    #depth_camera.setPos(0, 0, 100)
    #    #depth_camera.setHpr(0, -90, 0)
##
    #    ## Create a texture to store the normal information
    #    #self.scene_normal = Texture()
##
    #    ## Create a buffer to render the scene with normal information
    #    #self.normal_buffer = base.win.makeTextureBuffer("normalBuffer", 512 * 2, 512 * 2, self.scene_normal, to_ram=True)
    #    #self.normal_buffer.addRenderTexture(self.scene_normal, GraphicsOutput.RTMCopyRam, GraphicsOutput.RTPDepthStencil)
    #    ## Configure the normal buffer properties
    #    #normal_camera = base.makeCamera(self.normal_buffer)
    #    #normal_camera.reparentTo(render)
    #    #normal_camera.node().setScene(render)
    #    ## Apply a shader that encodes the normals into RGB colors
##
    #    #normal_camera.setPos(0, 0, 100)
    #    #normal_camera.setHpr(0, -90, 0)
#
#
    #    
#
    #    #fbprops = FrameBufferProperties()
    #    #fbprops.setRgbColor(1)
    #    #fbprops.setDepthBits(1)
    #    #fbprops.setAlphaBits(1)
    #    ## Set up a camera to render the scene into the buffer
    #    #self.buffer = base.graphicsEngine.makeOutput(
    #    #    base.win.getPipe(),
    #    #    "reflectionBuffer",
    #    #    -1,
    #    #    fbprops,
    #    #    WindowProperties.size(512, 512),
    #    #    GraphicsOutput.RTMBindOrCopy,
    #    #    base.win.getGsg(),
    #    #    None
    #    #)
    #    #self.buffer.setSort(-100)
    #    #self.reflectionTexture = Texture()
    #    #self.buffer.addRenderTexture(self.reflectionTexture, GraphicsOutput.RTMCopyRam, GraphicsOutput.RTPColor)
    #    #self.camera1 = base.makeCamera(self.buffer)
    #    #self.camera1.reparentTo(base.render)
    #    #self.camera1.node().setActive(1)
    #    #self.camera1.setPos(0, 0, 0) # Adjust camera position for reflection
#
#
#
    #    # Configure the camera properties (position, orientation, fov, etc.)
    #    # ...
#
#
    #    # Apply the cube map texture to the skybox
    #    #self.skybox.setTexGen(TextureStage.getDefault(), TextureStage.M_worldCube)
    #    #self.skybox.setTexture(cube_map_texture)
    #    #skybox = cubemap_texture
    #    # Assuming self.calculate_reflection_vector() returns the reflection vector in eye space
    #    
#
    #    self.reflective_surface.set_shader_input("skybox", cubemap_texture)
    #    self.reflective_surface.set_shader_input("iResolution", (base.win.getXSize(), base.win.getYSize()))
    #    self.reflective_surface.set_shader_input("iMouse", (base.win.getXSize() / 2, base.win.getYSize() / 2))
    #    #self.reflective_surface.set_shader_input('depthTexture', depth_tex)
#
    #    
    #    #self.reflective_surface.set_shader_input("reflectionTexture", depth_tex)
#
    #    # Add the render texture to the offscreen buffer
    #    albedo_texture = Texture()
#
    #    # Add the render texture to the offscreen buffer
    #    #offscreen_buffer = base.win.make_texture_buffer("OffscreenBuffer", 512, 512, albedo_texture)
    #    #offscreen_buffer.add_render_texture(albedo_texture, GraphicsOutput.RTMCopyRam, GraphicsOutput.RTPColor)
    #    #offscreen_buffer.set_clear_color_active(True)
    #    #offscreen_buffer.set_clear_color((0.5, 0.5, 0.5, 1))  # Set clear color to black
    #    #offscreen_camera = base.make_camera(offscreen_buffer)
    #    #offscreen_camera.reparent_to(NodePath())  # Reparent to a node in your scene graph
##
    #    ## Set the lens parameters of the offscreen camera to match the main camera
    #    #offscreen_camera.node().set_lens(base.cam.node().get_lens())
##
    #    ## Create a texture to render into
    #    #albedo_texture = Texture()
    #    #offscreen_buffer.add_render_texture(albedo_texture, GraphicsOutput.RTMCopyRam, GraphicsOutput.RTPColor)
##
    #    ## Create a camera to render the scene
    #    #offscreen_camera = base.make_camera(offscreen_buffer)
    #    #offscreen_camera.reparent_to(NodePath())  # Reparent to a node in your scene graph
    #    #offscreen_camera.node().set_lens(base.cam.node().get_lens())
#
#
    #    base.accept("aspectRatioChanged", self.win_resize)
#
    #    
#
    #    base.taskMgr.add(self.update_reflection, "update_reflection")
    #    projectionMatrix = base.cam.node().getLens().getProjectionMat()
    #    self.reflective_surface.set_shader_input("projectionMatrix", projectionMatrix)
    #    # Get the view matrix from the camera
    #    view_matrix = base.cam.getMat()
    #    
    #    # Set the view matrix as a shader input
    #    self.reflective_surface.setShaderInput("viewMatrix", view_matrix)
    #    base.taskMgr.add(self.generateReflectionTexture, "reflectionTexture")
#
#
#
#
    #    
#
    #    # Setup light source for shadow casting
    #    #light = Spotlight("shadow_light")
    #    #light.setColor(Vec4(1, 1, 1, 1))  # Set light color to white
    #    #lightNP = base.render.attachNewNode(light)
    #    #lightNP.setPos(0, 90, 50)  # Set light position
##
    #    ## Set up shadow caster
    #    #shadowBuffer = base.win.makeTextureBuffer("shadow_map", 1024, 1024)
    #    #shadowBuffer.setClearColor(Vec4(1))  # Clear color to white
    #    #shadowBuffer.setClearColorActive(True)
##
    #    #shadowLens = PerspectiveLens()
    #    #shadowLens.setFov(90)
    #    #light.setLens(shadowLens)
##
    #    #shadowCamera = base.makeCamera(shadowBuffer)
    #    #lightNP.node().setScene(base.render)  # Set scene for the light
    #    ## Enable shadows for the light
    #    #lightNP.node().setShadowCaster(True, 1024, 1024)
##
    #    ## Set up shader inputs for shadows
    #    #self.reflective_surface.setShaderInput("shadow_map", shadowBuffer.getTexture())
    #    
    #    self.reflective_surface.setP(-90)
    #    self.reflective_surface.reparentTo(base.render)
    #    self.skybox2.reparentTo(base.render)
#
    #    self.createReflectionBuffer()
    #    base.addTask(self.UpdateReflectionBuffer, 'updateBuffer')
    #    
        base.run()
#
    #    
#
    #    
    #    
#
    ##def calculate_reflection_vector(self):
    ##    # Define the surface normal and incident vector
    ##    surface_normal = Vec3(0, 0, 1)  # Example: upward-facing surface
    ##    #incident_vector = Vec3(0, 0, 1)  # Example: straight down from the camera
##
    ##    incident_vector = Vec3(0, 0, -1)  # Example: straight down from the camera
##
    ##    # Calculate the reflection vector in world space
    ##    reflection_vector = incident_vector - 2 * surface_normal * (incident_vector.dot(surface_normal))
##
    ##    # Get the model-view matrix (transformation matrix from world space to eye space)
    ##    modelview_matrix = base.camera.getMat()
##
    ##    # Invert the model-view matrix to get the eye-to-world transformation matrix
    ##    eye_to_world_matrix = LMatrix4.invertFrom(LMatrix4(), modelview_matrix)
##
    ##    # Transform the reflection vector from world space to eye space
    ##    reflection_vector_eye_space = reflection_vector * eye_to_world_matrix
##
    ##    return reflection_vector_eye_space
    #    
#
    #def createReflectionBuffer(self):
    #    # Create a buffer to render the reflected scene into
    #    
    #    
#
    #    base.cam.node().getLens().setNearFar(0.00001, 500.0)
    #    # First pass we render needed texture
    #    # Set up render targets
    #    self.albedo_tex = Texture()
    #    self.depth_tex = Texture()
    #    self.normal_tex = Texture()
    #    
    #    albedo_rt = base.win.makeTextureBuffer("AlbedoRT", 512, 512, self.albedo_tex)
    #    depth_rt = base.win.makeTextureBuffer("DepthRT", 512, 512, self.depth_tex)
    #    normal_rt = base.win.makeTextureBuffer("NormalRT", 512, 512, self.normal_tex)
    #    
    #    # Configure filters
    #    self.filter_mgr = FilterManager(base.win, base.cam)
    #    self.albedo_rt = self.create_render_texture("AlbedoRT", self.albedo_tex)
    #    self.depth_rt = self.create_render_texture("DepthRT", self.depth_tex)
    #    self.normal_rt = self.create_render_texture("NormalRT", self.normal_tex)
    #    
    #    # Render the scene to each render target
    #    self.render_scene(self.albedo_rt)
    #    self.render_scene(self.depth_rt)
    #    self.render_scene(self.normal_rt)
    #    
    #def UpdateReflectionBuffer(self, task):
    #    # Create a buffer to render the reflected scene into
    #    
    #    
#
    #    base.cam.node().getLens().setNearFar(0.00001, 500.0)
    #    # First pass we render needed texture
    #    # Set up render targets
    #    self.albedo_tex = Texture()
    #    self.depth_tex = Texture()
    #    self.normal_tex = Texture()
    #    
    #    albedo_rt = base.win.makeTextureBuffer("AlbedoRT", 512, 512, self.albedo_tex)
    #    depth_rt = base.win.makeTextureBuffer("DepthRT", 512, 512, self.depth_tex)
    #    normal_rt = base.win.makeTextureBuffer("NormalRT", 512, 512, self.normal_tex)
    #    
    #    # Configure filters
    #    self.albedo_rt = self.create_render_texture("AlbedoRT", self.albedo_tex)
    #    self.depth_rt = self.create_render_texture("DepthRT", self.depth_tex)
    #    self.normal_rt = self.create_render_texture("NormalRT", self.normal_tex)
    #    
    #    # Render the scene to each render target
    #    self.render_scene(self.albedo_rt)
    #    self.render_scene(self.depth_rt)
    #    self.render_scene(self.normal_rt)
    #    # Now you can use albedo_tex, depth_tex, and normal_tex as needed
    #    task.cont
    #    
    #def make_camera_buffer(self, render_target):
    #    self.albedo_tex = Texture()
    #    self.depth_tex = Texture()
    #    self.normal_tex = Texture()
    #    dr = render_target.make_display_region()
    #    dr.set_clear_color_active(True)
    #    dr.set_clear_color((0, 0, 0, 1))
    #    dr.set_camera(self.camera)                                                
    #    # Pass camera and other inputs to the shader
    #    self.reflective_surface.setShaderInput("cameraPos2", base.cam.getPos())
    #    transformation_matrix = base.cam.getMat(base.render)
    #    self.reflective_surface.setShaderInput("trans_clip_of_mcamera_to_view_of_mcamera", transformation_matrix)#NodePath(base.cam))
    #    camera_np = NodePath(base.cam)
#
    #    # Set the shader input using the NodePath object
    #    self.reflective_surface.setShaderInput("mcamera", camera_np)
    #    # Apply filters (example: SSAO for depth)
    #    self.filter_mgr.set_shader_input("albedo", albedo_tex)
    #    self.filter_mgr.set_shader_input("depth", depth_tex)
    #    self.filter_mgr.set_shader_input("normal", normal_tex)
    #    
    #    # Render the scene
    #    self.render_scene()
    #    
    #    # Retrieve textures
    #    albedo_tex = albedo_rt.get_texture()
    #    depth_tex = depth_rt.get_texture()
    #    normal_tex = normal_rt.get_texture()
#
    #    # Render the scene to obtain depth information
    #    base.graphicsEngine.renderFrame()
#
    #    self.reflectionTexture = self.albedo
#
#
    #    
    #    #self.reflective_surface.setShaderInput("mcamera", self.offscreen_camera)
    #    # Update uniforms
    #    self.reflective_surface.setShaderInput("texpad_albedo", self.albedo)
    #    self.reflective_surface.setShaderInput("reflectionVector", self.calculate_reflection_vector())
    #    self.reflective_surface.setShaderInput("reflectionTexture", self.reflectionTexture)
    #    self.reflective_surface.setShaderInput("sceneTexture", self.albedo)
    #    self.reflective_surface.setShaderInput("depthTexture", self.depth)  # Pass depth texture
    #    
    #    self.reflective_surface.setShaderInput("normalTexture", self.normal)
    #    self.albedo_rt = self.create_render_texture("AlbedoRT", self.albedo_tex)
    #    self.depth_rt = self.create_render_texture("DepthRT", self.depth_tex)
    #    self.normal_rt = self.create_render_texture("NormalRT", self.normal_tex)
    #    
    #    # Render the scene to each render target
    #    self.render_scene(self.albedo_rt)
    #    self.render_scene(self.depth_rt)
    #    self.render_scene(self.normal_rt)
#
#
    #    
    #    
    #    # Now you can use albedo_tex, depth_tex, and normal_tex as needed
    #    
    #def create_render_texture(self, name, texture):
    #    buffer = base.win.make_texture_buffer(name, 512, 512, texture)
    #    buffer.set_sort(-1)
    #    return buffer
    #    
    #def render_scene(self, render_target):
    #    # Render the scene to the specified render target
    #    base.cam.node().get_display_region(0).set_active(False)
    #    self.make_camera_buffer(render_target)
    #    base.graphicsEngine.render_frame()
    #    
    #def make_camera_buffer(self, render_target):
    #    base.cam.node().getLens().setNearFar(0.00001, 500.0)
    #    dr = render_target.make_display_region()
    #    dr.set_clear_color_active(True)
    #    dr.set_clear_color((0, 0, 0, 1))
    #    dr.set_camera(base.cam)
#
    #def generateReflectionTexture(self, task):
#
#
    #    
    #    ## Regenerate the reflection texture each frame
    #    #self.buffer.clearRenderTextures()
    #    ##self.createReflectionBuffer()  # Recreate the buffer and camera
##
    #    ## Get the position and direction that the main camera is looking at
    #    #camera_pos = base.camera.getPos(render)
    #    #look_at_pos = base.camera.getPos(render) + base.camera.getQuat(render).getForward()
    ##
    #    ## Set the position of the reflection camera to be above the water surface and look at the same point
    #    #reflection_height = self.reflective_surface.getZ()  # Adjust this based on your water surface height
    #    #self.camera1.setPos(camera_pos.getX(), camera_pos.getY(), camera_pos.getZ() - reflection_height)
    #    #self.camera1.lookAt(look_at_pos)
##
    #    #self.reflectionTexture = Texture()
    #    #self.buffer.addRenderTexture(self.reflectionTexture, GraphicsOutput.RTMCopyRam, GraphicsOutput.RTPColor)
#
#
#
    #    # Render the scene to generate the reflection texture
    #    base.graphicsEngine.renderFrame()
#
    #    return task.cont
    #def update_reflection(self, task):
#
    #    #base.cam.node().getLens().setNearFar(1.0, 500.0)
    #    ## First pass we render needed texture
    #    #self.albedo = Texture()
    #    #self.depth = Texture()
    #    #self.normal = Texture()
    #    #final_quad = self.manager.renderSceneInto(colortex = self.albedo, 
    #    #                                         depthtex = self.depth, 
    #    #                                         auxtex = self.normal,
    #    #                                         auxbits = AuxBitplaneAttrib.ABOAuxNormal)
##
    #    ## Pass camera and other inputs to the shader
    #    #transformation_matrix = base.cam.getMat(base.render)
    #    #self.reflective_surface.setShaderInput("trans_clip_of_mcamera_to_view_of_mcamera", transformation_matrix)#NodePath(base.cam))
    #    #camera_np = NodePath(base.cam)
##
    #    ## Set the shader input using the NodePath object
    #    #self.reflective_surface.setShaderInput("mcamera", camera_np)
    #    #self.reflective_surface.setShaderInput("albedo", self.albedo)  # Pass depth texture
    #    #self.reflective_surface.setShaderInput("depth", self.depth)  # Pass depth texture
    #    #self.reflective_surface.setShaderInput("normal", self.normal)  # Pass depth texture
##
    #    ## Render the scene to obtain depth information
    #    #base.graphicsEngine.renderFrame()
##
    #    #self.reflectionTexture = self.albedo
##
    #    ## Update uniforms
    #    #
    #    ##self.reflective_surface.setShaderInput("mcamera", self.offscreen_camera)
    #    #self.reflective_surface.setShaderInput("texpad_albedo", self.albedo)
    #    #self.reflective_surface.setShaderInput("reflectionVector", self.calculate_reflection_vector())
    #    #self.reflective_surface.setShaderInput("reflectionTexture", self.reflectionTexture)
    #    #self.reflective_surface.setShaderInput("sceneTexture", self.albedo)
    #    #self.reflective_surface.setShaderInput("depthTexture", self.depth)  # Pass depth texture
    #    #
    #    #self.reflective_surface.setShaderInput("normalTexture", self.normal)
    #    self.reflective_surface.setShaderInput("cameraPos2", base.cam.getPos())
#
    #    return task.cont


        
    
    def save_camera_view(self, camera, filename):
        
        # Render the scene to a texture
        tex = Texture()
        tex.setup2dTexture(1280, 720, Texture.T_unsigned_byte, Texture.F_rgba8)
        buffer = base.win.makeTextureBuffer("offscreen buffer", 1280, 720, tex)
        buffer.setClearColorActive(True)
        buffer.setClearColor((0, 0, 0, 1))
        cam = base.makeCamera(
            buffer, lens=camera.node().getLens())
        base.graphicsEngine.renderFrame()

        # Ensure the texture is fully generated
        tex.makeRamImage()

        # Save the texture to an image file
        tex.write(Filename(self.temp_folder + filename))
    
        
    def render_to_texture(self, camera, texture_name):
        buffer = base.win.make_texture_buffer(texture_name, 512, 512)
        buffer.set_clear_color_active(True)
        buffer.set_clear_color((0, 0, 0, 0))  # Clear color to transparent

        scene_camera = base.makeCamera(base.win, sort=-1, lens=base.cam.node().getLens())
        scene_camera.set_pos(0, -10, 0)  # Set camera position

        scene_camera.node().set_active(True)
        base.graphics_engine.render_frame()
        scene_camera.node().set_active(False)

        texture = buffer.get_texture()

        return texture

    def update(self, task):
        ft = globalClock.getFrameTime()
        self.reflective_surface.set_shader_input("iTime", ft)
        ft = globalClock.getFrameTime()
        self.reflective_surface.set_shader_input("time", ft * 10)
        return task.cont

    def win_resize(self):
        self.reflective_surface.set_shader_input("iResolution", (base.win.getXSize(), base.win.getYSize()))
        self.reflective_surface.set_shader_input("iMouse", (base.win.getXSize() / 2, base.win.getYSize() / 2))

    def loadSmiley(self):
        #my_card = CardMaker('card')
        #my_card.set_frame((-1, 0, 0), (1, 0, 0), (0.5, 0, 1), (-0.25, 0, 1))
        #my_card.set_uv_range((0, 0), (1, 1))
        #my_card = aspect2d.attach_new_node(my_card.generate())
        #my_card.set_scale(0.5)
        #my_card.set_pos(-0.5, 0, 0)
        ##my_card.setScale(100)
        #
        #myTexture = loader.loadTexture("textures\hdri/get_file_SkyOnlyHDRI042_16K-TONEMAPPED.jpg")
#
        #my_card.setTexture(myTexture)
#
        #my_card.setP(-90)
#
        #my_card.reparentTo(base.render)

        #s = loader.loadModel("plane.obj")
        #s.reparentTo(render)
        #self.loaded_models["plane.obj(0000)"] = s
        base.camLens.set_fov(90)
        base.camLens.set_near_far(0.1, 5000)

        loader.loadModel('DemoModels/smithai/smith.bam').ls()

        s = Actor("DemoModels/smithai/smith.bam")
        s.reparentTo(render)
        self.loaded_models["smith.bam(0000)"] = s
        #s.setPlayRate(10.0, 'run')
        s.play('run2')
        s.loop('run2')


        g = loader.loadModel("models/camera2.egg")
        shadowCameraDrawMask = BitMask32.bit(2)
        g.hide(shadowCameraDrawMask)
        g.reparentTo(render)
        self.loaded_models["camera2.bam(0001)"] = g

        
        # Create a new camera
        #new_camera = base.makeCamera(base.win)
#
        ## You can also specify a name for the new camera
        ## new_camera = base.makeCamera(name="MyCamera")
#
        ## Set the position, orientation, and other properties of the new camera
        ## For example:
        g.setPos(0, 0, 0)
        g.setHpr(0, 90, 0)
        #new_camera.lookAt(0, 0, 0)

        # Optionally, you can set the active camera to the new camera
        # This will make the new camera the active camera for rendering
        #base.cam = new_camera
        self.create_camera_fov_cone(g, fov_angle=60, num_segments=16, length=10)




        #my_hdri = loader.loadCubeMap("c:/Users/user/Desktop/SimpleThirdPersonCamera-main/hdri/hdri.hdr")
        #my_hdri.reparentTo(render)

        self.pipe.send(["Load", self.loaded_models, "DemoModels/MyTradis.bam(0000)", "MyTradis.bam(0000)"])
        self.pipe.send(["Load", self.loaded_models, "models/camera2.egg(0001)", "camera2.egg(0001)"])
        s.setY(20)
    def create_camera_fov_cone(self, camera, fov_angle, num_segments=16, length=10):
        # Create a GeomNode to hold the cone geometry
        cone_node = GeomNode("camera_fov_cone")
        format = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData("camera_fov_cone_data", format, Geom.UHStatic)
        vertex_writer = GeomVertexWriter(vdata, "vertex")
        normal_writer = GeomVertexWriter(vdata, "normal")
        color_writer = GeomVertexWriter(vdata, "color")
        tris = GeomTriangles(Geom.UHStatic)

        # Calculate the vertices for the cone
        center = Point3(0, 0, 0)
        apex = Vec3(0, 0, length)
        vertices = [apex]
        for i in range(num_segments):
            angle = fov_angle * (i / (num_segments - 1) - 0.5)
            x = length * angle
            vertex = Point3(x, 0, length)
            vertices.append(vertex)

        # Add vertices, colors, and normals to the vertex data
        for vertex in vertices:
            vertex_writer.addData3f(vertex)
            normal_writer.addData3f(vertex - center)
            color_writer.addData4f(1, 1, 1, 0.5)  # White with 50% opacity

        # Create triangles to form the cone faces
        for i in range(1, num_segments):
            tris.addVertices(0, i, i + 1)
        tris.addVertices(0, num_segments, 1)

        # Create a Geom object and add the triangles to it
        geom = Geom(vdata)
        geom.addPrimitive(tris)

        # Attach the Geom to the GeomNode
        cone_node.addGeom(geom)

        # Attach the GeomNode to the camera
        camera_node = camera.node()
        camera_node.addChild(cone_node)

# Usage example:

    def getFocus(self):
        """Bring Panda3d to foreground, so that it gets keyboard focus.
        Also send a message to wx, so that it doesn't render a widget focused.
        We also need to say wx that Panda now has focus, so that it can notice when
        to take focus back.
        """
        wp = WindowProperties()
        # This causes warnings on Windows
        #wp.setForeground(True)
        base.win.requestProperties(wp)
        self.pipe.send("focus")

    def resizeWindow(self, width, height):
        old_wp = base.win.getProperties()
        if old_wp.getXSize() == width and old_wp.getYSize() == height:
            return
        wp = WindowProperties()
        wp.setOrigin(0, 0)
        wp.setSize(width, height)
        base.win.requestProperties(wp)



    def handle_key_event(self, key):
        
        if key == "w":
            
            # Update flag based on key press/release
            self.w_pressed = True
        if key == "a":
            
            # Update flag based on key press/release
            self.a_pressed = True
        if key == "s":
            
            # Update flag based on key press/release
            self.s_pressed = True
        if key == "d":
            
            # Update flag based on key press/release
            self.d_pressed = True


        if key == "w-up":
            
            # Update flag based on key press/release
            self.w_pressed = False
        if key == "a-up":
            
            # Update flag based on key press/release
            self.a_pressed = False
        if key == "s-up":
            
            # Update flag based on key press/release
            self.s_pressed = False
        if key == "d-up":
            
            # Update flag based on key press/release
            self.d_pressed = False

    # Update function called every frame
    def update_camera(self, task):
        self.dt = globalClock.getDt()
        forward = base.camera.getQuat().getForward()
        right = base.camera.getQuat().getRight()
        # Move camera up if "w" is pressed
        if self.w_pressed:
            self.velocity += forward*self.acceleration*self.dt
        if self.a_pressed:
            self.velocity += -right*self.acceleration*self.dt
        if self.s_pressed:
            self.velocity += -forward*self.acceleration*self.dt
        if self.d_pressed:
            self.velocity += right*self.acceleration*self.dt
        speed = self.velocity.length()
        if speed > self.maxSpeed:
            speed = self.maxSpeed
            self.velocity.normalize()
            self.velocity *= speed
        # Update the player's position
        # Apply friction when the player stops moving
        if not self.walking:
            frictionVal = self.friction*self.dt
            if frictionVal > speed:
                self.velocity.set(0, 0, 0)
            else:
                self.frictionVec = -self.velocity
                self.frictionVec.normalize()
                self.frictionVec *= frictionVal
                self.velocity += self.frictionVec
        # Adjust camera position based on the direction vector
        base.camera.setPos(base.camera.getPos() + self.velocity*self.dt)
        return Task.cont  # Continue the task

    def get_filename(self, filepath):
        # Choose one of the methods for extracting the filename
        return os.path.basename(filepath)  # String manipulation method
        # OR
        #filename = wx.FileName(filepath)
        return filename.GetFullName()  # wx.FileName method

    def moveCamera(self, direction, state):
        self.keyMap[direction] = state

        #orientationQuat = self.manipulator.getQuat(sceneRoot)
        
        
        forward = base.camera.getQuat().getForward()
        right = base.camera.getQuat().getRight()

        
        
        if self.keyMap["up"]:
            self.velocity += forward*self.acceleration*self.dt
            self.walking = True
            print('w')
        if self.keyMap["down"]:
            self.velocity -= forward*self.acceleration*self.dt
            self.walking = True
        if self.keyMap["right"]:
            self.velocity += right*self.acceleration*self.dt
            self.walking = True
        if self.keyMap["left"]:
            self.velocity -= right*self.acceleration*self.dt
            self.walking = True
        


        # Prevent the player from moving too fast
        speed = self.velocity.length()

        if speed > self.maxSpeed:
            speed = self.maxSpeed
            self.velocity.normalize()
            self.velocity *= speed

        # Update the player's position
        

        # Apply friction when the player stops moving
        if not self.walking:
            frictionVal = self.friction*self.dt
            if frictionVal > speed:
                self.velocity.set(0, 0, 0)
            else:
                self.frictionVec = -self.velocity
                self.frictionVec.normalize()
                self.frictionVec *= frictionVal
                self.velocity += self.frictionVec
                
        # Adjust camera position based on the direction vector
        base.camera.setPos(base.camera.getPos() + self.velocity*self.dt)
        #base.camera.setPos(base.camera.getPos() + self.velocity)
        
    def handleRightClick(self):
        # Get mouse movement since last frame
        winProperties = base.win.getProperties()
        windowWidth = winProperties.get_x_size()
        windowHeight = winProperties.get_y_size()
        centerX = windowWidth / 2
        centerY = windowHeight / 2
        base.win.movePointer(0, int(centerX), int(centerY))
        self.mouse_down = not self.mouse_down
        
        #base.camera.setRpy(0, my, 0)
    def handleMidClick(self):
        self.mouse_down2 = not self.mouse_down2

    def remove_last_six_digits(self, filename):
        """Removes the last 6 digits from a filename, preserving the extension.

        Args:
            filename: The filename to modify.

        Returns:
            The modified filename with the last 6 digits removed.
        """
        #base, ext = os.path.splitext(filename)
        # Ensure filename length is at least 7 to avoid index errors
        if len(filename) >= 7:
          return filename[:-6]
        else:
          # Handle cases where filename is less than 7 characters
          return filename
    def handle_mouse_click(self):
        # Get the mouse position in world coordinates
        #mouse_pos = base.win.getAspectRatio() * (base.mouseWatcherNode.getMouseX(), base.mouseWatcherNode.getMouseY())
        
        mouse_pos = (base.mouseWatcherNode.getMouseX(), base.mouseWatcherNode.getMouseY())

        mouse_pos = base.mouseWatcherNode.getMouse()

        self.oldmpos = mouse_pos
        


        print("clicked at: ", mouse_pos)

        # Check if an object is currently selected
        if self.selected != None:
            base.taskMgr.add(self.perform_arrow_picking, "perform_arrow_picking")
            #self.perform_arrow_picking(self.Arrows[str(self.selected)]["x"], "x")
    def perform_arrow_picking(self, task):
        # Create a ray starting from the camera and pointing towards the mouse position
        
        mpos = base.mouseWatcherNode.getMouse()
        self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())
        self.myTraverser.traverse(render)
        # Assume for simplicity's sake that myHandler is a CollisionHandlerQueue.
        #if self.myHandler.getNumEntries() > 0:
        #    # This is so we get the closest object.
        #    self.myHandler.sortEntries()
        #    self.pickedObj = self.myHandler.getEntry(0).getIntoNodePath()
        #    self.pickedObj = self.pickedObj.findNetTag('myObjectTagX')
        #    self.pickedObjy = self.pickedObj.findNetTag('myObjectTagY')
        #    self.pickedObjz = self.pickedObj.findNetTag('myObjectTagZ')
        #    self.selectedObj = render.find(str(self.selected))
        #    if not self.pickedObj.isEmpty():
        #        #print("its not empty")
        #        
        #        print(self.selectedObj)
        #        print(self.pickedObj)
        #        base.taskMgr.add(self.X_drag, "x_drag")
        #        self.dragged_object = self.pickedObj
        #        self.selected_dragged_objectx = self.selectedObj 
        #        self.pickedObjyold = self.pickedObjy
        #        self.pickedObjzold = self.pickedObjz
        #        
        #    if not self.pickedObjy.isEmpty():    
        #        self.selectedObj.setPos(self.selectedObj.getX(), self.selectedObj.getX() + mpos.getX() * 5, self.selectedObj.getZ())
        #    if not self.pickedObjz.isEmpty():    
        #        self.selectedObj.setPos(self.selectedObj.getX(), self.selectedObj.getY(), self.selectedObj.getZ() + mpos.getY() * 5)
        
        
        if self.myHandler.getNumEntries() > 0:
        # Filter for arrow objects and ignore collisions with them
            for i in range(self.myHandler.getNumEntries() - 1, -1, -1):
                entry = self.myHandler.getEntry(i)
                self.intoNP = entry.getIntoNodePath()
                self.selectedObj = render.find(str(self.selected))
                if self.intoNP.hasNetTag('myObjectTagX') and self.y == False and self.z == False:
                    self.x = True
                    base.taskMgr.add(self.X_drag, "x_drag")
                    self.dragged_object = self.intoNP
                    self.selected_dragged_objectx = self.selectedObj
                    #self.myHandler.removeEntry(entry)  
                if self.intoNP.hasNetTag('myObjectTagY') and self.x == False and self.z == False:
                    self.y = True
                    base.taskMgr.add(self.Y_drag, "y_drag")
                    self.dragged_object = self.intoNP
                    self.selected_dragged_objectx = self.selectedObj 
                if self.intoNP.hasNetTag('myObjectTagZ') and self.x == False and self.y == False:
                    self.z = True
                    base.taskMgr.add(self.Z_drag, "z_drag")
                    self.dragged_object = self.intoNP
                    self.selected_dragged_objectx = self.selectedObj      
                
            return Task.cont
    def X_drag(self, task):
        # Get current and previous mouse positions
        mpos = base.mouseWatcherNode.getMouse()

        #move the mouse to the center of the screen
        winProperties = base.win.getProperties()
        windowWidth = winProperties.get_x_size()
        windowHeight = winProperties.get_y_size()
        centerX = windowWidth / 2
        centerY = windowHeight / 2 +0.3
        base.win.movePointer(0, int(centerX), int(centerY))

        delta_x = self.oldmpos.getX() - mpos.getX() * 3  # Calculate X-axis difference


        # Update selected object's X position based on delta_x
        self.selected_dragged_objectx.setPos(
            self.selected_dragged_objectx.getX() - delta_x,
            self.selected_dragged_objectx.getY(),
            self.selected_dragged_objectx.getZ()
        )

        # Update the positions of the arrow models to follow the dragged object
        self.arrowx.setPos(self.selected_dragged_objectx.getPos())
        self.arrowy.setPos(self.selected_dragged_objectx.getPos())
        self.arrowz.setPos(self.selected_dragged_objectx.getPos())

        # Update the old mouse position for the next drag
        self.oldmpos = mpos

        return Task.cont
    def Y_drag(self, task):
        # Get current and previous mouse positions
        mpos = base.mouseWatcherNode.getMouse()

        #move the mouse to the center of the screen
        winProperties = base.win.getProperties()
        windowWidth = winProperties.get_x_size()
        windowHeight = winProperties.get_y_size()
        centerX = windowWidth / 2
        centerY = windowHeight / 2 +0.3
        base.win.movePointer(0, int(centerX), int(centerY))

        delta_y = self.oldmpos.getX() - mpos.getX() * 3  # Calculate X-axis difference


        # Update selected object's X position based on delta_x
        self.selected_dragged_objectx.setPos(
            self.selected_dragged_objectx.getX(),
            self.selected_dragged_objectx.getY() + delta_y,
            self.selected_dragged_objectx.getZ()
        )

        # Update the positions of the arrow models to follow the dragged object
        self.arrowx.setPos(self.selected_dragged_objectx.getPos())
        self.arrowy.setPos(self.selected_dragged_objectx.getPos())
        self.arrowz.setPos(self.selected_dragged_objectx.getPos())

        # Update the old mouse position for the next drag
        self.oldmpos = mpos

        return Task.cont
    def Z_drag(self, task):
        # Get current and previous mouse positions
        mpos = base.mouseWatcherNode.getMouse()

        #move the mouse to the center of the screen
        winProperties = base.win.getProperties()
        windowWidth = winProperties.get_x_size()
        windowHeight = winProperties.get_y_size()
        centerX = windowWidth / 2
        centerY = windowHeight / 2 +0.3
        base.win.movePointer(0, int(centerX), int(centerY))

        delta_z = self.oldmpos.getY() - mpos.getY() * 3  # Calculate X-axis difference


        # Update selected object's X position based on delta_x
        self.selected_dragged_objectx.setPos(
            self.selected_dragged_objectx.getX(),
            self.selected_dragged_objectx.getY(),
            self.selected_dragged_objectx.getZ() - delta_z
        )

        # Update the positions of the arrow models to follow the dragged object
        self.arrowx.setPos(self.selected_dragged_objectx.getPos())
        self.arrowy.setPos(self.selected_dragged_objectx.getPos())
        self.arrowz.setPos(self.selected_dragged_objectx.getPos())

        # Update the old mouse position for the next drag
        self.oldmpos = mpos

        return Task.cont
        
    def endTask(self):
        self.x = False
        self.y = False
        self.z = False
        base.taskMgr.remove('x_drag')
        base.taskMgr.remove('y_drag')
        base.taskMgr.remove('z_drag')
        base.taskMgr.remove('perform_arrow_picking')
        ##############old code vvvvvv###############
        #near_pos = cam.getMat().xform(Vec3(mouse_pos[0], mouse_pos[1], 0))
        #far_pos = cam.getMat().xform(Vec3(mouse_pos[0], mouse_pos[1], 1))
        #origin_x, origin_y, origin_z = near_pos.getX(), near_pos.getY(), near_pos.getZ()
        #far_x, far_y, far_z = far_pos.getX(), far_pos.getY(), far_pos.getZ()
        
        #pick_ray = CollisionRay(LPoint3f(origin_x, origin_y, origin_z),
        #               LPoint3f(far_x, far_y, far_z) - LPoint3f(origin_x, origin_y, origin_z))

        # Perform ray casting against the arrow's collider (if it has one)
        #traverser = CollisionTraverser()
        #picker = CollisionHandlerQueue()
        #collider_node = arrow_node.getChild(0).find("**/+CollisionNode")
        #if collider_node.isEmpty():
        #    print("Warning: CollisionNode not found in child node!")
        #    # Handle the situation appropriately (e.g., return, create a default collider)
        #else:
        #    collider = collider_node.node()
        #    traverser.addCollider(collider, arrow_node)
        
        #picker.addCollider(arrow_node.getChild(0).getCollider(0))  # Assuming first child has collider
        

        
        # Create the ray line geometry
        #format = GeomVertexFormat.getV3()  # Vertex format with 3 floats for position
        #vdata = GeomVertexData("ray_lines", format, Geom.UH_static)
        #vertex = GeomVertexWriter(vdata, "vertex")
#
        ## Add start and end points of the ray
        #vertex.addData3f(origin_ndc)
        #vertex.addData3f(far_ndc)
#
        #lines = GeomLines(Geom.UH_static)
        #lines.addNextVertices(2)  # Two vertices for the line
#
        #geom = Geom(vdata)
        #geom.addPrimitive(lines)
#
        #node = GeomNode("ray_lines_node")
        #node.addGeom(geom)
        #nodePath = render.attachNewNode(node)
#
        ## Set color and thickness
        #nodePath.setColor(1, 1, 1, 1)  # Red color
        #nodePath.setRenderModeThickness(4)



        # Check if there was a collision with the arrow
        #if picker.getNumEntries() > 0:
        #    # There was at least one collision
        #    # You can access the first colliding object's name (optional):
        #    first_collision = picker.entries[0].getSourceNode().getName()
        #    print(f"Collision detected with: {first_collision}")
        #    base.graphicsEngine.processPick(pick_ray, picker)
        #    return picker.getNumEntries()
        #else:
        #    print("no collision")
    #def on_arrow_drag(self, dragged_arrow_node):
    #    def handle_mouse_move(event):
    #        # Get the current mouse position in world coordinates
    #        mouse_pos = base.graphicsEngine.getScreenAspect() * event.get_pos()
#
    #        # Calculate the delta (difference) in mouse movement since dragging started
    #        delta_pos = mouse_pos - self.initial_mouse_pos
#
    #        # Retrieve the object node associated with the dragged arrow
    #        object_node = self.arrows[self.selected][0]
#
    #        # Determine the axis to move based on the clicked arrow
    #        axis = "x" if dragged_arrow_node == self.arrows[self.selected]["x"] else "y" if dragged_arrow_node == self.arrows[self.selected_object_name]["y"] else "z"
#
    #        # Update the object's position based on the delta and axis
    #        current_pos = object_node.getPos()
    #        new_pos = Vec3(current_pos)
    #        if axis == "x":
    #            new_pos.x += delta_pos.x
    #        elif axis == "y":
    #            new_pos.y += delta_pos.y
    #        else:  # z-axis
    #            new_pos.z += delta_pos.z
    #        object_node.setPos(new_pos)
#
    #        # Reposition the dragged arrow to stay aligned with the object
    #        dragged_arrow_node.setPos(new_pos)
#
    #    # Store the initial mouse position when dragging starts
    #    self.initial_mouse_pos = base.graphicsEngine.getScreenAspect() * (base.mouseWatcherNode.getMouseX(), base.mouseWatcherNode.getMouseY())
#
    #    # Bind the mouse move event to handle dragging until mouse release
    #    base.accept("mouse-move", handle_mouse_move)
#
    #    # Unbind the mouse move event when the mouse button is released
    #    base.accept("mouse1-up", base.ignore("mouse-move"))  # Replace "mouse1-up" with the appropriate release event
    def create_camera_visualization(self, camera):
        # Create a NodePath to hold the visualization
        visualization = NodePath("camera_visualization")

        # Create a LineSegs object to draw lines
        lines = LineSegs()
        lines.setThickness(2)

        # Get the camera's position and view direction
        cam_pos = camera.getPos()
        cam_dir = camera.getNetTransform().getMat().getRow3(1)  # Get the forward direction

        # Define the length of the lines for visualization
        line_length = 10.0

        # Draw a line representing the camera's position and direction
        lines.setColor(Vec4(1, 0, 0, 1))  # Red color
        lines.moveTo(cam_pos)
        lines.drawTo(cam_pos + cam_dir * line_length)

        # Attach the lines to the visualization NodePath
        visualization.attachNewNode(lines.create())

        # Return the visualization NodePath
        return visualization
    def checkPipe(self, task):
        """This task is responsible for executing actions requested by wxWidgets.
        Currently supported requests with params:
        resize, width, height
        close
        """
        # TODO: only use the last request of a type
        #       e.g. from multiple resize requests take only the latest into account
        #self.sphere = loader.loadModel("DemoModels/environment.egg")
        #self.sphere.reparentTo(render)

        if base.mouseWatcherNode.hasMouse() and self.mouse_down:
            winProperties = base.win.getProperties()
            windowWidth = winProperties.get_x_size()
            windowHeight = winProperties.get_y_size()
            centerX = windowWidth / 2
            centerY = windowHeight / 2
            base.win.movePointer(0, int(centerX), int(centerY))
            mx = base.mouseWatcherNode.getMouseX() * 100
            my = base.mouseWatcherNode.getMouseY() * 100
            self.camRX += mx
            self.camRY += my
            base.camera.setHpr(-self.camRX, self.camRY, 0)
            
        #pan view
        if base.mouseWatcherNode.hasMouse() and self.mouse_down2:
            f = base.camera.getQuat().getUp()
            r = base.camera.getQuat().getRight()
            mx = base.mouseWatcherNode.getMouseX() * 2
            my = base.mouseWatcherNode.getMouseY() * 2
            r *= mx
            f *= my
            offset = r + f
            base.camera.setPos(base.camera.getPos() + offset)
            winProperties = base.win.getProperties()
            windowWidth = winProperties.get_x_size()
            windowHeight = winProperties.get_y_size()
            centerX = windowWidth / 2
            centerY = windowHeight / 2
            base.win.movePointer(0, int(centerX), int(centerY))
        #TODO add mouse wheel zoom in and out
        #if base.mouseWatcherNode.hasMouse() and self.mouse_down22:
        #    f = base.camera.getQuat().getForward()
        #    f *= base.camera.getPos()
        #    offset = f
        #    base.camera.setPos(base.camera.getPos() + offset)

        self.dt = globalClock.getDt()


        #self.walking = False


        

        # Accept key events (no need for separate press/release checks)
        
        base.disableMouse()
        #base.mouseWatcherNode.set_interest_as_whole_window()


        base.accept("mouse1-up", self.endTask)
        self.task_done = False

        base.accept("mouse1", self.handle_mouse_click)
        #base.accept("w", self.handle_key_event)
        base.accept("mouse3", self.handleRightClick)
        base.accept("mouse2", self.handleMidClick)
        base.accept("mouse3-up", self.handleRightClick)
        base.accept("mouse2-up", self.handleMidClick)
            

        CAMERA_SPEED = 50 
        base.accept("w", self.handle_key_event, ["w"])
        base.accept("w-up", self.handle_key_event, ["w-up"])
        base.accept("s", self.handle_key_event, ["s"])
        base.accept("s-up", self.handle_key_event, ["s-up"])
        base.accept("a", self.handle_key_event, ["a"])
        base.accept("a-up", self.handle_key_event, ["a-up"])
        base.accept("d", self.handle_key_event, ["d"])
        base.accept("d-up", self.handle_key_event, ["d-up"])

        #base.accept("w", self.moveCamera, extraArgs=[Vec3(0, CAMERA_SPEED, 0)])
        #base.accept("a", self.moveCamera, extraArgs=[Vec3(-CAMERA_SPEED, 0, 0)])
        #base.accept("s", self.moveCamera, extraArgs=[Vec3(0, -CAMERA_SPEED, 0)])
        #base.accept("d", self.moveCamera, extraArgs=[Vec3(CAMERA_SPEED, 0, 0)])


        # Create a CollisionHandlerQueuer with visualization mode set to Inlines
        if self.arrowx and self.arrowy and self.arrowz != None:
            if self.selected != {} or self.selected != None:
                self.Arrows[str(self.selected)] = {"x" : self.arrowx, "y" : self.arrowy, "z" : self.arrowz}
        try:
            for arrow in self.Arrows:
                arrow.setPos(self.selected.getPos())
        except Exception:
            pass
            #print(self.selected)
        while self.pipe.poll():
            request = self.pipe.recv()

            if request[0] == "resize":
                self.resizeWindow(request[1], request[2])
            elif request[0] == "close":
                sys.exit()
            if request[0] == "models/Arrow.objX":
                
                try:
                    if self.arrowx != None:
                        #arrow.reparentTo(render)
                        self.arrowx.setPos(request[3].getPos(request[3].getParent()))
                        self.selected = request[3]

                        self.selected.setTag('selected', '1')

                        print(self.arrowx.getPos())


                        # Customize arrow color, scale, etc.
                        self.arrow.setColor(Vec4(1, 0, 0, 1))  #
                        if request[2] == "x":
                            self.arrowx.setR(90)
                    else:
                        self.arrowx = loader.loadModel("models/Arrow.obj")
                        self.arrowx.reparentTo(render)
                        self.arrowx.setPos(request[3].getPos(request[3].getParent()))

                        self.selected = request[3]

                        self.arrowx.setTag('myObjectTagX', '1')

                        self.selected.setTag('selected', '1')

                        

                        print(self.arrowx.getPos())


                        # Customize arrow color, scale, etc.
                        self.arrowx.setColor(Vec4(1, 0, 0, 1))  #
                        if request[2] == "x":
                            self.arrowx.setR(90)

                        

                        self.manipulator = base.render.attachNewNode(PandaNode("xaxis"))

                        
                        self.arrowx.reparentTo(self.manipulator)
                        #self.arrowx.setBin("FixedEffectBin", 10)
                        self.arrowx.setDepthTest(False)
                        self.arrowx.setDepthWrite(0); 
                        self.arrowx.set_bin("fixed", 10000)

                        
                    
                except Exception:
                    pass
                
                    
            if request[0] == "models/Arrow.objY":
                
                try:
                    if self.arrowy != None:
                        #self.reparentTo(render)
                        self.arrowy.setPos(request[3].getPos(request[3].getParent()))
                        self.selected = request[3]

                        self.selected.setTag('selected', '1')

                        print(self.arrowy.getPos())

                        
                        # Customize arrow color, scale, etc.
                        self.arrowy.setColor(Vec4(0, 1, 0, 1))  #

                        if request[2] == "y":
                            self.arrowy.setP(90)
                    else:
                        self.arrowy = loader.loadModel("models/Arrow.obj")
                        self.arrowy.reparentTo(render)
                        self.arrowy.setPos(request[3].getPos(request[3].getParent()))

                        self.selected = request[3]

                        self.arrowy.setTag('myObjectTagY', '2')

                        self.selected.setTag('selected', '1')

                        print("Y: ", self.arrowy.getPos())


                        # Customize arrow color, scale, etc.
                        self.arrowy.setColor(Vec4(0, 1, 0, 1))  #
                        if request[2] == "y":
                            self.arrowy.setP(90)

                        #base.attachGeom(self.arrowy)

                        

                        self.manipulator = base.render.attachNewNode(PandaNode("yaxis"))

                        
                        self.arrowy.reparentTo(self.manipulator)

                        self.arrowy.reparentTo(self.manipulator)
                        #self.arrowx.setBin("FixedEffectBin", 10)
                        self.arrowy.setDepthTest(False)
                        self.arrowy.setDepthWrite(0); 
                        self.arrowy.set_bin("fixed", 10000)

                        
                except Exception:
                    pass
                    
            if request[0] == "models/Arrow.objZ":
                
                try:
                    #self.arrow.reparentTo(render)
                    if self.arrowz != None:
                        self.arrowz.setPos(request[3].getPos(request[3].getParent()))
                        self.selected = request[3]
                        
                        self.selected.setTag('selected', '1')

                        print(self.arrowz.getPos())
                        print(self.Arrows)

                        # Customize arrow color, scale, etc.
                        self.arrowz.setColor(Vec4(0, 0, 1, 1))  #

                        if request[2] == "z":
                            self.arrowz.setP(0)
                    else:
                        self.arrowz = loader.loadModel("models/Arrow.obj")
                        self.arrowz.reparentTo(render)
                        self.arrowz.setPos(request[3].getPos(request[3].getParent()))

                        self.selected = request[3]

                        self.arrowz.setTag('myObjectTagZ', '3')

                        self.selected.setTag('selected', '1')

                        print("Z: ", self.arrowz.getPos())


                        # Customize arrow color, scale, etc.
                        self.arrowz.setColor(Vec4(0, 1, 0, 1))  #
                        if request[2] == "z":
                            self.arrowz.setP(90)
                        
                        #self.manipulator = base.render.attachNewNode(PandaNode("zaxis"))

                        
                        #self.arrowz.reparentTo(self.manipulator)

                        self.arrowz.reparentTo(self.manipulator)
                        #self.arrowx.setBin("FixedEffectBin", 10)
                        self.arrowz.setDepthTest(False)
                        self.arrowz.setDepthWrite(0); 
                        self.arrowz.set_bin("fixed", 10000)
                        self.arrowz.setAttrib(DepthTestAttrib.make(DepthTestAttrib.MDisable))

                        
                        
                except Exception:
                    pass
            elif request[0] == "setPos":
                global p
                global selected_object
                #try:
                    
                    #global p
                #for f in self.loaded_models.keys():
                self.loaded_models[request[4]].setPos(request[1], request[2], request[3])
                print(request[4])
                #except Exception:
                #    try:
                #        print(request[4])
                #    except Exception as e:
                #        print('it doesnt exist', e)
            if request[0] == "setHpr":
                global p
                global selected_object
                #try:
                    #global p
                #for f in self.loaded_models.keys():
                self.loaded_models[request[4]].setHpr(request[1], request[2], request[3])
                print(request[4])
                #except Exception:
                #    try:
                #        print(request[4])
                #    except Exception as e:
                #        print('it doesnt exist', e)
            if request[0] == "setScale":
                global p
                global selected_object
                #try:
                    #global p
                #for f in self.loaded_models.keys():
                self.loaded_models[request[4]].setScale(request[1], request[2], request[3])
                print(request[4])
                #except Exception:
                #    try:
                #        print(request[4])
                #    except Exception as e:
                #        print('it doesnt exist', e)
                
            elif request[0] == "filepath":
                filepath = request[1]
                filepath2 = request[2]
                print("filepath: ", filepath, " filepath2: ", filepath2)
                self.num = random.randint(1000,9999)

                if filepath in filepath2:
                    filepath += f"({str(self.num)})"
                    print("HERE", self.loaded_models)
                
                    #h.model_name[self.get_filename(filepath)](filepath)
                filename = self.get_filename(request[1])
                filename = request[1]
                
                file_with_no_num = request[1]
                
                
                    
                #self.loaded_models[filename] = loader.loadModel(request[1])
                s = loader.loadModel(request[1])
                
                s.reparentTo(render)
                #if filename in self.loaded_models:
                
                filename += f"({str(self.num)})"
                self.loaded_models[filename] = s
                print("loaded models: ", self.loaded_models)
                #self.pipe.send(["Load", self.loaded_models, filepath, file_with_no_num])
                self.pipe.send(["Load", self.loaded_models, filename, filename])
            elif request[0] == "DirectionalLight":
                #amb_light = AmbientLight('amblight')
                #amb_light.set_color(Vec4(Vec3(1),1))
                #amb_light_node = base.render.attach_new_node(amb_light)
                #base.render.set_light(amb_light_node)
                # Create an ambient light node
                
                ambient_light = AmbientLight("AmbientLight")
                ambient_light.setColor(Vec4(Vec3(10), 1))  # Set ambient light color
                ambient_light_np = base.render.attachNewNode(ambient_light)

                # Enable lighting in the scene
                base.render.setLight(ambient_light_np)


                # Create a directional light node
                #sunlight = DirectionalLight("Sunlight")
                #sunlight.setColor((4, 4, 2, 1))  # Set light color (white)
                #sunlight.setShadowCaster(True)
                #sunlight_np = render.attachNewNode(sunlight)


                slight_1 = Spotlight('slight_1')
                slight_1.set_color(Vec4(Vec3(5),1))
                slight_1.set_shadow_caster(True, 4096, 4096)
                # slight_1.set_attenuation((0.5,0,0.000005))
                lens = PerspectiveLens()
                slight_1.set_lens(lens)
                slight_1.get_lens().set_fov(120)
                slight_1_node = render.attach_new_node(slight_1)
                slight_1_node.set_pos(50, 50, 90)
                slight_1_node.look_at(0,0,0.5)
                render.set_light(slight_1_node)

                slight_2 = Spotlight('slight_2')
                slight_2.set_color(Vec4(Vec3(5),1))
                # slight_2.set_shadow_caster(True, 16384, 16384)
                slight_2.set_attenuation((0.5,0,0.0005))
                lens = PerspectiveLens()
                slight_2.set_lens(lens)
                slight_2.get_lens().set_fov(90)
                slight_2_node = base.render.attach_new_node(slight_2)
                slight_2_node.set_pos(-82, -79, 50)
                slight_2_node.look_at(0,0,0.5)
                base.render.set_light(slight_2_node)

                env_light_1 = PointLight('env_light_1')
                env_light_1.set_color(Vec4(Vec3(6),1))#vec3(6),1
                env_light_1 = base.render.attach_new_node(env_light_1)
                env_light_1.set_pos(0,0,0)

                base_env = loader.load_model('models/daytime_skybox.bam')
                base_env.reparent_to(base.render)
                base_env.set_scale(1)
                base_env.set_pos(0,0,0)
                base_env.set_light(env_light_1)
                base_env.set_light_off(base.render.find('**/slight_1'))

                
                ## Set the direction of the light
                #sunlight_np.setHpr(180, -40, 0)  # Set the direction of the light (in this case, facing downwards)
                ##self.complexpbrPipeline = complexpbr.apply_shader(base.render)
                ##self.complexpbrPipeline.enable_shadows(sunlight_np)
                #if self.complexpbrPipeline is not None:
                #    self.complexpbrPipeline.enable_shadows(sunlight_np)
                #else: 
                #    print("Error: ComplexPBR pipeline is not initialized. Shadows cannot be enabled.")






                # Enable lighting in the scene
                #render.setLight(sunlight_np)

                #setting the shadow caster
                #sunlight.setShadowCaster(True, 512, 512)
                
            elif request[0] == "filepathdel":
                filenamedel = request[1]
                filename = request[1]
                print("request 1: ", filenamedel, "\nrequest 2: ", filename)
                
                #node_to_delete = self.findNode(filenamedel)
                filename_no_num = self.remove_last_six_digits(filenamedel)
                try:
                    node_to_delete = render.find(os.path.basename(filenamedel))
                    if not node_to_delete:
                        node_to_delete = render.find(os.path.basename(filename_no_num))
                except Exception as e:
                    print("Exception: ", e)
                print(node_to_delete)
                if node_to_delete:
                    del self.loaded_models[filenamedel]
                    #self.loaded_models.pop(filenamedel)
                    self.pipe.send(["Deleting: ", self.loaded_models])
                    node_to_delete.removeNode()
                    loader.unloadModel(filenamedel)
                    print('deleted model: ', filenamedel)
                else:
                    print(f"Model with filename '{filename_no_num}' not found in scene graph.")
                
            
        return task.cont


import wx.lib.scrolledpanel as scrolled
import wx.lib.floatcanvas.FloatCanvas as FC

class NodePanel(wx.Panel):
    def __init__(self, parent, node_id, text="Node", input_value="", output_value="", checkbox_state=False, style=wx.BORDER_RAISED):
        super().__init__(parent)
        self.node_id = node_id
        self.selected = False
        #self.sizer2 = wx.BoxSizer(wx.VERTICAL)
        
        self.SetWindowStyleFlag(wx.BORDER_RAISED)
        if node_id == "behavior tree":
            self.sizer2 = wx.BoxSizer(wx.VERTICAL)
            self.title = wx.StaticText(self, label=node_id)
            self.sizer2.Add(self.title, 0, wx.EXPAND | wx.ALL, 5)
            self.input1 = wx.StaticText(self, label="input")
            self.input_ctrl = wx.TextCtrl(self, value=input_value)
            self.output_source = wx.StaticText(self, label="output source")
            self.output_ctrl = wx.TextCtrl(self, value=output_value)
            #self.add_input = wx.Button(self, label="add input")
            self.sizer2.Add(self.input1, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input_ctrl, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.output_source, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.output_ctrl, 0, wx.EXPAND | wx.ALL, 5)
            #self.sizer2.Add(self.add_input, 0, wx.EXPAND | wx.ALL, 5)
            #self.Bind(wx.EVT_BUTTON, self.on_add_input, self.add_input)
            self.num_of_inputs = [1]

            self.SetSizer(self.sizer2)
        
        elif node_id == "Precondition switch":
            
            self.sizer2 = wx.GridSizer(rows=15, cols=2, vgap=1, hgap=1)
            
            self.string = wx.StaticText(self, label="")
            self.title = wx.StaticText(self, label=node_id)
            self.sizer2.Add(self.title, 0, wx.EXPAND | wx.ALL, 5)
            self.input1 = wx.StaticText(self, label="Precondition input 1")
            self.input_ctrl = wx.TextCtrl(self, value=input_value)
            self.input2 = wx.StaticText(self, label="Precondition input 2")
            self.input_ctrl2 = wx.TextCtrl(self, value=input_value)
            self.input3 = wx.StaticText(self, label="Precondition input 3")
            self.input_ctrl3 = wx.TextCtrl(self, value=input_value)
            self.input4 = wx.StaticText(self, label="Precondition input 4")
            self.input_ctrl4 = wx.TextCtrl(self, value=input_value)
            self.input5 = wx.StaticText(self, label="Precondition input 5")
            self.input_ctrl5 = wx.TextCtrl(self, value=input_value)
            self.input6 = wx.StaticText(self, label="Precondition input 6")
            self.input_ctrl6 = wx.TextCtrl(self, value=input_value)
            self.input7 = wx.StaticText(self, label="Precondition input 7")
            self.input_ctrl7 = wx.TextCtrl(self, value=input_value)
            self.input8 = wx.StaticText(self, label="Precondition input 8")
            self.input_ctrl8 = wx.TextCtrl(self, value=input_value)
            self.input9 = wx.StaticText(self, label="Precondition input 9")
            self.input_ctrl9 = wx.TextCtrl(self, value=input_value)
            self.input10 = wx.StaticText(self, label="Precondition input 10")
            self.input_ctrl10 = wx.TextCtrl(self, value=input_value)
            self.input11 = wx.StaticText(self, label="Precondition input 11")
            self.input_ctrl11 = wx.TextCtrl(self, value=input_value)
            self.input12 = wx.StaticText(self, label="Precondition input 12")
            self.input_ctrl12 = wx.TextCtrl(self, value=input_value)
            self.output_source = wx.StaticText(self, label="output source")
            
            self.output_ctrl = wx.TextCtrl(self, value=output_value)
            self.precondition_dict = {"input1": self.input_ctrl.GetValue(), "input2": self.input_ctrl2.GetValue(), "input3": self.input_ctrl3.GetValue(), "input4": self.input_ctrl4.GetValue(), "input5": self.input_ctrl5.GetValue(),
                                  "input6": self.input_ctrl6.GetValue(), "input7": self.input_ctrl7.GetValue(), "input8": self.input_ctrl8.GetValue(), "input9": self.input_ctrl9.GetValue(), "input10": self.input_ctrl10.GetValue(),
                                    "input11": self.input_ctrl11.GetValue(), "input12": self.input_ctrl12.GetValue()}


            #self.add_input = wx.Button(self, label="add input")
            self.sizer2.Add(self.string, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input1, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input_ctrl, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input2, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input_ctrl2, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input3, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input_ctrl3, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input4, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input_ctrl4, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input5, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input_ctrl5, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input6, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input_ctrl6, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input7, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input_ctrl7, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input8, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input_ctrl8, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input9, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input_ctrl9, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input10, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input_ctrl10, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input11, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input_ctrl11, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input12, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input_ctrl12, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.output_source, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.output_ctrl, 0, wx.EXPAND | wx.ALL, 5)

            self.SetSizer(self.sizer2)
        elif node_id == "Action":
            panel = wx.Panel(self)
            #self.sizer3 = wx.BoxSizer(wx.VERTICAL)
            self.title = wx.StaticText(panel, label=node_id)

            # Get the workspace directory
            workspace_dir = "./"  # Change this to your workspace directory path

            # Get a list of filenames in the workspace directory
            files = os.listdir(workspace_dir)

            # Create a list box with the filenames
            self.combo_box = wx.ComboBox(panel, choices=files, style=wx.CB_READONLY)

            self.button_create = wx.Button(panel, label="Create New Python File")

            # Create a sizer for the panel
            sizer4 = wx.BoxSizer(wx.VERTICAL)



            # Bind an event handler for item selection
            self.combo_box.Bind(wx.EVT_LISTBOX, self.on_select)
            self.combo_box.Bind(wx.EVT_COMBOBOX_DROPDOWN, self.on_dropdown)
            sizer4.Add(self.button_create, 0, wx.EXPAND | wx.ALL, 5)
            panel.SetSizer(sizer4)

            # Set sizer for the panel
            
            sizer4.Add(self.combo_box, 0, wx.EXPAND | wx.ALL, 5)
            panel.SetSizerAndFit(sizer4)
            
            self.button_create.Bind(wx.EVT_BUTTON, self.on_create_file)

            self.Show()

            # Show the frame
            #self.Show()

            

            #self.sizer2.Add(self.checkbox, 0, wx.EXPAND | wx.ALL, 5)
            #self.sizer2.Add(self.input1, 0, wx.EXPAND | wx.ALL, 5)
            #self.sizer2.Add(self.input_ctrl, 0, wx.EXPAND | wx.ALL, 5)
            #self.sizer2.Add(self.output_source, 0, wx.EXPAND | wx.ALL, 5)
            #self.sizer2.Add(self.output_ctrl, 0, wx.EXPAND | wx.ALL, 5)
#
            #self.Bind(wx.EVT_CHECKBOX, self.on_checkbox_change, self.checkbox)
            #self.Bind(wx.EVT_TEXT, self.on_input_change, self.input_ctrl)
            #self.Bind(wx.EVT_PAINT, self.on_paint)
            #self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        else:
            self.sizer2 = wx.BoxSizer(wx.VERTICAL)
            self.checkbox = wx.CheckBox(self, label="Checkbox")
            self.input1 = wx.StaticText(self, label="input1")
            self.input_ctrl = wx.TextCtrl(self, value=input_value)
            self.output_source = wx.StaticText(self, label="output source")
            self.output_ctrl = wx.TextCtrl(self, value=output_value)

            self.sizer2.Add(self.checkbox, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input1, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.input_ctrl, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.output_source, 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(self.output_ctrl, 0, wx.EXPAND | wx.ALL, 5)

            self.Bind(wx.EVT_CHECKBOX, self.on_checkbox_change, self.checkbox)
            self.Bind(wx.EVT_TEXT, self.on_input_change, self.input_ctrl)
            self.Bind(wx.EVT_PAINT, self.on_paint)
            self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        
        
        
        
            self.SetSizer(self.sizer2)
        
    def on_dropdown(self, event):
        # Clear the current items
        self.combo_box.Clear()

        # Get the current directory
        current_dir = os.getcwd()

        # Filter the files to show only .py files
        py_files = [filename for filename in os.listdir(current_dir) if filename.endswith(".py")]

        # Populate the combo box with .py files
        for py_file in py_files:
            self.combo_box.Append(py_file)
    def on_create_file(self, event):
        wildcard = "Python files (*.py)|*.py"
        dlg = wx.FileDialog(self, "Create a new Python file", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            with open(filepath, 'w') as f:
                # Write base content to the file
                f.write("# This is a new Python file\n")
                f.write("# Add your code here\n")

            self.combobox.SetValue(filepath)

        dlg.Destroy()  
    def on_select(self, event):
        # Get the selected item
        selected_index = event.GetSelection()
        selected_item = event.GetEventObject().GetString(selected_index)
    def on_add_input(self, event):
        self.sizer2.Clear()
        self.DestroyChildren()
        self.title = wx.StaticText(self, label=self.node_id)
        self.input1 = wx.StaticText(self, label="input1")
        self.input_ctrl = wx.TextCtrl(self, value="")
        self.output_source = wx.StaticText(self, label="output")
        self.output_ctrl = wx.TextCtrl(self, value="")
        
        self.sizer2.Add(self.title, 0, wx.EXPAND | wx.ALL, 5)
        self.sizer2.Add(self.input1, 0, wx.EXPAND | wx.ALL, 5)
        self.sizer2.Add(self.input_ctrl, 0, wx.EXPAND | wx.ALL, 5)
        self.sizer2.Add(self.output_source, 0, wx.EXPAND | wx.ALL, 5)
        self.sizer2.Add(self.output_ctrl, 0, wx.EXPAND | wx.ALL, 5)
        
        for input in self.num_of_inputs:
            print(self.num_of_inputs)
            self.sizer2.Add(wx.StaticText(self, label="input"), 0, wx.EXPAND | wx.ALL, 5)
            self.sizer2.Add(wx.TextCtrl(self, value=""), 0, wx.EXPAND | wx.ALL, 5)
        self.add_input = wx.Button(self, label="add input")
        self.sizer2.Add(self.add_input, 0, wx.EXPAND | wx.ALL, 5)

        self.Bind(wx.EVT_BUTTON, self.on_add_input, self.add_input)

        self.sizer2.Layout()
        self.num_of_inputs.append(random.randint(1,1000000))


        
    def on_checkbox_change(self, event):
        checkbox_state = self.checkbox.GetValue()
        print(f"Checkbox state of Node {self.node_id}: {checkbox_state}")
    
    def on_input_change(self, event):
        input_value = self.input_ctrl.GetValue()
        print(f"Input value of Node {self.node_id}: {input_value}")
    
    def on_paint(self, event):
        dc = wx.PaintDC(self)
        if self.selected:
            dc.SetPen(wx.Pen(wx.RED, 2))
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            rect = wx.Rect(0, 0, self.GetSize().width, self.GetSize().height)
            dc.DrawRectangle(rect)
        event.Skip()

    def on_left_down(self, event):
        self.selected = not self.selected
        self.Refresh()
        event.Skip()

class AIEditor(wx.ScrolledWindow):
    def __init__(self, parent):
        super().__init__(parent)
        self.init_ui()
        self.nodes = []
        self.connections = []

    def init_ui(self):
        self.sizer2 = wx.GridSizer(wx.VERTICAL)
        node1 = NodePanel(self, node_id="brain jar")
        node2 = NodePanel(self, node_id="behavior tree")
        self.sizer2.Add(node1, 0, wx.LC_REPORT | wx.ALL, 5)
        self.sizer2.Add(node2, 0, wx.LC_REPORT | wx.ALL, 5)
        self.SetSizer(self.sizer2)

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

        self.Bind(wx.EVT_MIDDLE_DOWN, self.on_middle_down)
        self.Bind(wx.EVT_MIDDLE_UP, self.on_middle_up)
        self.Bind(wx.EVT_MOTION, self.on_mouse_motion)

        self.dragging = False
        self.last_mouse_pos = None
    def on_middle_down(self, event):
        self.dragging = True
        self.last_mouse_pos = event.GetPosition()

    def on_middle_up(self, event):
        self.dragging = False

    def on_mouse_motion(self, event):
        if self.dragging and event.MiddleIsDown():
            current_pos = event.GetPosition()
            delta = current_pos - self.last_mouse_pos
            self.Scroll(self.GetViewStart()[0] - delta.x, self.GetViewStart()[1] - delta.y)
            self.last_mouse_pos = current_pos
            self.Refresh()

    def on_paint(self, event):
        # Your paint logic here
        pass

    def on_right_click(self, event):
        menu = wx.Menu()
        add_node_item = menu.AppendSubMenu(wx.Menu(), "Add Node")
        self.add_node_submenu(add_node_item.GetSubMenu())
        search_node_item = menu.Append(wx.ID_ANY, "Search for a Node")

        self.Bind(wx.EVT_MENU, self.on_search_node, search_node_item)

        self.PopupMenu(menu)
        menu.Destroy()

    def add_node_submenu(self, submenu):
        nodes = ["brain jar", "follow object", "run away", "Perform Custom Function", "Precondition switch", "Precondition tree", "animation",
                  "behavior Properties", "Action", "FailIfPrecondition", "OnPrecondition"]
        for node_id in nodes:  # Assuming there are 5 node options
            node_item = submenu.Append(wx.ID_ANY, f"Node {node_id}")
            
            self.Bind(wx.EVT_MENU, lambda event, id=node_id: self.on_add_selected_node(id), node_item)
            

    def on_add_selected_node(self, node_id):
        # Logic to add the selected node to the node graph
        new_node = NodePanel(self, node_id=node_id)
        self.nodes.append(new_node)
        self.sizer2.Add(new_node, 0, wx.LC_REPORT | wx.ALL, 5)
        self.Layout()

    def on_search_node(self, event):
        # Logic to search for a node
        pass





class Animation(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        # Define animation sequences dictionary
        self.animation_sequences = {}

        self.init_ui()

    def init_ui(self):
        # Create a vertical box sizer for the main layout
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Create a horizontal box sizer for the animation list and properties
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        # Create a checklist box to display animation sequences
        self.anim_list = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.anim_list.InsertColumn(0, "Animations")
        hbox.Add(self.anim_list, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        # Create a panel for properties
        self.prop_panel = wx.Panel(self)
        self.add_properties(self.prop_panel)
        hbox.Add(self.prop_panel, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        # Add the horizontal sizer to the vertical sizer
        vbox.Add(hbox, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        # Create a horizontal box sizer for the buttons
        button_hbox = wx.BoxSizer(wx.HORIZONTAL)

        # Create buttons for adding, removing, and editing animation sequences
        add_button = wx.Button(self, label='Add')
        get_selected_button = wx.Button(self, label='Get Selected Animations')
        get_selected_button.Bind(wx.EVT_BUTTON, self.on_get_selected)

        # Bind button events
        add_button.Bind(wx.EVT_BUTTON, self.on_add)

        # Add buttons to horizontal sizer
        button_hbox.Add(add_button, flag=wx.EXPAND | wx.ALL, border=5)
        button_hbox.Add(get_selected_button, flag=wx.EXPAND | wx.ALL, border=5)

        # Add button horizontal sizer to the vertical sizer
        vbox.Add(button_hbox, flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(vbox)

        # Create a file dialog
        self.file_dialog = wx.FileDialog(self, "Select Animation Files", wildcard="Animation Files (*.egg;*.bam)|*.egg;*.bam",
                                         style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST)

        # Show the frame
        self.Show()

    def add_properties(self, panel):
        # Add properties controls to the panel
        # For example, you can add text controls, sliders, etc.
        prop_vbox = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(prop_vbox)

        # Example properties controls
        prop_label = wx.StaticText(panel, label="Properties:")
        isIdle = wx.CheckBox(panel, label="Is Idle")

        # Add properties controls to the panel's sizer
        prop_vbox.Add(prop_label, flag=wx.EXPAND | wx.ALL, border=5)
        prop_vbox.Add(isIdle, flag=wx.EXPAND | wx.ALL, border=5)

    def on_add(self, event):
        # Show the file dialog
        if self.file_dialog.ShowModal() == wx.ID_CANCEL:
            return  # User canceled the operation

        # Get the paths of the selected files
        selected_files = self.file_dialog.GetPaths()

        # Specify the directory against which paths will be made relative
        base_directory = "D:/~000AAAclients/test/Documents/SimpleThirdPersonCamera-main"

        # Process each selected file
        for file_path in selected_files:
            # Check the file extension
            if file_path.endswith(".egg") or file_path.endswith(".bam"):
                # Get the relative path of the file
                relative_file_path = os.path.relpath(file_path, base_directory)

                # Get the local file name (including folder structure)
                local_file_name = os.path.normpath(relative_file_path)

                # Load the actor using the local file name
                self.actor = Actor(local_file_name)

                # Check if the actor loaded successfully
                if not self.actor.isEmpty():
                    # Clear the checklist before populating
                    self.anim_list.DeleteAllItems()

                    # Populate the checklist with animation names
                    animations = self.actor.getAnimNames()
                    for animation in animations:
                        self.anim_list.Append([animation])

                    # Add NLA tracks to the checklist
                    nla_tracks = self.actor.getAnimControls()
                    for track_name in nla_tracks:
                        self.anim_list.Append(["NLA: " + track_name])
            else:
                # Notify the user about invalid file types
                wx.MessageBox(f"Invalid file type: {file_path}\nOnly .egg and .bam files are supported.",
                              "Error", wx.OK | wx.ICON_ERROR)

    def on_get_selected(self, event):
        selected_indices = []
        # Iterate over the items in the list
        for i in range(self.anim_list.GetItemCount()):
            # Check if the item at index i is checked
            if self.anim_list.IsItemChecked(i):
                # If checked, add its index to the list of selected indices
                selected_indices.append(i)

        # Get the text of the selected items using their indices
        selected_animations = [self.anim_list.GetItemText(i) for i in selected_indices]
        print("Selected animations:", selected_animations)



    



    def on_close(self, event):
        self.file_dialog.Destroy()
        self.Destroy()
    def on_remove(self, event):
        # Implement logic for removing the selected animation sequence
        pass

    def on_edit(self, event):
        # Get the index of the selected item in the list control
        index = self.anim_list_ctrl.GetFirstSelected()

        if index != -1:
            # Retrieve the data associated with the selected item
            item_data = self.anim_list_ctrl.GetItemData(index)

            # Access the animation sequence using the item data
            selected_sequence = self.animation_sequences.get(item_data)

            if selected_sequence is not None:
                # Open the dialog to edit the selected sequence
                edit_dialog = EditAnimationSequenceDialog(self, selected_sequence)
                edit_dialog.ShowModal()
                edit_dialog.Destroy()
            else:
                wx.MessageBox("Invalid sequence selected.", "Error", wx.OK | wx.ICON_ERROR)
        else:
            wx.MessageBox("Please select an animation sequence to edit.", "No Sequence Selected", wx.OK | wx.ICON_INFORMATION)


# Example of a dialog for editing animation sequences
class EditAnimationSequenceDialog(wx.Dialog):
    def __init__(self, parent, sequence):
        super().__init__(parent, title="Edit Animation Sequence")

        self.sequence = sequence

        # Create controls and layout for editing the animation sequence
        self.init_ui()

    def init_ui(self):
        print(self.sequence)
        # Add controls such as text boxes, sliders, or dropdowns to edit sequence properties

        # Example: Display the name of the sequence
        name_label = wx.StaticText(self, label="Sequence Name:")
        self.name_textctrl = wx.TextCtrl(self, value=self.sequence)

        # Example: Display the duration of the sequence
        duration_label = wx.StaticText(self, label="Sequence Duration:")
        self.duration_textctrl = wx.TextCtrl(self, value=str(self.sequence.duration))

        # Example: Add OK and Cancel buttons to apply or discard changes
        ok_button = wx.Button(self, label="OK")
        cancel_button = wx.Button(self, label="Cancel")
        ok_button.Bind(wx.EVT_BUTTON, self.on_ok)
        cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

        # Layout controls using sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(name_label, 0, wx.ALL, 5)
        sizer.Add(self.name_textctrl, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(duration_label, 0, wx.ALL, 5)
        sizer.Add(self.duration_textctrl, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(ok_button, 0, wx.ALL | wx.ALIGN_RIGHT, 5)
        sizer.Add(cancel_button, 0, wx.ALL | wx.ALIGN_RIGHT, 5)
        self.SetSizer(sizer)
        sizer.Fit(self)

    def on_ok(self, event):
        # Apply changes to the sequence and close the dialog
        self.sequence.name = self.name_textctrl.GetValue()
        self.sequence.duration = int(self.duration_textctrl.GetValue())
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        # Discard changes and close the dialog
        self.EndModal(wx.ID_CANCEL)

class objectslist(wx.Panel):
    """A special Panel which holds a Panda3d window."""
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        # See __doc__ of initialize() for this callback
        # Create a timer that fires every second

        

        self.timerw = 0

        self.object_node = None

        self.timerx = False
        self.timery = False
        self.timerz = False
        self.loops = 0

        self.created_arrows = False

        self.arrow = []

        self.arrows = {}

        self.loaded = False

        self.model_list = wx.TreeCtrl(self, wx.ID_ANY, size=(400,150))

        self.model_list.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_object_selected)

        self.root = self.model_list.AddRoot("Root")

        self.model_name_not_p = {}
        #self.Prev_model_name_not_p = {}

        self.model_name = {}

        self.load_button = wx.Button(self, wx.ID_ANY, label="Load")
        self.delete_button = wx.Button(self, wx.ID_ANY, label="Delete", pos=(100, 0))

        for model in p.loaded_models:  # Assuming 'panda_app' is your Panda3dApp instance
            unique_key = model
            if model not in self.model_name_not_p:
                #self.model_list.DeleteAllItems()
                print("model", model)
                self.model_list.AppendItem(self.root, str(model))#2, str(model))
                #loading models path
                self.model_name_not_p[unique_key] = model

        # Bind event handlers
        self.Bind(wx.EVT_BUTTON, self.on_load_button, self.load_button)
        self.Bind(wx.EVT_BUTTON, self.on_delete_button, self.delete_button)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_object_selected)

        #self.model_list = wx.ListCtrl(self, wx.ID_ANY, style=wx.LC_REPORT)

        

        

        #self.x_slider = wx.Slider(self, wx.ID_ANY, value=0, minValue=-10000000, maxValue=10000000, name="x", pos=(400,0))
        self.x_slider = wx.TextCtrl(self, id=wx.ID_ANY, value="0", pos=(30, 220), name="x", style=1, size=(70, 20))
        self.y_slider = wx.TextCtrl(self, id=wx.ID_ANY, value="0", pos=(150, 220), name="y", style=0, size=(70, 20))
        self.z_slider = wx.TextCtrl(self, id=wx.ID_ANY, value="0", pos=(270, 220), name="z", style=0, size=(70, 20))

        
        self.x_slider_rot = wx.TextCtrl(self, id=wx.ID_ANY, value="0", pos=(30, 260), name="x", style=1, size=(70, 20))
        self.y_slider_rot = wx.TextCtrl(self, id=wx.ID_ANY, value="0", pos=(150, 260), name="y", style=0, size=(70, 20))
        self.z_slider_rot = wx.TextCtrl(self, id=wx.ID_ANY, value="0", pos=(270, 260), name="z", style=0, size=(70, 20))
        
        self.x_slider_scale = wx.TextCtrl(self, id=wx.ID_ANY, value="0", pos=(30, 300), name="x", style=1, size=(70, 20))
        self.y_slider_scale = wx.TextCtrl(self, id=wx.ID_ANY, value="0", pos=(150, 300), name="y", style=0, size=(70, 20))
        self.z_slider_scale = wx.TextCtrl(self, id=wx.ID_ANY, value="0", pos=(270, 300), name="z", style=0, size=(70, 20))
        
        font = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.pos_lable = wx.StaticText(self, label="Position: ", pos=(20, 200))
        self.x_lable = wx.StaticText(self, label="x: ", pos=(10, 220))
        self.y_lable = wx.StaticText(self, label="y: ", pos=(130, 220))
        self.z_lable = wx.StaticText(self, label="z: ", pos=(250, 220))
        self.pos_lable.SetFont(font)
        self.x_lable.SetFont(font)
        self.y_lable.SetFont(font)
        self.z_lable.SetFont(font)
        self.rot_lable = wx.StaticText(self, label="Rotation: ", pos=(20, 240))
        self.rot_x_lable = wx.StaticText(self, label="x: ", pos=(10, 260))
        self.rot_y_lable = wx.StaticText(self, label="y: ", pos=(130, 260))
        self.rot_z_lable = wx.StaticText(self, label="z: ", pos=(250, 260))
        self.rot_lable.SetFont(font)
        self.rot_x_lable.SetFont(font)
        self.rot_y_lable.SetFont(font)
        self.rot_z_lable.SetFont(font)
        self.scale_lable = wx.StaticText(self, label="Scale: ", pos=(20, 280))
        self.scale_x_lable = wx.StaticText(self, label="x: ", pos=(10, 300))
        self.scale_y_lable = wx.StaticText(self, label="y: ", pos=(130, 300))
        self.scale_z_lable = wx.StaticText(self, label="z: ", pos=(250, 300))
        self.scale_lable.SetFont(font)
        self.scale_x_lable.SetFont(font)
        self.scale_y_lable.SetFont(font)
        self.scale_z_lable.SetFont(font)
        self.refresh_list()
        

        self.x_slider.Bind(wx.EVT_TEXT, self.updateTransforms)
        self.y_slider.Bind(wx.EVT_TEXT, self.updateTransforms)
        self.z_slider.Bind(wx.EVT_TEXT, self.updateTransforms)
        self.x_slider_rot.Bind(wx.EVT_TEXT, self.updateTransforms)
        self.y_slider_rot.Bind(wx.EVT_TEXT, self.updateTransforms)
        self.z_slider_rot.Bind(wx.EVT_TEXT, self.updateTransforms)
        self.x_slider_scale.Bind(wx.EVT_TEXT, self.updateTransforms)
        self.y_slider_scale.Bind(wx.EVT_TEXT, self.updateTransforms)
        self.z_slider_scale.Bind(wx.EVT_TEXT, self.updateTransforms)


        
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onShow, self.timer)
        self.timer.Start(0)  # Start timer with 1 second interval
        
        
        


        

        
        #self.onShow()
    def onShow(self, event):
        global selected_object
        
        #try:
        #if selected_object != None and self.timerw >= 1:

            #self.posxyz = p.loaded_models[self.selected_object_name].getPos()
            #self.rotxyz = p.loaded_models[self.selected_object_name].getHpr()
            #self.scalexyz = p.loaded_models[self.selected_object_name].getScale()
#
            #self.x_slider.SetValue(str(self.posxyz[0]))
            #self.y_slider.SetValue(str(self.posxyz[1]))
            #self.z_slider.SetValue(str(self.posxyz[2]))
            #self.timerw = 0
                #self.x_slider_rot, self.y_slider_rot, self.z_slider_rot = self.posxyz
                #self.x_slider_scale, self.y_slider_scale, self.z_slider_scale = self.posxyz
        #except Exception:
         #   print('error')
        
        self.timerw += 0.1
        if not self.loaded: 
            #self.model_list.InsertColumn(0, 'Model Name', wx.LIST_FORMAT_RIGHT, 150)  # Define column width
            #self.model_list.InsertColumn(1, 'Path', wx.LIST_FORMAT_RIGHT, 150)  # Define column width
            self.model_list.SetPosition((0, 50))

            
            self.loaded = True
        #print("p.loaded_models: ", p.loaded_models)
        #self.model_list.DeleteAllItems()
        #self.model_name_not_p = {}
        #for model in p.loaded_models:  # Assuming 'panda_app' is your Panda3dApp instance
        #    unique_key = model
        #    if model not in self.model_name_not_p:
        #        #self.model_list.DeleteAllItems()
        #        print("model", model)
        #        self.model_list.InsertStringItem(2, str(model))
        #        #loading models path
        #        self.model_name_not_p[unique_key] = model
                
        #p.loaded_models = self.

        #for loop in range(0):
        

        selection = self.model_list.GetSelection()
        if selection.IsOk():
            selected_object = self.model_list.GetItemText(selection)

        #if self.model_list.GetFocusedItem() != -1:

         #   selected_object = self.model_list.GetItemText(self.model_list.GetFocusedItem(), 0)




        if self.loops <= 1:
            if self.timerx == True:
                self.create_arrow(self.object_node, Vec4(1, 0, 0, 1), "x")
                if self.timerw > 0.2:
                    self.timerw = 0
                    self.timery = True
                    self.timerx = False
            if self.timery == True:
                self.create_arrow(self.object_node, Vec4(0, 1, 0, 1), "y")
                if self.timerw == 0.1:
                    self.timerw = 0
                    self.timerz = True
                    self.timery = False
            if self.timerz == True:
                self.create_arrow(self.object_node, Vec4(0, 0, 1, 1), "z")
                if self.timerw > 0.1:
                    self.loops += 1
                    self.timerx = True
                    self.timerz = False
        else:
            self.timerx = False
    def updateTransforms(self, event):
        try:

            


            x = float(self.x_slider.GetValue())
            y = float(self.y_slider.GetValue())
            z = float(self.z_slider.GetValue())

            p.loaded_models[self.selected_object_name].setPos(x, y, z)

            p.setObjPos(x, y, z, self.selected_object_name)

            h1 = float(self.x_slider_rot.GetValue())
            p1 = float(self.y_slider_rot.GetValue())
            r = float(self.z_slider_rot.GetValue())

            x = float(self.x_slider_scale.GetValue())
            y = float(self.y_slider_scale.GetValue())
            z = float(self.z_slider_scale.GetValue())

            p.loaded_models[self.selected_object_name].setHpr(h1, p1, r)
            p.setObjRot(h1, p1, r, self.selected_object_name)
            p.loaded_models[self.selected_object_name].setScale(x, y, z)
            p.setObjScale(x, y, z, self.selected_object_name)

            print(p.loaded_models[self.selected_object_name].getPos())
            print(p.loaded_models[self.selected_object_name].getHpr())
            
            
        except Exception:
            pass
            #print(p.loaded_models[self.selected_object_name])
        #p.setObjRot(self.x_slider_rot, self.y_slider_rot, self.z_slider_rot)
        
    def create_arrow(self, parent, color, direction):
            # Create a simple arrow geometry using Panda3D primitives
        if direction == "x":
            p.create_arrow = "models/Arrow.objX"
            #self.arrow.append([parent, color, direction, "models/Arrow.objX"])
        elif direction == "y":
            p.create_arrow = "models/Arrow.objY"
            #self.arrow.append([parent, color, direction, "models/Arrow.objY"])
        elif direction == "z":
            p.create_arrow = "models/Arrow.objZ"
            #self.arrow.append([parent, color, direction, "models/Arrow.objZ"])
        p.Arrow_color = color
        p.Arrow_direction = direction 
        p.Arrow_parent = parent

    def on_object_selected(self, event):
        #self.selected_object_name = self.model_list.GetItemText(self.model_list.GetFocusedItem(), 1)
        selection = self.model_list.GetSelection()
        if selection.IsOk():
            self.selected_object_name = self.model_list.GetItemText(selection)
            self.selected_object_name = self.model_name[self.selected_object_name]
        

        # Check if object exists in the scene
        if self.selected_object_name not in self.arrows:
            # Load the object using your Panda3D logic
            self.object_node = p.loaded_models[self.selected_object_name]

            # Create arrows for each axis (X, Y, Z)
            self.timerx = True
            self.timerw = 0
            self.loops = 0
            self.arrows[self.selected_object_name] = {
                "x": (self.object_node, Vec4(1, 0, 0, 1), "x"),
                "y": (self.object_node, Vec4(0, 1, 0, 1), "y"),
                "z": (self.object_node, Vec4(0, 0, 1, 1), "z"),
            }
        else:
            self.object_node = p.loaded_models[self.selected_object_name]
            self.timerw = 0
            self.loops = 0
            self.timerx = True
        p.Arrow_parent = self.object_node
        
            
    def refresh_list(self):
        global assigned_scripts
        #self.model_list.DeleteAllItems()
        self.model_list.DeleteChildren(self.root)

        # Add loaded models to the tree
        for model in p.loaded_models:
            unique_key = model
            item = self.model_list.AppendItem(self.root, os.path.basename(model))
            self.model_list.SetItemData(item, model)
            self.model_name_not_p[unique_key] = model
            self.model_name[os.path.basename(model)] = model
            if os.path.basename(model) not in assigned_scripts:
                assigned_scripts[os.path.basename(model)] = []
    def on_load_button(self, event):
        # Open user's default file open dialog with appropriate filters
        script_dir = os.path.dirname(__file__)
        wildcard = os.path.join(script_dir, "Model Files (*.obj;*.egg;*.bam)|*.obj;*.egg;*.bam")
        dialog = wx.FileDialog(self, message="Select a model to load",
                               wildcard=wildcard, style=wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            filepath = dialog.GetPath()
            filepath = os.path.relpath(filepath, os.path.dirname(__file__))
            if "\\" in filepath:  # Check if backward slashes exist
                filepath = filepath.replace("\\", "/")

            p.filepath = filepath
            

            self.refresh_list()
            print(p.loaded_models)
            # Process the selected file
            print(f"Loading model: {filepath}")
            print(f"Loading model path: {p.filepath}")

    def on_delete_button(self, event):
        selected_item = self.model_list.GetSelection()
        if selected_item:
            model_path = self.model_name[self.model_list.GetItemData(selected_item)]
            if model_path:
                try:
                    model = os.path.basename(model_path)
                    p.loaded_models.pop(model_path)  # Assuming loaded_models is a list of filepaths
                    if model in assigned_scripts:
                        assigned_scripts.pop(model)
                    if model in object_properties:
                        object_properties.pop(model)
                    self.model_list.Delete(selected_item)
                except ValueError:
                    pass  # Extract filename
    
            # Find the model name in self.model_name using the filename
            for key, value in self.model_name.items():
                if os.path.basename(key) == os.path.basename(model_path):  # Compare filenames
                    try:
                        
                        del self.model_name[key]
                        p.filepathdel = value  # Assuming p.filepathdel sets path for deletion (use the full path from value)
                        print(f"Deleted model: {model_path}")
                        print("with key: ", key)
                        self.model_list.Delete(model_path)
                        del self.model_name_not_p[os.path.basename(key)]
                        #del p.loaded_models[os.path.basename(key)]

                        wx.MessageBox(f'The selected item "{model_path}" is getting deleted from model list \n "{self.model_name} \n and model list with models with no path: \n"{self.model_name_not_p}"', 'ERROR',
                                  wx.OK | wx.ICON_INFORMATION)

                        break  # Exit the loop after finding a 
                    except Exception:
                        break
                
            else:
                # Show a message box if the model wasn't found
                wx.MessageBox(f'The selected item "{model_path}" is not in the model list \n "{self.model_name}" models with no path "{self.model_name_not_p} \n and models on controller "{p.loaded_models}"', 'ERROR',
                              wx.OK | wx.ICON_INFORMATION)
                # handle dialog being cancelled or ended by some other button

class TopPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Create a sizer to manage the layout
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetInitialSize((200, 50))
        # Create the compile button
        self.compile_button = wx.Button(self, label="Compile")
        self.compile_button.Bind(wx.EVT_BUTTON, self.on_compile_button)
        
        # Add the compile button to the sizer
        sizer.Add(self.compile_button, 0, wx.ALL, 5)

        self.save_button = wx.Button(self, label="save new project")
        self.save_button.Bind(wx.EVT_BUTTON, self.on_save_button)
        
        # Add the compile button to the sizer
        sizer.Add(self.save_button, 0, wx.ALL, 5)
        
        # Set the sizer for the panel
        self.SetSizer(sizer)
        
        # Set the initial size of the panel
        
    

    
    def remove_last_six_digits(self, filename):
        """Removes the last 6 digits from a filename, preserving the extension.

        Args:
            filename: The filename to modify.

        Returns:
            The modified filename with the last 6 digits removed.
        """
        #base, ext = os.path.splitext(filename)
        # Ensure filename length is at least 7 to avoid index errors
        if len(filename) >= 7:
          return filename[:-6]
        else:
          # Handle cases where filename is less than 7 characters
          return filename
    def on_save_button(self, event):
        global projects_location
        #wildcard = "All files (*.*)|*.*"  # Set a wildcard to allow all file types
        #dialog = wx.DirDialog(self, message="Select a folder", style=wx.DD_DIR_MUST_EXIST)
        #if dialog.ShowModal() == wx.ID_OK:
        #    self.selected_folder = dialog.GetPath()
        #    self.path.SetValue(self.selected_folder)
        #    print("Selected folder:", self.selected_folder)
        #    # Now you can use the selected_folder variable to access the chosen folder
        #dialog.Destroy()
        projects_location = self.selected_folder
    def on_compile_button(self, event):
        global compile_imports
        # Load the scene data
        scene_data = self.load_scene("scene.json")

        # Modify the scene data (add, remove, or update objects)
        for model in p.loaded_models:

            for i in assigned_scripts[model]:
                r, _ = os.path.splitext(os.path.basename(i))
                print()
                #stage one loading imports
                compile_imports += f'''
import {r}\
'''
            
            
                #stage 2 loading classes/functions and base

            print(model)
            
            self.remove_object(scene_data, f'{os.path.basename(model)}')
            self.add_object(scene_data, f'{os.path.basename(model)}', f'{self.remove_last_six_digits(model)}', [3, 0, 0], [0, 0, 0], [1, 1, 1], assigned_scripts[os.path.basename(self.remove_last_six_digits(model))], object_properties[os.path.basename(self.remove_last_six_digits(model))])
        #self.update_object(scene_data, 'cube', position=[1, 2, 3])
        #self.remove_object(scene_data, 'sphere')

        # Save the updated scene data
        compile_imports += f'''
from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
import json

class Game(ShowBase):
    def __init__(self):
        super().__init__() 
'''
        #for r in p.loaded_models:
        compile_imports += f'''
        with open('scene.json', 'r') as file:
            scene_data = json.load(file)

        # Load models based on scene data
        for model_data in scene_data['objects']:
            model_name = model_data['name']
            model_path = model_data['model']
            
            # Load model
            model = self.loader.loadModel(model_path)
            
            # Reparent the model to render
            model.reparentTo(self.render)
        
'''
        for r in p.loaded_models:
            for j in assigned_scripts[r]:
                splitted_module, _ = os.path.splitext(os.path.basename(j))
                compile_imports += f'''
            {splitted_module}.onStart()
            update_function = lambda task: Controller.update(task, model)
            self.taskMgr.add(update_function, '{splitted_module}')
'''
#        for r in p.loaded_models:
#            for j in assigned_scripts[r]:
#                compile_imports += f'''
#    def {r}(self, task):
#
#        return Task.cont
#'''
        compile_imports += f'''

game = Game()
game.run()
'''
        self.save_scene(scene_data, os.path.join(projects_location ,"scene.json"))
        with open(os.path.join(projects_location, 'compiled_game.py'), 'w') as file:
            file.write(compile_imports)
    def load_scene(self, filename):
        try:
            with open(filename, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {"objects": []}  # Return an empty scene if the file doesn't exist

    def save_scene(self, scene_data, filename):
        with open(filename, 'w') as file:
            json.dump(scene_data, file, indent=2)

    def add_object(self, scene_data, name, model, position, rotation, scale, scripts, script_props):
        # Add a new object to the scene data
        new_object = {
            "name": name,
            "model": model,
            "position": position,
            "rotation": rotation,
            "scale": scale,
            "scripts": scripts,
            "script-properties": script_props
        }
        scene_data['objects'].append(new_object)

    def remove_object(self, scene_data, name):
        # Remove an object from the scene data by name
        scene_data['objects'] = [obj for obj in scene_data['objects'] if obj['name'] != name]

    def update_object(self, scene_data, name, **kwargs):
        # Update the properties of an existing object by name
        for obj in scene_data['objects']:
            if obj['name'] == name:
                for key, value in kwargs.items():
                    obj[key] = value
                break

class AddPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        self.list = wx.ListCtrl(self, size=(400, 1050), style=wx.LC_REPORT)

        self.list.InsertColumn(1, "Add to scene", format=wx.LIST_ALIGN_DEFAULT)
        self.list.InsertItem(1, 'Sun light')
        self.list.InsertItem(1, 'Spot light')
        self.list.InsertItem(1, 'Camera')

        self.list.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.on_item_focused)
    def on_item_focused(self, event):
        if event.GetText() == "Sun light":
            p.gfx = "DirectionalLight"
            print("sun")


class Property:
    def __init__(self, name, value, filename):
        self.name = name
        self.value = value
        self.filename = filename

class PropertiesPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        self.panel2 = wx.Panel(self)
        self.SetSize(400, 400)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.SetBackgroundColour(wx.Colour(150, 150, 150))
        #self.panel2.SetBackgroundColour(wx.Colour(150, 150, 150))
        
        self.SetDropTarget(PropertiesDropTarget(self))
        self.button = wx.Button(self, label="Add script or drop on the gray area", name="add script or drop it here")
        self.refresh_button = wx.Button(self, label="Refresh")

        self.sizer.Add(self.button, 0, wx.EXPAND)
        self.sizer.Add(self.refresh_button, 0, wx.EXPAND)
        self.sizer.Add(self.panel2, 1, wx.EXPAND)
        
        self.SetSizer(self.sizer)

        self.refresh_button.Bind(wx.EVT_BUTTON, self.on_refresh_button)

        global selected_object

        self.old_selected_object = selected_object

        self.script = None

        self.vars1 = []

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update, self.timer)
        self.timer.Start(0)
        
        self.SetSizer(self.sizer)
    def on_refresh_button(self, event):
        properties2 = []

        global object_properties
        global assigned_scripts
        global selected_object

        print(assigned_scripts)
        print(selected_object)

        # Ensure each object has its own properties dictionary
        if selected_object not in object_properties:
            object_properties[selected_object] = {'strings': {}, 'integers': {}, 'booleans': {}}

        # Get the object's properties dictionary
        obj_props = object_properties[selected_object]

        # Iterate over each script assigned to the selected object
        for script in assigned_scripts[selected_object]:
            with open(script, 'r') as file:
                tree = ast.parse(file.read())
                for node in tree.body:
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                name = target.id
                                value = eval(compile(ast.Expression(node.value), script, 'eval'))

                                # Check if the property already exists for the object
                                if isinstance(value, str) and name in obj_props['strings']:
                                    value = obj_props['strings'][name]
                                    print("it was str")
                                elif isinstance(value, int) and name in obj_props['integers']:
                                    value = obj_props['integers'][name]
                                    print("it was int")
                                elif isinstance(value, bool) and name in obj_props['booleans']:
                                    value = obj_props['booleans'][name]
                                    print("it was bool")

                                # Add or update the property in the object's properties dictionary
                                #if isinstance(value, str):
                                #    obj_props['strings'][name] = value
                                #elif isinstance(value, int):
                                #    obj_props['integers'][name] = value
                                #elif isinstance(value, bool):
                                #    obj_props['booleans'][name] = value

                                properties2.append(Property(name, value, script))

                                break

        self.update_properties(properties2)

    def update(self, event):
        global selected_object
        global assigned_scripts
        global object_properties
        if selected_object not in object_properties:
            object_properties[selected_object] = {'strings': {}, 'integers': {}, 'booleans': {}}
        obj_props = object_properties[selected_object]
            
        try:
            if selected_object != self.old_selected_object and selected_object in assigned_scripts:
                properties2 = []
                print(assigned_scripts)
                print(selected_object)
                for script in assigned_scripts[selected_object]:
                    with open(script, 'r') as file:
                        tree = ast.parse(file.read())
                        for node in tree.body:
                            if isinstance(node, ast.Assign):
                                for target in node.targets:
                                    
                                    if isinstance(target, ast.Name):
                                        name = target.id
                                        value = eval(compile(ast.Expression(node.value), script, 'eval'))
                                        
                                        if isinstance(value, str) and name in obj_props['strings']:
                                            value = obj_props['strings'][name]
                                            print("it was str")
                                        elif isinstance(value, int) and name in obj_props['integers']:
                                            value = obj_props['integers'][name]
                                            print("it was int")
                                        elif isinstance(value, bool) and name in obj_props['booleans']:
                                            value = obj_props['booleans'][name]
                                            print("it was bool")
                                        
                                        properties2.append(Property(name, value, script))

                                        break

                self.update_properties(properties2)
                self.old_selected_object = selected_object
            elif self.script == None:
                for child in self.GetChildren():
                    if child not in [self.button, self.refresh_button]:
                        child.Destroy()
            else:
                if selected_object != self.old_selected_object and self.script != None:
                    print(assigned_scripts)
                    print(selected_object)
                    
                    with open(self.script, 'r') as file:
                        tree = ast.parse(file.read())
                        for node in tree.body:
                            if isinstance(node, ast.Assign):
                                for target in node.targets:
                                    if isinstance(target, ast.Name):
                                        name = target.id
                                        value = eval(compile(ast.Expression(node.value), self.script, 'eval'))
                                        if isinstance(value, str) and name in obj_props['strings']:
                                            value = obj_props['strings'][name]
                                            print("it was str")
                                        elif isinstance(value, int) and name in obj_props['integers']:
                                            value = obj_props['integers'][name]
                                            print("it was int")
                                        elif isinstance(value, bool) and name in obj_props['booleans']:
                                            value = obj_props['booleans'][name]
                                            print("it was bool")
                                        
                                        properties2.append(Property(name, value, self.script))

                                        break
                    self.old_selected_object = selected_object
        except Exception:
            pass

    def update_properties(self, properties2):
        
        # Clear existing UI elements
        for child in self.GetChildren():
            if child not in [self.button, self.refresh_button]:
                child.Destroy()
        
        #self.SetSizer(self.sizer)
        #button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        #button_sizer.Add(self.button, 0, wx.EXPAND | wx.ALL, 5)
        #button_sizer.Add(self.refresh_button, 0, wx.EXPAND | wx.ALL, 5)


        # Add UI elements for properties
        total_height = 0
        # Add filename label
        filename_labels = {}
        remove_buttons = {}

        for prop in properties2:
            # Add filename label
            
            if prop.filename not in filename_labels:
                filename_labels[prop.filename] = wx.StaticText(self, label=os.path.basename(prop.filename))
                self.sizer.Add(filename_labels[prop.filename], 0, wx.EXPAND | wx.ALL, 5)
                total_height += filename_labels[prop.filename].GetSize().height  # Update total height
                # Add remove button
                remove_button = wx.Button(self, label="Remove")
                remove_buttons[prop.filename] = remove_button
                self.sizer.Add(remove_button, 0, wx.EXPAND | wx.ALL, 5)
                total_height += remove_button.GetSize().height  # Update total height
                remove_button.Bind(wx.EVT_BUTTON, lambda event, filename=prop.filename: self.on_remove_button(event, filename))
            
            # Add property label
            label = wx.StaticText(self, label=prop.name)
            self.sizer.Add(label, 0, wx.EXPAND | wx.ALL, 5)
            total_height += label.GetSize().height  # Update total height
            
            
            if isinstance(prop.value, bool):
                checkbox = wx.CheckBox(self, wx.ID_ANY)
                checkbox.SetValue(prop.value)
                self.sizer.Add(checkbox, 0, wx.EXPAND | wx.ALL, 5)
                total_height += checkbox.GetSize().height  # Update total height
                checkbox.Bind(wx.EVT_CHECKBOX, lambda event, name=prop.name: self.on_checkbox_changed(event, name))
            elif isinstance(prop.value, int):
                slider = wx.TextCtrl(self, wx.ID_ANY, value=str(prop.value))#, minValue=0, maxValue=100)
                self.sizer.Add(slider, 0, wx.EXPAND | wx.ALL, 5)
                total_height += slider.GetSize().height  # Update total height
                slider.Bind(wx.EVT_TEXT, lambda event, name=prop.name: self.on_slider_changed(event, name))
            elif isinstance(prop.value, str):
                text_ctrl = wx.TextCtrl(self, wx.ID_ANY, value=prop.value)
                self.sizer.Add(text_ctrl, 0, wx.EXPAND | wx.ALL, 5)
                total_height += text_ctrl.GetSize().height  # Update total height
                text_ctrl.Bind(wx.EVT_TEXT, lambda event, name=prop.name: self.on_text_changed(event, name))      

        self.Layout()

    def on_checkbox_changed(self, event, name):
        global selected_object
        global object_properties
        checkbox = event.GetEventObject()
        booleans[name] = checkbox.GetValue()
        
        object_properties[selected_object]["booleans"][name] = checkbox.GetValue()
        checkbox.SetValue(object_properties[selected_object]["booleans"][name])
        print(object_properties[selected_object]["booleans"][name])
        checkbox = checkbox.GetValue()
        
        print("Checkbox changed:", checkbox)
        return True  

    def on_slider_changed(self, event, name):
        global selected_object
        global object_properties
        slider = event.GetEventObject()

        integers[name] = slider.GetValue()
        
        object_properties[selected_object]["integers"][name] = slider.GetValue()
        slider.SetValue(str(object_properties[selected_object]["integers"][name]))
        slider = slider.GetValue()
        
        print("Slider changed:", slider)
        return True  

    def on_text_changed(self, event, name):
        global selected_object
        global object_properties
        global strings
        text_ctrl = event.GetEventObject()
        #strings[name] = text_ctrl.GetValue()
        
        object_properties[selected_object]["strings"][name] = text_ctrl.GetValue()
        text_ctrl.SetValue(object_properties[selected_object]["strings"][name])
        
        text_ctrl = text_ctrl.GetValue()

        print("Text changed:", text_ctrl)
        return True
  




class PropertiesDropTarget(wx.FileDropTarget):
    def __init__(self, panel):
        super().__init__()
        self.panel = panel

    def OnDropFiles(self, x, y, filenames):
        # Process dropped files
        properties2 = []
        global properties
        global object_properties
        global selected_object

        # Gather all filenames from assigned_scripts into a single list
        #all_filenames = [filename2 for script_list in assigned_scripts.values() for filename2 in set(script_list)]

        for filename in filenames:
                # Check if filename is already assigned to the selected object
            if filename not in assigned_scripts.get(selected_object, []):
                assign_script(selected_object, filename)
            with open(filename, 'r') as file:
                print("filename: ", filename)
                tree = ast.parse(file.read())
                for node in tree.body:
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                #try:
                                #    if object_properties[selected_object]:
                                #        value = object_properties[selected_object][1]
                                #except Exception:
                                #    pass
                                name = target.id
                                value = eval(compile(ast.Expression(node.value), filename, 'eval'))
                                properties2.append(Property(name, value, filename))
                                properties.script = filename
                                if len(object_properties[selected_object]['strings']) == 0 \
                                and len(object_properties[selected_object]['integers']) == 0 \
                                and len(object_properties[selected_object]['booleans']) == 0:
                                    object_properties[selected_object] = {'strings': {}, 'integers': {}, 'booleans': {}}
                # Check if filename is already in assigned_scripts
                #if filename not in all_filenames:
                 #   assign_script(selected_object, filename)

        self.panel.update_properties(properties2)
        return True
class FileList(wx.Panel):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        self.panel2 = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL) 

        self.current_row = 0
        self.hovered_item = None
        self.files = []

        # Set the FileList panel itself as the drop target
        self.SetDropTarget(MyFileDropTarget(self))
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

        self.SetBackgroundColour(wx.Colour(150, 150, 150))

        self.GetParent().Bind(wx.EVT_LEFT_UP, self.on_panel_click)
        #global properties_target
        #self.SetDropTarget(drag_and_drop_properties.PropertiesDropTarget(self))

    def on_right_click(self, event):
        # Get the position of the mouse pointer when the right-click occurred
        pos = event.GetPosition()
        pos2 = wx.GetMousePosition()
        # Convert the mouse pointer position to the client coordinates of the FileList panel
        client_pos = self.ScreenToClient(pos)
        client_pos2 = self.ScreenToClient(pos2)

        # Find out which panel, if any, was right-clicked
        for child in self.GetChildren():
            panel_pos = child.GetPosition()
            panel_size = child.GetSize()
            if panel_pos[0] <= client_pos[0] <= panel_pos[0] + panel_size[0] and \
               panel_pos[1] <= client_pos[1] <= panel_pos[1] + panel_size[1]:
                # Perform actions for the right-clicked panel
                print("Right-clicked on panel:", child)
                # For example, you can show a context menu here
                self.show_context_menu(child, client_pos2)
                break

    def show_context_menu(self, panel, pos):
        # Create a context menu
        menu = wx.Menu()
        # Add menu items
        item1 = menu.Append(wx.ID_ANY, "create file")
        item2 = menu.Append(wx.ID_ANY, "import file")
        _ , extension = os.path.splitext(panel.file_path) 
        if extension == ".py":
            item3 = menu.Append(wx.ID_ANY, "open in vs code")
            self.selected = panel
            self.Bind(wx.EVT_MENU, self.on_item3_selected, item3)
        # Bind events to menu items
        self.Bind(wx.EVT_MENU, self.on_item1_selected, item1)
        self.Bind(wx.EVT_MENU, self.on_item2_selected, item2)
        # Show the context menu at the specified position
        self.PopupMenu(menu, pos)
        # Destroy the menu when done with it to prevent memory leaks
        menu.Destroy()

    def on_item1_selected(self, event):
        print("Item 1 selected")
        dialog = wx.TextEntryDialog(self, "Enter a file name with its extension:", "Create File", "")
        if dialog.ShowModal() == wx.ID_OK:
            # Get the entered text
            file_name = dialog.GetValue()
            if not file_name == "file" or not file_name == "file.py":
                print("Entered file name:", file_name)
                # Now you can use the entered file name to create a new file
                # For example, you can create an empty file with the entered name
                self.create_file(file_name)
        dialog.Destroy()

    def create_file(self, file_name):
    # Define the template for the Python file content
        filename, _ = os.path.splitext(file_name)
        template = f'''\

def setup(self):
    # Your setup code here
    pass

def update(self, task):
    # Your update code here
    return task.cont
'''

        filename += ".py"
        # Write the template to the new Python file
        file_path = os.path.join(projects_location, filename)
        print(file_name)
        print(file_path)
        with open(file_path, 'w') as file:
            file.write(template)

        print("Created file:", file_name)
        self.update(projects_location)


    def on_item2_selected(self, event):
        print("Item 2 selected")

    def on_item3_selected(self, event):
        file_path = self.selected.file_path
        code_executable = self.find_vscode_executable()
        if code_executable:
            # Open the file in VS Code using the found path to the 'code' executable
            subprocess.run([code_executable, file_path])
        else:
            print("Visual Studio Code not found.")

    def find_vscode_executable(self):
        # Determine the platform
        if sys.platform.startswith('win'):
            return self.find_vscode_executable_windows()
        elif sys.platform.startswith('darwin'):
            return self.find_vscode_executable_mac()
        elif sys.platform.startswith('linux'):
            return self.find_vscode_executable_linux()
        else:
            return None

    def find_vscode_executable_windows(self):
        # Search for Visual Studio Code executable on Windows
        try:
            # Check if 'code.cmd' exists in the default installation directory
            vscode_path = subprocess.check_output(['where', 'code.cmd'], universal_newlines=True).strip()
            return vscode_path
        except subprocess.CalledProcessError:
            return None


    def create_file_panel(self, directory, item, extension, pos):
        panel = wx.Panel(parent=self, size=(32, 100), pos=pos)

        sizer1 = wx.BoxSizer(wx.VERTICAL)
        image_path = os.path.dirname(__file__) + "\h000.png"  # Adjust image paths as needed
        image_py = wx.Image(image_path, wx.BITMAP_TYPE_ANY)
        image_path = os.path.dirname(__file__) + "\h001.png"
        image_info = wx.Image(image_path, wx.BITMAP_TYPE_ANY)
        image_path = os.path.dirname(__file__) + "\h002.png"
        image_folder = wx.Image(image_path, wx.BITMAP_TYPE_ANY)
        image_index = image_py if extension == ".py" else image_info
        if extension == "" or extension == "/" or extension == "\ ":
            image_index = image_folder
        image_bitmap = wx.Bitmap(image_index)
        panel.file_icon = wx.StaticBitmap(panel, wx.ID_ANY, image_bitmap)

        panel.file_text = wx.StaticText(panel, label=item, pos=(0, 40))

        panel.SetSizer(sizer1)

        # Store the full file path in the panel object
        panel.file_path = os.path.join(directory)

        
        panel.Bind(wx.EVT_LEFT_DOWN, self.on_start_drag)

        return panel

    def on_start_drag(self, event):
        self.Bind(wx.EVT_MOTION, self.on_hover)
        item_index = self.files.index(event.GetEventObject())

        data = wx.FileDataObject()
        data.AddFile(os.path.join(self.files[item_index].file_path))  # Access full file path

        dropSource = wx.DropSource(self.hovered_item)
        dropSource.SetData(data)
        res = dropSource.DoDragDrop(flags=wx.Drag_DefaultMove)

        if res != wx.DragMove:
            self.handle_file_move(item_index)

    def on_hover(self, event):
        self.hovered_item = event.GetEventObject()

    def handle_file_move(self, dragged_item_index):
        target_position = self.ScreenToClient(wx.GetMousePosition())
        target_panel = None
        for child in self.sizer.GetChildren():
            if child.GetRect().Contains(target_position):
                target_panel = child
                break

        if not target_panel:
            return

        target_index = self.sizer.GetChildren().index(target_panel)

        if dragged_item_index == target_index:
            pass  # No change in position
        elif dragged_item_index < target_index:
            # Move item up
            self.files.insert(target_index, self.files.pop(dragged_item_index))
            self.sizer.Remove(dragged_item_index)
            self.sizer.Insert(target_index, self.files[target_index])
        else:
            # Move item down
            self.files.insert(target_index + 1, self.files.pop(dragged_item_index))  # Insert after target
            self.sizer.Remove(dragged_item_index)
            self.sizer.Insert(target_index + 1, self.files[target_index + 1])

        # Update layout to reflect changes
        self.Layout()

        # Unbind motion event (no longer hovering)
        self.Unbind(wx.EVT_MOTION)

    def on_panel_click(self, event):
        pos = event.GetPosition()
        # Convert the mouse pointer position to the client coordinates of the FileList panel
        client_pos = self.ScreenToClient(pos)
        for child in self.GetChildren():
            panel_pos = child.GetPosition()
            panel_size = child.GetSize()
            if panel_pos[0] <= client_pos[0] <= panel_pos[0] + panel_size[0] and \
                panel_pos[1] <= client_pos[1] <= panel_pos[1] + panel_size[1]:
                    clicked_panel = child
                    print("Panel clicked:", clicked_panel)

    def update(self, directory_path):
        self.sizer.Clear(True)
        for child in self.sizer.GetChildren():
            child.Unbind(wx.EVT_LEFT_UP)
        pos = (10,0)
        for item in os.listdir(directory_path):
            if os.path.join(directory_path, item):
                f, extension = os.path.splitext(item)
                created_file = self.create_file_panel(os.path.join(directory_path, item), item, extension, pos)
                self.sizer.Add(created_file, flag=wx.EXPAND)  # Add to current row, column 0
                pos = (pos[0] + 42, pos[1])
                if len(self.sizer.GetChildren()) % 19 == 0:
                    pos = (10, pos[1] + 100)  # Move to next row if filled
                self.files.append(created_file)

        self.SetSizer(self.sizer)


class MyFileDropTarget(wx.FileDropTarget):
    def __init__(self, panel):
        wx.FileDropTarget.__init__(self)
        self.panel = panel 

    def OnDropFiles(self, x, y, filenames):
        client_pos = self.panel.ScreenToClient(wx.GetMousePosition())
        print("Mouse Position:", client_pos)

        hovered_panel = None

        for child in self.panel.GetChildren():
            panel_pos = child.GetPosition()
            panel_size = child.GetSize()
            if panel_pos[0] <= client_pos[0] <= panel_pos[0] + panel_size[0] and \
               panel_pos[1] <= client_pos[1] <= panel_pos[1] + panel_size[1]:
                print("got the hovered child")
                hovered_panel = child
                break

        if hovered_panel is None:
            print("No folder hovered over")
            return False

        target_dir = hovered_panel.file_path
        print("File(s) dropped onto directory:", target_dir)
        for filename in filenames:
            if os.path.exists(os.path.join(target_dir, os.path.basename(filename))):
                print("Destination file already exists. File will not be moved.")
                msb = wx.MessageBox(f'''Destination file already exists on path {target_dir}. would you like to override it? {filename}"''', 'ERROR',
                              wx.YES_NO | wx.ICON_INFORMATION)
                if msb == wx.YES:
                    self.override_file(filename, os.path.join(target_dir, os.path.basename(filename)))
                    f.flist.update(target_dir)
                    print("clicked yes")
                else:
                    print("clicked no")
            else:
                # Move the file
                print(os.path.join(target_dir, os.path.basename(filename)))
                os.rename(filename, os.path.join(target_dir, os.path.basename(filename)))
                print("File moved successfully.")
                print(" ", filename)
                f.flist.update(target_dir)
            
        

        return True
    def override_file(self, source_path, destination_path):
        # Open the source file for reading in binary mode
        with open(source_path, 'rb') as source_file:
            # Read the content of the source file
            content = source_file.read()

        # Write the content to the destination file, overwriting its previous content
        with open(destination_path, 'wb') as destination_file:
            destination_file.write(content)



class FileSystem(wx.Panel):
    """A special Panel which holds a Panda3d window."""
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        # Create sizers for layout
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Directory tree control
        self.tree_ctrl = wx.TreeCtrl(self, size=(200, 200))
        root_folder = os.path.expanduser(projects_location)
        self.root = self.tree_ctrl.AddRoot(root_folder)
        self.tree_ctrl.SetItemText(self.root, root_folder)
        sizer.Add(self.tree_ctrl, 1, wx.EXPAND)

        # File list control with an extra column for image
        #self.file_list = wx.ListCtrl(self, wx.ID_ANY, size=(900, 200))
        #self.file_list.InsertColumn(0, 'Model Name', wx.LIST_FORMAT_RIGHT, 150)
        #self.file_list.InsertColumn(1, '', wx.LIST_FORMAT_LEFT, 30)  # Empty column for image
        self.flist = FileList(parent=self, size=(900, 200))
        sizer.Add(self.flist, 2, wx.EXPAND)

        
        
        self.AddFolders(self.tree_ctrl, root_folder)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_tree_selection, self.tree_ctrl)
        self.SetSizer(sizer)

    def onShow(self, event):
        pass

    def AddFolders(self, tree_ctrl, root_dir):
        for item in os.listdir(root_dir):
            item_path = os.path.join(root_dir, item)
            if os.path.isdir(item_path):
                child = tree_ctrl.AppendItem(tree_ctrl.GetRootItem(), item)
                self.AddSubfolders(tree_ctrl, child, item_path)
            else:
                tree_ctrl.AppendItem(tree_ctrl.GetRootItem(), item)

    def AddSubfolders(self, tree_ctrl, parent_item, dir_path):
        try:
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                if os.path.isdir(item_path):
                    child = tree_ctrl.AppendItem(parent_item, item)
                    # Uncomment for recursive subfolders
                    # self.AddSubfolders(tree_ctrl, child, item_path)
                else:
                    tree_ctrl.AppendItem(parent_item, item)
        except Exception:
            pass

    def on_tree_selection(self, event):
        selected_item = event.GetItem()
        selected_path = self.tree_ctrl.GetItemText(selected_item)
        if os.path.isdir(selected_path):
            self.UpdateFileList(selected_path)
        else:
            pass

    def UpdateFileList(self, directory_path):
        self.flist.update(directory_path)

# Function to assign a script to an object
def assign_script(object_name, script_name):
    if object_name in assigned_scripts:
        assigned_scripts[object_name].append(script_name)
    else:
        assigned_scripts[object_name] = [script_name]
    
def main():
    global app
    global frame
    global load, projects_location, p, h, f, properties, top_panel, sizer, sizer2, sizer3, frame, onload
    load = True
    
    
    # Create necessary components for project layout
    #p = PandaViewport(parent=frame)
    notebook = wx.Notebook(frame)

    # Create the first tab with PandaViewport panel
    p = PandaViewport(parent=notebook)
    notebook.AddPage(p, "Viewport")
    # Create the second tab with OtherPanel
    panel22 = AIEditor(parent=notebook)
    notebook.AddPage(panel22, "AI Node Editor")
    h = objectslist(parent=frame)
    f = FileSystem(parent=frame)
    properties = PropertiesPanel(parent=frame)
    top_panel = TopPanel(parent=frame)
    create_panel = AddPanel(parent=frame)
    sizer2 = wx.BoxSizer(wx.VERTICAL)
    sizer3 = wx.BoxSizer(wx.VERTICAL)
    
    sizer3.Add(top_panel, 0, flag=wx.EXPAND)
    #sizer3.Add(p, 1, flag=wx.EXPAND)
    sizer3.Add(notebook, 1, flag=wx.EXPAND)
    sizer3.Add(f, 0, flag=wx.LEFT)  # Optional left shift
    sizer.Add(sizer3, 1, flag=wx.EXPAND)
    sizer2.Add(h, 1, flag=wx.EXPAND)
    sizer2.Add(properties, 1, flag=wx.EXPAND)
    sizer.Add(sizer2, 1, wx.EXPAND)
    sizer.Add(create_panel, 1, flag=wx.EXPAND)
    parent_frame = frame
    parent_frame.SetSizer(sizer)
    parent_frame.Layout()
    parent_frame.Show()
    #wx.CallLater(2000, create_second_frame)  
    #frame = wx.Frame(parent=None, size=wx.Size(1920,1050), pos=(0,0), title="thomas Engine Beta")
    
    
    
    
    
    
    #sizer.Add(onload, 1, wx.EXPAND)
    #del onload


    


    #p = PandaViewport(parent=frame)
    ##t = wx.TextCtrl(parent=frame)
    #h = objectslist(parent=frame)
    #f = FileSystem(parent=frame)
    #properties = PropertiesPanel(parent=frame)
    #top_panel = TopPanel(parent=frame)
    #sizer2 = wx.BoxSizer(wx.VERTICAL)
    #sizer3 = wx.BoxSizer(wx.VERTICAL)
    #sizer3.Add(top_panel, 0, flag=wx.EXPAND)
    #sizer3.Add(p, 1, flag=wx.EXPAND)
    #sizer3.Add(f, 0, flag=wx.LEFT)  # Optional left shift
    ##sizer.Add(t, 0, flag=wx.EXPAND)
    #sizer.Add(sizer3, 1, flag=wx.EXPAND)
    ##sizer.Add(t, 0, flag=wx.EXPAND)
    #sizer2.Add(h, 1, flag=wx.EXPAND)
    #sizer2.Add(properties, 1, flag=wx.EXPAND)
    ##sizer2.Add(f, 1, flag=wx.EXPAND)
    #sizer.Add(sizer2, 1, wx.EXPAND)
    

    #frame.SetSizer(sizer)
    frame.Show()
    app.MainLoop()
def load_scene(filename):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"objects": []}  # Return an empty scene if the file doesn't exist
def save_scene(scene_data, filename):
    with open(filename, 'w') as file:
        json.dump(scene_data, file, indent=2)
def add_object(scene_data, name, model, position, rotation, scale, scripts, script_props):
    # Add a new object to the scene data
    new_object = {
        "name": name,
        "model": model,
        "position": position,
        "rotation": rotation,
        "scale": scale,
        "scripts": scripts,
        "script-properties": script_props
    }
    scene_data['objects'].append(new_object)
def remove_object(scene_data, name):
    # Remove an object from the scene data by name
    scene_data['objects'] = [obj for obj in scene_data['objects'] if obj['name'] != name]
def update_object(scene_data, name, **kwargs):
    # Update the properties of an existing object by name
    for obj in scene_data['objects']:
        if obj['name'] == name:
            for key, value in kwargs.items():
                obj[key] = value
            break
class ProjectDialog(wx.Dialog):
    def __init__(self, parent, title):
        super().__init__(parent, title=title, size=(400, 200))

        self.init_ui()

    def init_ui(self):
        
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        create_checkbox = wx.CheckBox(panel, label='Include Default Scene')
        load_checkbox = wx.CheckBox(panel, label='Include Empty Scene')

        create_button = wx.Button(panel, label='Create')
        load_button = wx.Button(panel, label='Load')

        create_button.Bind(wx.EVT_BUTTON, self.on_create)
        load_button.Bind(wx.EVT_BUTTON, self.on_load)

        sizer.Add(create_checkbox, 0, wx.ALL | wx.EXPAND, 10)
        sizer.Add(load_checkbox, 0, wx.ALL | wx.EXPAND, 10)
        sizer.Add(create_button, 0, wx.ALL | wx.EXPAND, 10)
        sizer.Add(load_button, 0, wx.ALL | wx.EXPAND, 10)

        panel.SetSizer(sizer)

    def on_create(self, event):
        global projects_location
        global p
        wildcard = "All files (*.*)|*.*"  # Set a wildcard to allow all file types
        dialog = wx.DirDialog(frame, message="Select a folder", style=wx.DD_DIR_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_OK:
            projects_location = dialog.GetPath()
            print("Selected folder:", projects_location)
        # Now you can use the selected_folder variable to access the chosen folder
        dialog.Destroy()


        # Handle create project action
        
        # Load the scene data
        scene_data = load_scene("scene.json")

        # Modify the scene data (add, remove, or update objects)
        try:
            for model in p.loaded_models:
                print(model)
            
                remove_object(scene_data, f'{os.path.basename(model)}')
                add_object(scene_data, f'{os.path.basename(model)}', f'{Panda3dApp.remove_last_six_digits(self, model)}', [3, 0, 0], [0, 0, 0], [1, 1, 1], assigned_scripts[os.path.basename(model)], object_properties[os.path.basename(model)])
        except Exception:
            print("its none")
        #self.update_object(scene_data, 'cube', position=[1, 2, 3])
        #self.remove_object(scene_data, 'sphere')

        # Save the updated scene data
        save_scene(scene_data, "scene.json")
        self.EndModal(wx.ID_OK)
    

    def on_load(self, event):
        # Handle load project action

        self.EndModal(wx.ID_CANCEL)
if __name__ == "__main__":
    app = wx.App(redirect=False)
    compile_imports = ""
    onload = None

    selected_object = None
    assigned_scripts = {}
    object_properties = {}

    strings = {}
    integers = {}
    booleans = {}
    vector3 = {}
    vector2 = {}
    selected_object = None
    p = None
    #t = wx.TextCtrl(parent=frame)
    h = None
    f = None
    properties = None
    top_panel = None
    sizer2 = None
    sizer3 = None
    frame = wx.Frame(parent=None, size=wx.Size(1920,1050), pos=(0,0), title="select project")
    frame.Maximize()

    

    projects_location = "C:\\"
    dlg = ProjectDialog(frame, "Project Options")
    result = dlg.ShowModal()
    dlg.Destroy()
    if result == wx.ID_OK:
        print("Create project clicked")
        # Handle create project action
    elif result == wx.ID_CANCEL:
        print("Load project clicked")
        # Handle load project action
    onload = None
    #onload = OnLoadClass(parent=frame)
    #sizer.Add(onload)
    frame.Maximize()
    sizer = wx.FlexGridSizer(3, 3, 5) # two rows, one column
    sizer.AddGrowableRow(0) # make first row growable
    sizer.AddGrowableCol(0) # make first column growable
    sizer.SetFlexibleDirection(wx.BOTH)
    sizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)
    load = True
    loaded = True
    notebook = wx.Notebook(frame)

    # Create the first tab with PandaViewport panel
    '''
    panel1 = PandaViewport(notebook)
    notebook.AddPage(p, "Viewport")
    # Create the second tab with OtherPanel
    panel2 = Animation(notebook)
    notebook.AddPage(panel2, "Anim Node Editor")
    '''
    #wildcard = "All files (*.*)|*.*"  # Set a wildcard to allow all file types
    #dialog = wx.DirDialog(frame, message="Select a folder", style=wx.DD_DIR_MUST_EXIST)
    #if dialog.ShowModal() == wx.ID_OK:
    #    selected_folder = dialog.GetPath()
    #    print("Selected folder:", selected_folder)
    #    # Now you can use the selected_folder variable to access the chosen folder
    #dialog.Destroy()
    #projects_location = selected_folder
    
    #frame = None
    main()
    #frame2.Show()
    frame.Show()
    app.MainLoop()
