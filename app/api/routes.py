from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from app.models.schemas import TryOnResponse, Category, ErrorResponse
from app.services.image_utils import process_image, cleanup_files
from app.pipelines.factory import PipelineFactory
from app.services.hf_client import QuotaExceededError, ServerOverloadedError
import uuid
import os
import shutil

router = APIRouter()

@router.post(
    "/try-on",
    response_model=TryOnResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Virtual Try-On Endpoint",
    description="Upload user image and garment image, and specify a category to get the synthesized realistic try-on result."
)
async def generate_try_on(
    background_tasks: BackgroundTasks,
    user_image: UploadFile = File(..., description="Full-body or frontal human image"),
    garment_image: UploadFile = File(..., description="Catalog-style garment image"),
    category: Category = Form(..., description="Garment category for pipeline routing"),
):
    # Validate content types (simple check)
    if not (user_image.content_type.startswith("image/") and garment_image.content_type.startswith("image/")):
        raise HTTPException(status_code=400, detail="Uploaded files must be images")

    user_img_path = None
    garm_img_path = None

    try:
        # 1. Process and save uploaded files temporarily
        user_bytes = await user_image.read()
        garm_bytes = await garment_image.read()
        
        user_img_path = process_image(user_bytes)
        garm_img_path = process_image(garm_bytes)

        # 2. Get the correct pipeline based on the category
        pipeline = PipelineFactory.get_pipeline(category)

        # 3. Execute the pipeline
        # Note: In a true async production system without GPU blocking, 
        # this would be sent to a Celery/Redis queue and return a Job ID.
        # Since we are prioritizing standard inference using HF API, we can await it or run in thread.
        # Gradio client prediction is blocking, so we run normally (or via run_in_threadpool).
        
        result_url = pipeline.execute(human_img_path=user_img_path, garm_img_path=garm_img_path)

        # 4. Convert result to base64 to avoid local disk storage
        job_id = uuid.uuid4().hex
        
        if result_url and os.path.exists(result_url):
            import base64
            with open(result_url, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
        else:
            raise Exception("No valid image generated.")

        # 5. Cleanup local files in background
        background_tasks.add_task(cleanup_files, user_img_path, garm_img_path, result_url)

        return TryOnResponse(
            status="success",
            message="Try-On image generated successfully",
            result_image_url=f"data:image/jpeg;base64,{img_b64}", 
            job_id=job_id
        )

    except QuotaExceededError as e:
        cleanup_files(user_img_path, garm_img_path)
        raise HTTPException(status_code=429, detail=str(e))
    except ServerOverloadedError as e:
        cleanup_files(user_img_path, garm_img_path)
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        # Cleanup on failure too
        cleanup_files(user_img_path, garm_img_path)
        raise HTTPException(status_code=500, detail=f"Try-On pipeline failed: {str(e)}")

