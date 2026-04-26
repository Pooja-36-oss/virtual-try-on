import time
from app.pipelines.base import BasePipeline
from app.services.hf_client import hf_vton_client
from app.services.image_utils import (
    generate_fullbody_mask, 
    generate_lowerbody_mask, 
    preserve_face_and_pose,
    preserve_identity_via_mask
)

# These parameters might need tuning depending on the specific model endpoint.
# We are making intelligent assumptions for OOTDiffusion / IDM-VTON space parameters.

class ShirtPipeline(BasePipeline):
    def execute(self, human_img_path: str, garm_img_path: str):
        # Upper body, standard V-TON
        return hf_vton_client.execute_try_on(
            human_img_path=human_img_path,
            garm_img_path=garm_img_path,
            garment_desc="Upper body shirt, t-shirt, top",
            is_checked=True,
            is_checked_crop=False,
            denoise_steps=30,
            seed=42
        )

class PantPipeline(BasePipeline):
    def execute(self, human_img_path: str, garm_img_path: str):
        # Lower body
        mask_path = generate_lowerbody_mask(human_img_path)
        result_img = hf_vton_client.execute_try_on(
            human_img_path=human_img_path,
            garm_img_path=garm_img_path,
            garment_desc="Lower body pant, trousers, skirt, jeans",
            is_checked=False,
            is_checked_crop=False,
            denoise_steps=30,
            seed=42,
            mask_path=mask_path
        )
        
        # Post-process: Stitch original arms, hands, and face back
        if result_img and mask_path:
            return preserve_identity_via_mask(human_img_path, result_img, mask_path)
        return result_img

class KurtiPipeline(BasePipeline):
    def execute(self, human_img_path: str, garm_img_path: str):
        # Indian wear: Use shorter mask (0.60 bottom) for knee-length kurti to protect hands
        mask_path = generate_fullbody_mask(human_img_path, bottom_ratio=0.60)
        result_img = hf_vton_client.execute_try_on(
            human_img_path=human_img_path,
            garm_img_path=garm_img_path,
            garment_desc="Knee-length Indian kurti tunic outfit, traditional ethnic wear",
            is_checked=False,        
            is_checked_crop=False,
            denoise_steps=35,        # Slightly more steps for accuracy
            seed=42,
            mask_path=mask_path      
        )
        # Post-process: Stitch original face and head back
        if result_img:
            return preserve_face_and_pose(human_img_path, result_img)
        return result_img

class LehengaPipeline(BasePipeline):
    def execute(self, human_img_path: str, garm_img_path: str):
        # Indian wear: Use full-length mask (0.95 bottom) for floor-length lehenga
        mask_path = generate_fullbody_mask(human_img_path, bottom_ratio=0.95)
        result_img = hf_vton_client.execute_try_on(
            human_img_path=human_img_path,
            garm_img_path=garm_img_path,
            garment_desc="Full traditional Indian lehenga choli set, including embroidered top and long flared skirt",
            is_checked=False,        
            is_checked_crop=False,
            denoise_steps=40,        # Higher steps for complex lehenga details
            seed=84,
            mask_path=mask_path      
        )
        # Post-process: Stitch original face and head back
        if result_img:
            return preserve_face_and_pose(human_img_path, result_img)
        return result_img
