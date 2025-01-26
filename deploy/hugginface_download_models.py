import os
from pathlib import Path
from huggingface_hub import hf_hub_download
import subprocess

# Enable faster downloads with hf_transfer
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

# Base paths
COMFY_PATH = Path("./models")
CLIP_VISION_PATH = COMFY_PATH / "clip_vision"
IPADAPTER_PATH = COMFY_PATH / "ipadapter"

# Create required directories
CLIP_VISION_PATH.mkdir(parents=True, exist_ok=True)
IPADAPTER_PATH.mkdir(parents=True, exist_ok=True)

# Dictionary mapping of target filenames to their HF repo sources
CLIP_VISION_MODELS = {
    "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors": {
        "repo_id": "h94/IP-Adapter",
        "filename": "models/image_encoder/model.safetensors",
    },
    "CLIP-ViT-bigG-14-laion2B-39B-b160k.safetensors": {
        "repo_id": "h94/IP-Adapter",
        "filename": "sdxl_models/image_encoder/model.safetensors",
    },
    "clip-vit-large-patch14-336.bin": {
        "repo_id": "Kwai-Kolors/Kolors-IP-Adapter-Plus",
        "filename": "image_encoder/pytorch_model.bin",
    },
}

IPADAPTER_MODELS = {
    "ip-adapter_sd15.safetensors": {
        "repo_id": "h94/IP-Adapter",
        "filename": "models/ip-adapter_sd15.safetensors",
    },
    "ip-adapter_sd15_light_v11.bin": {
        "repo_id": "h94/IP-Adapter",
        "filename": "models/ip-adapter_sd15_light_v11.bin",
    },
    "ip-adapter-plus_sd15.safetensors": {
        "repo_id": "h94/IP-Adapter",
        "filename": "models/ip-adapter-plus_sd15.safetensors",
    },
    "ip-adapter-plus-face_sd15.safetensors": {
        "repo_id": "h94/IP-Adapter",
        "filename": "models/ip-adapter-plus-face_sd15.safetensors",
    },
    "ip-adapter-full-face_sd15.safetensors": {
        "repo_id": "h94/IP-Adapter",
        "filename": "models/ip-adapter-full-face_sd15.safetensors",
    },
    "ip-adapter_sd15_vit-G.safetensors": {
        "repo_id": "h94/IP-Adapter",
        "filename": "models/ip-adapter_sd15_vit-G.safetensors",
    },
    "ip-adapter_sdxl_vit-h.safetensors": {
        "repo_id": "h94/IP-Adapter",
        "filename": "sdxl_models/ip-adapter_sdxl_vit-h.safetensors",
    },
    "ip-adapter-plus_sdxl_vit-h.safetensors": {
        "repo_id": "h94/IP-Adapter",
        "filename": "sdxl_models/ip-adapter-plus_sdxl_vit-h.safetensors",
    },
    "ip-adapter-plus-face_sdxl_vit-h.safetensors": {
        "repo_id": "h94/IP-Adapter",
        "filename": "sdxl_models/ip-adapter-plus-face_sdxl_vit-h.safetensors",
    },
    "ip-adapter_sdxl.safetensors": {
        "repo_id": "h94/IP-Adapter",
        "filename": "sdxl_models/ip-adapter_sdxl.safetensors",
    },
}


def download_models(models_dict: dict, target_dir: Path):
    """Download models from Hugging Face and save to target directory."""
    for target_filename, source in models_dict.items():
        print(f"Downloading {target_filename}...")
        try:
            downloaded_path = hf_hub_download(
                repo_id=source["repo_id"],
                filename=source["filename"],
            )
            # Create symlink to the downloaded file
            target_path = target_dir / target_filename
            if target_path.exists():
                target_path.unlink()
            target_path.symlink_to(downloaded_path)
            print(f"Successfully downloaded and linked {target_filename}")
        except Exception as e:
            print(f"Error downloading {target_filename}: {str(e)}")


def main():
    print("Downloading CLIP Vision models...")
    download_models(CLIP_VISION_MODELS, CLIP_VISION_PATH)

    print("\nDownloading IP-Adapter models...")
    download_models(IPADAPTER_MODELS, IPADAPTER_PATH)


if __name__ == "__main__":
    main()
