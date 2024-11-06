import bpy
import os, platform, subprocess
#from ping3 import ping, verbose_ping
import urllib.request
import webbrowser
import ssl
import socket
import json
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
version = ""
urlPath = ""

def check(bl_info):
    global version, urlPath
    vs = ''
    version = bl_info["version"]
    for v in version:
        vs += str(v)+'.'
    version = vs[:-1]
    #urlPath = "https://gist.githubusercontent.com/schroef/4010a53b81200748af09b5abb9d24e88/raw/update_quickswitch.json"
    #urlPath = "https://api.github.com/repos/schroef/Extra-Image-List/tags"
    urlPath = "https://api.github.com/repos/schroef/Extra-Image-List/releases"
    #urlPath = 'https://gist.githubusercontent.com/schroef/4010a53b81200748af09b5abb9d24e88/raw/5d552535e7f4f15d4d6494ba450ea88da2eeb756/update_quickswitch.json'


# Pin google
# https://stackoverflow.com/questions/2953462/pinging-servers-in-python
def is_connected():
    hostname = "www.google.com"
    # Option for the number of packets as a function of
    try:
        if socket.gethostbyname(hostname):
            return True
    except:
        return False
#    param = '-n' if platform.system().lower()=='windows' else '-c'

#    # Building the command. Ex: "ping -c 1 google.com"
#    command = ['ping', param, '1', hostname]
#    if subprocess.call(command) == 0:
#        return True
#    else:
#        return False


def get_json_from_remote():
    # Check if we make to much calls
    # https://api.github.com/rate_limit    
    remote_json = "" # We clear it so it doesnt get cached
    request = urllib.request.Request(urlPath)
    try:
        context = ssl._create_unverified_context()
    except:
        # some blender packaged python versions don't have this, largely
        # useful for local network setups otherwise minimal impact
        context = None
    
    if context:
        result = urllib.request.urlopen(request, context=context)
    else:
        result = urllib.request.urlopen(request)
    try:
#        gcontext = ssl.SSLContext()  # Only for gangstars this actually works
#        with urllib.request.urlopen(urlPath, context=gcontext) as response:
#            remote_json = response.read()
        remote_json = result.read()          
    except urllib.request.HTTPError as err:
        print('Could not read tags from server.')
        print(err)
        return None
    tags_json = json.loads(remote_json)
    return tags_json


def check_update_exist():
    tags_json = get_json_from_remote()
    remote_ver_str = tags_json[0]['tag_name'].strip('v.')
    release_notes = tags_json[0]['body']

    installed_ver_float = str_version_to_float(version)
    remote_ver_float = str_version_to_float(remote_ver_str)
    return remote_ver_float > installed_ver_float, remote_ver_str, release_notes

def get_latest_version_url():
    tags_json = get_json_from_remote()
    if len(tags_json) == 0:
        print('remote releases list is empty')
        return None
    zip_url = tags_json[0]['html_url']

    return zip_url

def str_version_to_float(ver_str):
    repi = ver_str.partition('.')
    cc = repi[0]+'.' + repi[2].replace('.', '')
    return float(cc)


class EIS_AddonCheckUpdateExist(bpy.types.Operator):
    bl_idname = "qs.check_for_update"
    bl_label = "Check for update"
    bl_description = "Check for update"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        eis = bpy.context.scene.eis_props
        if not is_connected():
            eis.update_text = 'Make sure you are connected to internet'
            return {'CANCELLED'}
        
        update_exist, remote_ver_str, release_notes = check_update_exist()
        curr_ver_f = str_version_to_float(version)
        rem_ver_f = str_version_to_float(remote_ver_str)

        if update_exist:
            self.report({'INFO'}, f'Found new update: {remote_ver_str}')
            eis.update_text = f'New update: {remote_ver_str}\nRelease notes:\n{release_notes}'
            eis.update_exist = True
            eis.show_getBtn = True
        elif curr_ver_f == rem_ver_f:
            self.report({'INFO'}, 'You have the latest version')
            eis.update_text = f'You have the latest version: {version}\nRelease notes:\n{release_notes}'
            eis.update_exist = False
            eis.show_getBtn = False
        elif curr_ver_f > rem_ver_f:
            self.report({'INFO'}, 'You are ahead of official releases')
            eis.update_text = f'You seem to be ahead of official releases\nYour version: {version}\nremote Version: {remote_ver_str}\nThere is nothing to download'
            eis.update_exist = False
            eis.show_getBtn = False

        return {"FINISHED"}

        
        
class EIS_get_update(bpy.types.Operator):
    """go to the new update"""
    bl_idname="qs.get_update"
    bl_label="Get Update"
    
    def execute(self, context):
        webbrowser.open(get_latest_version_url())   


def updateHide(self,context):
    scn = context.scene
    eis = context.scene.eis_props 
    if self:
        eis.hide_update = True
    else:
        eis.hide_update = False
        eis.update_text = ""


class EIS_props(bpy.types.PropertyGroup):
    update_check_int : IntProperty(name="Update Checker", default=0)
    change_log_int : IntProperty(name="Changelog Checker", default=0)
    update_exist: bpy.props.BoolProperty(name="Update Exist", description="New update avialable",  default=False)
    update_text: bpy.props.StringProperty(name="Update text",  default='', update=updateHide)
    hide_update: bpy.props.BoolProperty(name="Hide Updates",  default=False)
    show_getBtn: bpy.props.BoolProperty(name="Show get button",  default=True)
    

# class EISPanel(bpy.types.Panel):
#     """QuickSwitch panel in properties windows"""
#     bl_label = "QuickSwitch"
#     bl_idname = "EIS_PT_Panel"
#     bl_space_type = 'PROPERTIES'
#     bl_region_type = 'WINDOW'
#     bl_context = "scene"
class EISPreferences(bpy.types.AddonPreferences):
    bl_idname = 'Extra-Image-List'

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        eis = context.scene.eis_props
        
        layout.use_property_split = True
        layout.use_property_decorate = False
        col = layout.column(align=True)
        
        if eis.hide_update:
            iconHide = 'HIDE_ON'
        else:
            iconHide = 'HIDE_OFF'
                        
        
        row = col.row(align=True)
        row.operator(EIS_AddonCheckUpdateExist.bl_idname, text="check for updates", icon="FILE_REFRESH")
        row.prop(eis,"hide_update", text='',icon=iconHide)      
        
        if eis.update_text: # If there's a new Update
            if eis.hide_update:
                layout = layout.box()
                col = layout.column(align=True)
                sub_row = col.row(align=True)
                split_lines_text = eis.update_text.splitlines()
                for line in split_lines_text:
                    sub_row = col.row(align=True)
                    sub_row.label(text=line)
                if eis.show_getBtn:
                    layout = self.layout
                    col = layout.column(align=True)
                    col.operator(EIS_get_update.bl_idname, icon="URL")
                    

classes = [
    EISPreferences,
    EIS_props,
    EIS_AddonCheckUpdateExist,
    EIS_get_update,
]
        
def register():
    
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.eis_props = PointerProperty(type = EIS_props)
    


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.eis_props


if __name__ == "__main__":
    register()

    # test call
#    bpy.ops.object.update_checker()

