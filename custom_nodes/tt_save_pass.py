import torch

import os
import node_helpers
from PIL import Image, ImageOps, ImageSequence, ImageFile

import numpy as np

from aiohttp import web
from server import PromptServer
import folder_paths
import time
import imghdr

import hashlib
import json
import aiohttp

class TT_Save_Pass:


    """
    A example node

    Class methods
    -------------
    INPUT_TYPES (dict): 
        Tell the main program input parameters of nodes.
    IS_CHANGED:
        optional method to control when the node is re executed.

    Attributes
    ----------
    RETURN_TYPES (`tuple`): 
        The type of each element in the output tuple.
    RETURN_NAMES (`tuple`):
        Optional: The name of each output in the output tuple.
    FUNCTION (`str`):
        The name of the entry-point method. For example, if `FUNCTION = "execute"` then it will run Example().execute()
    OUTPUT_NODE ([`bool`]):
        If this node is an output node that outputs a result/image from the graph. The SaveImage node is an example.
        The backend iterates on these output nodes and tries to execute all their parents if their parent graph is properly connected.
        Assumed to be False if not present.
    CATEGORY (`str`):
        The category the node should appear in the UI.
    execute(s) -> tuple || None:
        The entry point method. The name of this method must be the same as the value of property `FUNCTION`.
        For example, if `FUNCTION = "execute"` then this method's name must be `execute`, if `FUNCTION = "foo"` then it must be `foo`.
    """
    RENDER_PASSES_DIRECTORY = os.path.join(folder_paths.get_input_directory(), "render_passes")
    DEFAULT_PASS = "beauty"
    LAST_UPDATE_FILE = os.path.join(RENDER_PASSES_DIRECTORY, "last_update.json")
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        cls.ensure_render_directory()
        input_types = {
            "required": {
                "print_to_screen": (["enable", "disable"],),
                "choose_pass": (["beauty", "depth", "normal"],),
            }
        }

        for pass_name in os.listdir(cls.RENDER_PASSES_DIRECTORY):
            pass_dir = os.path.join(cls.RENDER_PASSES_DIRECTORY, pass_name)
            if os.path.isdir(pass_dir):
                files = [f for f in os.listdir(pass_dir) if os.path.isfile(os.path.join(pass_dir, f))]
                input_types["required"][f"image_{pass_name}"] = (sorted(files), {"image_upload": False})

        return input_types

    @classmethod
    def ensure_render_directory(cls):
        os.makedirs(cls.RENDER_PASSES_DIRECTORY, exist_ok=True)

    @staticmethod
    def get_image_type(file_content: bytes) -> str:
        image_type = imghdr.what(None, file_content)
        return image_type if image_type else "unknown"
    
    @classmethod
    def get_annotated_filepath(cls, name: str, default_pass: str | None = None) -> str:
        name, base_dir = cls.annotated_filepath(name)

        if base_dir is None:
            if default_pass is not None:
                base_dir = os.path.join(cls.RENDER_PASSES_DIRECTORY, default_pass)
            else:
                base_dir = os.path.join(cls.RENDER_PASSES_DIRECTORY, cls.DEFAULT_PASS)

        return os.path.join(base_dir, name)
    
    @classmethod
    def annotated_filepath(cls, name: str) -> tuple[str, str | None]:
        for pass_name in os.listdir(cls.RENDER_PASSES_DIRECTORY):
            if name.endswith(f"[{pass_name}]"):
                base_dir = os.path.join(cls.RENDER_PASSES_DIRECTORY, pass_name)
                name = name[:-len(f"[{pass_name}]")]
                return name, base_dir

        return name, None
    
    @classmethod
    async def get_last_workflow(cls):
        try:
            url = "http://127.0.0.1:8188/history"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    history = await response.json()
                    if history and isinstance(history, dict):
                        # Get the first (most recent) entry
                        last_entry_id, last_entry = next(iter(history.items()))
                        if isinstance(last_entry, dict) and 'prompt' in last_entry:
                            #  third entry in array is the prompt
                            return last_entry['prompt'][2]
                        else:
                            print(f"Invalid structure in the last history item: {last_entry_id}")
                            return None
                    else:
                        print("No valid history found")
                        return None
        except Exception as e:
            print(f"Error fetching last workflow: {str(e)}")
            return None
    
    @classmethod
    def save_image_route(cls):
        @PromptServer.instance.routes.post("/inputs")
        async def save_image(request):
            data = await request.post()
            image = data['uploaded-image']
            render_pass = data.get('image-type', 'unknown')

            # Get the original filename
            print(f"Received filename: {image.filename}")
            original_filename = os.path.basename(image.filename)
            name, ext = os.path.splitext(original_filename)

            image_content = image.file.read()
            image_type = cls.get_image_type(image_content)

            # If no extension, use the detected image type
            if not ext:
                ext = f".{image_type}"

            # render_pass_dir = cls.get_render_pass_directory(render_pass)
            render_pass_dir = os.path.join(cls.RENDER_PASSES_DIRECTORY, render_pass)
            os.makedirs(render_pass_dir, exist_ok=True)
            filepath = os.path.join(render_pass_dir, f"{name}{ext}")

            with open(filepath, 'wb') as f:
                f.write(image_content)

            return web.json_response({
                "status": "success", 
                "filename": f"{name}{ext}", 
                "render_pass": render_pass
            })


    # RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_TYPES = ("IMAGE",)
    OUTPUT_NODE = True
    #RETURN_NAMES = ("image_output_name",)
    FUNCTION = "load_image"
    OUTPUT_NODE = True
    CATEGORY = "TT"

    def load_image(self, image_beauty, image_depth, image_normal, choose_pass, print_to_screen):
        if print_to_screen == "enable":
            print("load_image called----------------------------")
            print(f"Your input contains:")
            print(f"choose_pass: {choose_pass}")

        # Select the appropriate image based on choose_pass
        if choose_pass == "beauty":
            selected_image = image_beauty
        elif choose_pass == "depth":
            selected_image = image_depth
        elif choose_pass == "normal":
            selected_image = image_normal
        else:
            raise ValueError(f"Invalid choose_pass value: {choose_pass}")

        # Load the selected image file and convert it to a tensor
        image_path = self.get_annotated_filepath(selected_image, default_pass=choose_pass)
        img = node_helpers.pillow(Image.open, image_path)
        
        output_images = []
        w, h = None, None

        for i in ImageSequence.Iterator(img):
            i = node_helpers.pillow(ImageOps.exif_transpose, i)

            if i.mode == 'I':
                i = i.point(lambda i: i * (1 / 255))
            image = i.convert("RGB")

            if len(output_images) == 0:
                w = image.size[0]
                h = image.size[1]
            
            if image.size[0] != w or image.size[1] != h:
                continue
            
            image = np.array(image).astype(np.float32) / 255.0
            image = torch.from_numpy(image)[None,]
            output_images.append(image)

        if len(output_images) > 1:
            output_image = torch.cat(output_images, dim=0)
        else:
            output_image = output_images[0]

        return (output_image,)

    
    
    """
        The node will always be re executed if any of the inputs change but
        this method can be used to force the node to execute again even when the inputs don't change.
        You can make this node return a number or a string. This value will be compared to the one returned the last time the node was
        executed, if it is different the node will be executed again.
        This method is used in the core repo for the LoadImage node where they return the image hash as a string, if the image hash
        changes between executions the LoadImage node is executed again.
    """
    #@classmethod
    #def IS_CHANGED(s, image, string_field, int_field, float_field, print_to_screen):
    #    return ""
    @classmethod
    def IS_CHANGED(cls, image_beauty, image_depth, image_normal, choose_pass, print_to_screen):
        print(f"IS_CHANGED called----------------------------------")
        return time.time()
        # image_path = cls.get_annotated_filepath(image)
        # m = hashlib.sha256()
        # with open(image_path, 'rb') as f:
        #     m.update(f.read())
        # return m.digest().hex()








# Set the web directory, any .js file in that directory will be loaded by the frontend as a frontend extension
# WEB_DIRECTORY = "./somejs"


# # Add custom API routes, using router
# from aiohttp import web
# from server import PromptServer
# import folder_paths

# @PromptServer.instance.routes.get("/beauty")
# async def get_hello(request):
    
#     return web.json_response("beauty pass")


# Register the route
TT_Save_Pass.save_image_route()

# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {
    "TT_Save_Pass": TT_Save_Pass
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "TT_Save_Pass": "tt save pass Node"
}