#-------------------------------------------------------------------------------
#                    Extra Image List - Addon for Blender
#
# - Two display options (preview and plain list)
# - Button to clear all users for the selected image datablock
# - Double click on image in Node Editor opens the image in UV/Image Editor
#
# Version: 0.2
# Revised: 30.05.2017
# Author: Miki (meshlogic)
#-------------------------------------------------------------------------------

#######################################################

'''
# Extra Image List ######

# Changelog

## [0.2.9] - 2024-11-12

### Removed

- Updater, thing about Blenders Extension Platform, easier method perhaps

### Fixed

- poll issue with nodes light object > use different approach to get active node vs material

## [0.2.8] - 2024-11-05

### Fixed

- Poll isseu texture preview > update nested image texture nodegroup
- Update not working for neste image texture > nodegroup

### Changed

-Shortcut double Right Click to preview texture UV Editor > Double Left click

## 0.2.7] - 2022-05-16

### Fixed

- Poll isseu texture preview > #295

## [0.2.6] - 2021-11-01

### Fixed

- Poll isseu texture preview

## [0.2.5] - 2021-07-29

### Fixed

- Panel issue difference 2.83 and 290

## [0.2.4] - 2021-04-06 

### Added

- Node textore node update btn
- Simple updater check
- Show/hide info > cleaner panel

### Updated

- Panel design to 2.8 with sup-panels
- Default rows & cols

### Fixed

- List view updating with arrow buttons

## [0.2.3] - 2019-11-01 

### Fixed

- Got 2.80 working

#  
# Todo
#
# V Fix left right not adjust list view IDX
#######################################################
'''


bl_info = {
    "name": "Extra Image List",
    "author": "Miki (meshlogic) - Rombout Versluijs (updated panel)",
    "category": "UV",
    "description": "An alternative image list for UV/Image Editor.",
    "location": "UV/Image Editor > Tools > Image List",
    "version": (0, 2, 9),
    "blender": (2, 80, 0),
    "wiki_url": "https://github.com/schroef/Extra-Image-List",
    "tracker_url": "https://github.com/schroef/Extra-Image-List/issues",
}

import bpy
import os
from bpy.props import *

from bpy.types import (
    Panel, 
    AddonPreferences, 
    Menu, 
    Operator, 
    Scene, 
    UIList, 
    PropertyGroup
    )
from bpy.props import (
    EnumProperty, 
    StringProperty, 
    BoolProperty, 
    IntProperty, 
    PointerProperty
    )
from bpy.app.handlers import persistent
#-------------------------------------------------------------------------------
# UI PANEL - Extra Image List
#-------------------------------------------------------------------------------
class EIL_PT_ImageListPanel(Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Image List"
    bl_label = "Extra Image List"

    def draw(self, context):
        layout = self.layout
        cs = context.scene
        props = cs.extra_image_list

        #--- Get the current image in the UV editor and list of all images
        img = context.space_data.image
        img_list = bpy.data.images

        layout = self.layout
        #-----------------------------------------------------------------------
        # PREVIEW List Style
        #-----------------------------------------------------------------------
        if props.style == 'PREVIEW':
            #--- Image preview list
            layout.template_ID_preview(
                context.space_data, "image",
                new = "image.new",
                open = "image.open",
                rows = props.rows, cols = props.cols
            )

        #-----------------------------------------------------------------------
        # LIST Style
        #-----------------------------------------------------------------------
        elif props.style == 'LIST':
            layout.row()
            layout.template_list(
                "EIL_UL_ImageList", "",
                bpy.data, "images",
                props, "image_id",
                #rows = len(bpy.data.images)
            )

        #-----------------------------------------------------------------------
        # Image Source
        #-----------------------------------------------------------------------
        if img != None:
            if props.info:
                #--- Image source
                row = layout.row()
                row.prop(img, "source")
                #row.label(text="Image Source:", icon='DISK_DRIVE')
                row = layout.row(align=True)

                if img.source == 'FILE':
                    if img.packed_file:
                        row.operator("image.unpack", text="", icon='PACKAGE')
                    else:
                        row.operator("image.pack", text="", icon='UGLYPACKAGE')

                    row.prop(img, "filepath", text="")
                    row.operator("image.reload", text="", icon='FILE_REFRESH')
                else:
                    row.label(text=img.source + " : " + img.type)

                #--- Image size
                col = layout.column(align=True)
                row = layout.row(align=True)
                row.alignment = 'LEFT'

                if img.has_data:
                    filename = os.path.basename(img.filepath)
                    #--- Image name
                    col.label(text=filename, icon='FILE_IMAGE')
                    #--- Image size
                    row.label(text="Size:", icon='TEXTURE')
                    row.label(text="%d x %d x %db" % (img.size[0], img.size[1], img.depth))
                else:
                    row.label(text="Can't load image file!", icon='ERROR')

        row = layout.row()
        split = row.split(factor=0.5)
        #--- Navigation button PREV
        sub = split.column(align=True)
        sub.scale_y = 1.5
        sub.operator("extra_image_list.nav", text="", icon='BACK').direction = 'PREV'

        # Disable button for the first image or for no images
        sub.enabled = (img!=img_list[0] if (img!=None and len(img_list)>0) else False)

        #--- Navigation button NEXT
        sub = split.column(align=True)
        sub.scale_y = 1.5
        sub.operator("extra_image_list.nav", text="", icon='FORWARD').direction = 'NEXT'
        
        row = layout.row()
        row.operator("extra_image_list.update_node", icon='NODE_TEXTURE')

        # Disable button for the last image or for no images
        sub.enabled = (img!=img_list[-1] if (img!=None and len(img_list)>0) else False)

#-------------------------------------------------------------------------------
# OPTIONS SUB-PANEL
#-------------------------------------------------------------------------------
# Expand Background Sub-panel
class EIL_PT_ImageListPanel_Options(Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Image List"
    bl_label = "Options"
    bl_parent_id = "EIL_PT_ImageListPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        cs = context.scene
        props = cs.extra_image_list

        layout.use_property_split = True
        layout.use_property_decorate = False

        #-----------------------------------------------------------------------
        # SETTINGS
        #-----------------------------------------------------------------------
        layout.prop(props, "info")
        #--- List style buttons
        #--- Num. of rows & cols for image preview list
        if (bpy.app.version[1] < 90):
            column = layout.column(align=True)
            column.label(text="Preview Style")
        else:		
            column = layout.column(heading="Preview Style:", align=True)
        column.prop(props, "style") #,expand=True
        if props.style =='PREVIEW':
            column.prop(props, "rows")
            column.prop(props, "cols")

        layout.use_property_split = True
        if (bpy.app.version[1] < 90):
            op = layout.column(align=True)
            op.label(text="Clean")
        else:
            op = layout.column(heading="Clean", align=True)
        op.prop(props,"clean_enabled", text="Blend File")

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align=False)
        flow.active = props.clean_enabled
        flow.enabled = props.clean_enabled
        flow.prop(props, "clear_mode", text="")
        flow.operator("extra_image_list.clear", text="Clear", icon='ERROR')


#-------------------------------------------------------------------------------
# CUSTOM TEMPLATE_LIST FOR IMAGES
#-------------------------------------------------------------------------------
class EIL_UL_ImageList(UIList):
    bl_idname = "EIL_UL_ImageList"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        ##NEW BL280
        # 'DEFAULT' and 'COMPACT' layout types should usually use the same draw code.
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            pass
        # 'GRID' layout type should be as compact as possible (typically a single icon!).
        elif self.layout_type in {'GRID'}:
            pass

        # Image name and icon
        row = layout.row(align=True)
        if data == None:
            row.prop(item, "name", text="", emboss=False, icon_value=custom_icons["image_empty"].icon_id)
        row.prop(item, "name", text="", emboss=False, icon_value=icon)

        # Image status (fake user, zero users, packed file)
        row = row.row(align=True)
        row.alignment = 'RIGHT'

        # if item.use_fake_user:
        #     row.label(text="F")
        # else:
        # Allows user to edit it from listview
        row.prop(item, "use_fake_user", text="", emboss=False)
        if item.users == 0:
            row.label(text="0")

        if item.packed_file:
            #row.label(icon='PACKAGE')
            row.operator("image.unpack", text="", icon='PACKAGE', emboss=False)


#--- Update the active image when you select another item in the template_list
def update_active_image(self, context):
    try:
        id = bpy.context.scene.extra_image_list.image_id

        if id < len(bpy.data.images):
            img = bpy.data.images[id]
            bpy.context.space_data.image = img
    except:
        pass

#-------------------------------------------------------------------------------
# UPDATE NODE IMAGE
#-------------------------------------------------------------------------------
class EIL_OT_UpdateNode(Operator):
    bl_idname = "extra_image_list.update_node"
    bl_label = "Update Texture Node"
    bl_description = "Updates the active Texture Node"

    @classmethod
    def poll(cls, context):
        aNode = None
        # print(bpy.context.active_object.active_material)
        # print(bpy.context.active_object.active_material.node_tree.nodes.active)
        # return context.active_node and context.active_node.type == 'TEX_IMAGE' 
        # source: https://blender.stackexchange.com/a/68351/7631
        # return context.scene.node_tree.nodes.active and context.scene.node_tree.nodes.active.type == 'TEX_IMAGE' 
        # return context.active_object.active_material.node_tree.nodes.active is not None
        # return context.active_node is not None
        # actN = context.active_node
        if bpy.context.active_object.type == 'LIGHT':
            ntree = bpy.context.active_object.data.id_data.node_tree
            aNode = ntree.nodes.active 
        else:
            if bpy.context.active_object.active_material:
                aNode = bpy.context.active_object.active_material.node_tree.nodes.active
        if aNode!=None:
            if aNode.type=='GROUP':
                aNode = aNode.node_tree.nodes.active
        else: 
            return False
        return aNode.type == 'TEX_IMAGE' and aNode != None #and bpy.context.active_object.active_material.node_tree.nodes

    def execute(self, context):
        aNode = None
        # Get active node
        if bpy.context.active_object.type == 'LIGHT':
            ntree = bpy.context.active_object.data.id_data.node_tree
            aNode = ntree.nodes.active 
        else:
            if bpy.context.active_object.active_material:
                aNode = bpy.context.active_object.active_material.node_tree.nodes.active
        
        # print(aNode.type)
        # aNode = context.active_object.active_material.node_tree.nodes.active
        if aNode!=None:
            if aNode.type=='GROUP':
                aNode = aNode.node_tree.nodes.active

        # Get list of all images
        img_list = list(bpy.data.images)

        # Get index of the current image in UV editor, return if there is none image
        img = context.space_data.image
        if img in img_list:
            id = img_list.index(img)
        else:
            return{'FINISHED'}
        
        # if id:
        if aNode:
            if aNode.type == 'TEX_IMAGE':
                aNode.image = img_list[id]
                # aNode.image = bpy.data.images[id]

        return{'FINISHED'}

#-------------------------------------------------------------------------------
# IMAGE NAVIGATION OPERATOR
#-------------------------------------------------------------------------------
class EIL_OT_Nav(Operator):
    bl_idname = "extra_image_list.nav"
    bl_label = "Nav"
    bl_description = "Navigation button"

    direction : EnumProperty(
        items = [
            ('NEXT', "PREV", "PREV"),
            ('PREV', "PREV", "PREV")
        ],
        name = "direction",
        default = 'NEXT')

    def execute(self, context):
        # Get list of all images
        img_list = list(bpy.data.images)

        # Get index of the current image in UV editor, return if there is none image
        img = context.space_data.image
        if img in img_list:
            id = img_list.index(img)
        else:
            return{'FINISHED'}

        # Navigate
        if self.direction == 'NEXT':
            if id+1 < len(img_list):
                context.space_data.image = img_list[id+1]

        if self.direction == 'PREV':
            if id > 0:
                context.space_data.image = img_list[id-1]

        return{'FINISHED'}


#-------------------------------------------------------------------------------
# CLEAR IMAGE USERS OPERATOR
#-------------------------------------------------------------------------------
BAKE_TYPES = ('COMBINED', 'AO', 'SHADOW', 'NORMAL', 'UV', 'EMIT', 'ENVIRONMENT',
            'DIFFUSE', 'GLOSSY', 'TRANSMISSION', 'SUBSURFACE', 'GRID',
            'FULL', 'NORMALS', 'TEXTURE', 'DISPLACEMENT', 'DERIVATIVE', 'VERTEX_COLORS', 'EMIT',
            'ALPHA', 'MIRROR_INTENSITY', 'MIRROR_COLOR', 'SPEC_INTENSITY', 'SPEC_COLOR')

class EIL_OT_Clear(Operator):
    bl_idname = "extra_image_list.clear"
    bl_label = "Clear Users"
    bl_description = """Use with caution !!\nClear all users for selected image datablocks.\nSo the image datablock can disappear after save and reload of the blend file."""

    def execute(self, context):
        cs = context.scene
        props = cs.extra_image_list

        #--- SELECTED IMAGE ----------------------------------------------------
        if props.clear_mode == 'SELECTED':

            # Get image in the editor
            img = context.space_data.image
            if img != None:
                img.user_clear()

        #--- NO USERS ----------------------------------------------------
        if props.clear_mode == 'NO USERS':

            for img in bpy.data.images:
                if img.users == 0:
                    bpy.data.images.remove(img)

        #--- INVALID IMAGES ----------------------------------------------------
        elif props.clear_mode == 'INVALID':

            for img in bpy.data.images:

                # Load image in the editor
                context.space_data.image = img
                try:
                    img.update()
                except:
                    pass

                # Clear if loaded image has no data
                if img.has_data == False:
                    img.user_clear()

        #--- GENERATED IMAGES --------------------------------------------------
        elif props.clear_mode == 'GENERATED':

            for img in bpy.data.images:
                if img.source == 'GENERATED':
                    img.user_clear()

        #--- BAKED IMAGES ------------------------------------------------------
        elif props.clear_mode == 'BAKED':

            # Seek for images ending with "_baketype"
            bake_types = tuple(["_"+s for s in BAKE_TYPES])

            for img in bpy.data.images:

                # Get image name without extension
                name = img.name.upper()
                if len(name.split(".")[-1]) <= 3:
                    name = name.rsplit(".", 1)[0]

                # Clear if name ends with a bake type
                if name.endswith(bake_types):
                    img.user_clear()

        #--- ALL IMAGES --------------------------------------------------------
        elif props.clear_mode == 'ALL':
            for img in bpy.data.images:
                if img != None:
                    img.user_clear()

        return{'FINISHED'}


#-------------------------------------------------------------------------------
# SHOW NODE IMAGE OPERATOR
# - Show node image in the IMAGE_EDITOR after double click on the node
#-------------------------------------------------------------------------------
IMG_NODES = ("ShaderNodeTexImage", "ShaderNodeTexEnvironment")

class EIL_OT_ShowNodeImage(Operator):
    bl_idname = "node.show_image"
    bl_label = "Show node image in the UV/Image Editor"

    def execute(self, context):
        node = context.active_node

        #--- Test if the active node is image type
        if node and node.bl_idname in IMG_NODES:

            # Find IMAGE_EDITOR
            for area in bpy.context.screen.areas:
                if area.type == 'IMAGE_EDITOR':
                    space = area.spaces.active

                    # Show image in IMAGE_EDITOR
                    if node.image:
                        space.image = node.image

        return {"FINISHED"}


#-------------------------------------------------------------------------------
# CUSTOM HANDLER (scene_update_post) #NEW name bl 2.80 depsgraph_update_post
# - This handler is invoked after the scene updates
# - Keeps template_list synced with the active image
#-------------------------------------------------------------------------------
@persistent
def update_image_list(context):
    # try:
    props = bpy.context.scene.extra_image_list

    # Try to find the active image in the IMAGE_EDITOR
    img = None
    for area in bpy.context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            img = area.spaces.active.image
            break

    # Update selected item in the template_list
    if img != None:
        id = bpy.data.images.find(img.name)
        # if id != -1 and id != props.image_id:
        props.image_id = id
    # except:
    # 	pass


#-------------------------------------------------------------------------------
# CUSTOM SCENE PROPS
#-------------------------------------------------------------------------------
class ExtraImageList_Props(PropertyGroup):

    style : EnumProperty(
        items = [
            ('PREVIEW', "Preview", "", 0),
            ('LIST', "List", "", 1),
        ],
        default = 'PREVIEW',
        name = "Style",
        description = "Image list style")

    clean_enabled : BoolProperty(
            default=False,
            name="Clean:",
            description="Enables option to clear scene of image textures. Be careful!")

    clear_mode : EnumProperty(
        items = [
            ('NO USERS', "No Users", "Clears all images with no users", 0),
            ('SELECTED', "Selected Image", "Clear the image selected in the editor", 1),
            ('INVALID', "Invalid Images", "Clear invalid images (has_data == False)", 2),
            ('GENERATED', "Generated Images", "Clear generated images (source == 'GENERATED')", 3),
            ('BAKED', "Baked Images", "Clear images ending with a bake type e.g. '_COMBINED'", 4),
            ('ALL', "All Images", "Clear all images", 4),
        ],
        default = 'NO USERS',
        name = "Image Selection",
        description = "Select images to be cleared")

    rows : IntProperty(
        name = "Rows",
        description = "Num. of rows in the preview list",
        default = 4, min = 1, max = 15)

    cols : IntProperty(
        name = "Cols",
        description = "Num. of columns in the preview list",
        default = 6, min = 1, max = 30)

    # Index of the active image in the template_list
    image_id : IntProperty(
        name = "Image ID",
        default = 0,
        update = update_active_image)

    options : BoolProperty(
        name="Options",
        default=False)

    info : BoolProperty(
        name="Show Info",
        default=False)

    settings : BoolProperty(
        name="Settings",
        default=False)

def icon_Load():
    # importing icons
    import bpy.utils.previews
    global custom_icons
    custom_icons = bpy.utils.previews.new()

    # path to the folder where the icon is
    # the path is calculated relative to this py file inside the addon folder
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")

    # load a preview thumbnail of a file and store in the previews collection
    custom_icons.load("empty", os.path.join(icons_dir, "empty_image_128x.png"), 'IMAGE')

# global variable to store icons in
custom_icons = None

#-------------------------------------------------------------------------------
# REGISTER/UNREGISTER ADDON CLASSES
#-------------------------------------------------------------------------------
keymaps = []

#Classes for register and unregister
classes = (
    EIL_PT_ImageListPanel,
    EIL_PT_ImageListPanel_Options,
    EIL_UL_ImageList,
    EIL_OT_ShowNodeImage,
    ##NW bl280 PropertyGroup Needs to be added now?
    ExtraImageList_Props,
    EIL_OT_Clear,
    EIL_OT_UpdateNode,
    EIL_OT_Nav,
    )

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.extra_image_list = PointerProperty(type=ExtraImageList_Props)
    bpy.app.handlers.depsgraph_update_post.append(update_image_list)


    # Add custom shortcut (image node double click)
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name="Node Editor", space_type='NODE_EDITOR')
    kmi = km.keymap_items.new("node.show_image", 'LEFTMOUSE', 'DOUBLE_CLICK')
    keymaps.append((km, kmi))
    icon_Load()

def unregister():
    global custom_icons
    bpy.utils.previews.remove(custom_icons)

    del bpy.types.Scene.extra_image_list
    bpy.app.handlers.depsgraph_update_post.remove(update_image_list)

    # Remove custom shortcuts
    for km, kmi in keymaps:
        km.keymap_items.remove(kmi)
    keymaps.clear()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

