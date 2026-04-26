from gradio_client import Client, handle_file
import os
import time
from typing import Optional
from app.config import settings

# CRITICAL: Set HF_TOKEN as environment variable so gradio_client
# can use it for ZeroGPU authentication automatically.
# The gradio_client library checks os.environ["HF_TOKEN"] internally.
if settings.hf_token:
    os.environ["HF_TOKEN"] = settings.hf_token
    print(f"[AUTH] HF_TOKEN env var set (starts with: {settings.hf_token[:10]}...)")
else:
    print("[AUTH] WARNING: No HF_TOKEN configured! ZeroGPU spaces will reject requests.")

class QuotaExceededError(Exception):
    """Custom exception raised when Hugging Face ZeroGPU quota is exceeded."""
    pass

class ServerOverloadedError(Exception):
    """Custom exception raised when external HF Space is overloaded or unreachable."""
    pass

class HFClient:
    def __init__(self, space_id: str = None):
        self.space_id = space_id or settings.vton_space_id
        self.token = settings.hf_token if settings.hf_token else None
        try:
            self.client = Client(self.space_id, token=self.token)
            print(f"[AUTH] HF Client connected to {self.space_id} (authenticated: {bool(self.token)})")
        except Exception as e:
            print(f"Failed to initialize HF Client for {self.space_id}: {e}")
            self.client = None

    def execute_try_on(self, 
                       human_img_path: str, 
                       garm_img_path: str, 
                       garment_desc: str,
                       is_checked: bool,
                       is_checked_crop: bool,
                       denoise_steps: int,
                       seed: int,
                       mask_path: str = None) -> Optional[str]:
        """
        Executes the try-on using the gradio client.
        The parameters here correspond to IDM-VTON space parameters.
        """
        if not self.client:
            print("Attempting to initialize Gradio Client lazily...")
            try:
                self.client = Client(self.space_id, token=self.token)
            except Exception as e:
                raise Exception(f"Failed to connect to Hugging Face space {self.space_id}: {e}")

        max_retries = 5
        for attempt in range(max_retries):
            try:
                # Build the image dict for IDM-VTON
                # If a mask_path is provided, include it as a layer
                layers = []
                if mask_path:
                    layers = [handle_file(mask_path)]
                
                result = self.client.predict(
                    dict({"background": handle_file(human_img_path), "layers": layers, "composite": None}),
                    handle_file(garm_img_path),
                    garment_desc,
                    is_checked,
                    is_checked_crop,
                    denoise_steps,
                    seed,
                    api_name="/tryon"
                )
                # result is usually a tuple where [0] is the result image path
                if isinstance(result, tuple) or isinstance(result, list):
                    return result[0]
                return result
            except Exception as e:
                err_str = str(e).lower()
                print(f"HF inference attempt {attempt + 1} failed: {e}")
                
                # Check for common temporary server issues
                is_timeout = "timed out" in err_str or "ssl" in err_str
                is_overloaded = "no gpu" in err_str or "retry later" in err_str
                
                if is_timeout or is_overloaded:
                    if attempt < max_retries - 1:
                        sleep_time = 15 * (attempt + 1)
                        print(f"Retrying in {sleep_time}s due to external server load/timeout...")
                        time.sleep(sleep_time)
                        continue
                # If we exhausted retries or it's a different error
                if "daily zerogpu quotas" in err_str or "rate limit" in err_str:
                    raise QuotaExceededError("Hugging Face daily ZeroGPU quota exceeded. Please wait for reset or upgrade your HF account.")
                
                if is_timeout or is_overloaded:
                    raise ServerOverloadedError("Hugging Face servers are currently very busy or timed out. Please try again in a few minutes.")

                raise Exception(f"HF Space Error -> {e}. The public space might be overloaded, try again later or use a private endpoint.")

hf_vton_client = HFClient()
