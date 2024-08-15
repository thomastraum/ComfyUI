import torch
import os
import node_helpers
from PIL import Image, ImageOps
import numpy as np
from aiohttp import web
from server import PromptServer
import folder_paths
import time
import imghdr

class TT_Save_Pass:
    """
    A node that saves and loads images for different render passes.
    """
    def __init__(self):
        self.render_passes_directory = os.path.join(folder_paths.get_output_directory(), "render_passes")
        self.last_saved_image = None

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "print_to_screen": (["enable", "disable"],),
                "string_field": ("STRING", {
                    "multiline": False,
                    "default": "Hello World!"
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "load_image"
    OUTPUT_NODE = True
    CATEGORY = "TT"

    def get_render_pass_directory(self, pass_name: str) -> str:
        pass_dir = os.path.join(self.render_passes_directory, pass_name)
        os.makedirs(pass_dir, exist_ok=True)
        return pass_dir

    @staticmethod
    def get_image_type(file_content: bytes) -> str:
        image_type = imghdr.what(None, file_content)
        return image_type if image_type else "unknown"

    @classmethod
    def save_image_route(cls):
        @PromptServer.instance.routes.post("/save_image")
        async def save_image(request):
            data = await request.post()
            image = data['uploaded_image']
            render_pass = data.get('image_type', 'unknown')

            image_content = image.file.read()
            image_type = cls.get_image_type(image_content)

            timestamp = int(time.time())
            filename = f"{render_pass}_{timestamp}.{image_type}"

            render_pass_dir = cls().get_render_pass_directory(render_pass)
            filepath = os.path.join(render_pass_dir, filename)

            with open(filepath, 'wb') as f:
                f.write(image_content)

            cls.last_saved_image = filepath

            return web.json_response({"status": "success", "filename": filename, "render_pass": render_pass})

    def load_image(self, print_to_screen, string_field):
        if self.last_saved_image and os.path.exists(self.last_saved_image):
            img = node_helpers.pillow(Image.open, self.last_saved_image)
            
            i = node_helpers.pillow(ImageOps.exif_transpose, img)
            if i.mode == 'I':
                i = i.point(lambda i: i * (1 / 255))
            image = i.convert("RGB")
            
            image = np.array(image).astype(np.float32) / 255.0
            image = torch.from_numpy(image)[None,]
            if 'A' in i.getbands():
                mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                mask = 1. - torch.from_numpy(mask)
            else:
                mask = torch.zeros((64,64), dtype=torch.float32, device="cpu")
            
            if print_to_screen == "enable":
                print(f"""Your input contains:
                    Loaded image: {self.last_saved_image}
                    Render pass: {os.path.basename(os.path.dirname(self.last_saved_image))}
                    String field: {string_field}
                """)

            return (image, mask.unsqueeze(0))
        else:
            blank_image = torch.zeros((1, 3, 64, 64), dtype=torch.float32)
            blank_mask = torch.zeros((1, 64, 64), dtype=torch.float32)
            return (blank_image, blank_mask)

    @classmethod
    def IS_CHANGED(cls, print_to_screen, string_field):
        return cls.last_saved_image

# Register the route
TT_Save_Pass.save_image_route()

# A dictionary that contains all nodes you want to export with their names
NODE_CLASS_MAPPINGS = {
    "TT_Save_Pass": TT_Save_Pass
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "TT_Save_Pass": "TT Save Pass Node"
}