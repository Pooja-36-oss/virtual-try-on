# Virtual Try-On (V-TON) Backend - Indian Ethnic Wear Optimized

## 1. System Architecture

This is a production-ready FastAPI backend designed to process user images and garment images for realistic virtual try-on, with special optimizations for Indian ethnic wear (Kurti, Lehenga). 

* **Web Framework**: FastAPI handles HTTP requests, offering high performance, automatic documentation (Swagger UI), and validation via Pydantic.
* **Architecture Pattern**: Strategy Pattern. We route requests to specific AI pipelines based on the uploaded garment category (`shirt`, `pant`, `multi`, `kurti`, `lehenga`).
* **AI Model Integration**: Uses `gradio_client` to interface with Hugging Face Inference Spaces (e.g., IDM-VTON or OOTDiffusion) avoiding the need for heavy local GPU computation unless explicitly desired. The space handles human parsing, pose estimation, and cloth warping.
* **Storage**: Temporarily writes files to the system temporary directory and cleans them up asynchronously via FastAPI `BackgroundTasks` after generation. Results are returned as base64 Data URIs to avoid local disk dependency.

### Folder Structure
```
.
├── app
│   ├── api
│   │   ├── __init__.py
│   │   └── routes.py         # The /api/v1/try-on endpoints
│   ├── models
│   │   ├── __init__.py
│   │   └── schemas.py        # Pydantic schemas and enums
│   ├── pipelines
│   │   ├── __init__.py
│   │   ├── base.py           # Abstract BasePipeline class
│   │   ├── category_pipelines.py  # specific pipelines logic for each garment
│   │   └── factory.py        # PipelineFactory for routing
│   ├── services
│   │   ├── __init__.py
│   │   ├── hf_client.py      # HuggingFace Client Wrapper
│   │   └── image_utils.py    # Image Preprocessing & Cleanup
│   ├── config.py             # Pydantic BaseSettings 
│   └── main.py               # FastAPI App definition
├── requirements.txt          # Python dependencies
├── .env.sample               # Environment variables sample
└── README.md                 # This file
```

---

## 7. Environment Variables
To get started, copy the `.env.sample` to `.env`:
```bash
cp .env.sample .env
```
Ensure you provide a valid `VTON_SPACE_ID` (e.g., `yisol/IDM-VTON` or your private Hugging Face space) and an optional `HF_TOKEN` if using a private endpoint.

---

## 8. Step-by-step Deployment Guide

1. **Clone & Setup Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   pip install -r requirements.txt
   ```

2. **Run Locally**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Production Deployment (Docker/Gunicorn)**
   Use Gunicorn with Uvicorn workers for production scaling:
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```
   *Note: Ensure to mount a volume or integrate an S3 bucket if you plan to persist generated images, as current implementation returns them inline and cleans up local caches.*

---

## 9. Testing Instructions (Postman/cURL)

When running locally, FastAPI auto-generates Swagger docs at `http://127.0.0.1:8000/docs`, providing a web UI to upload images seamlessly.

Alternatively, use `cURL`:

### Example Request (Kurti)
```bash
curl -X 'POST' \\
  'http://127.0.0.1:8000/api/v1/try-on' \\
  -H 'accept: application/json' \\
  -H 'Content-Type: multipart/form-data' \\
  -F 'user_image=@/path/to/human.jpg;type=image/jpeg' \\
  -F 'garment_image=@/path/to/kurti.jpg;type=image/jpeg' \\
  -F 'category=kurti'
```

### Example Response
```json
{
  "status": "success",
  "message": "Try-On image generated successfully",
  "result_image_url": "/tmp/gradio/some_hash/image.webp",
  "job_id": "4e73b2a2b027419890f5b991cd4754ab"
}
```

---

## 10. Future Improvement Suggestions

1. **Local Model Hosting integration**: Swap out the `HFClient` with an `OnPremModelClient` that loads Diffusers, DensePose, and Graphonomy components locally using a robust Queue like Celery.
2. **Body Measurement / Size-Aware Scaling**: Use `mediapipe` for pose estimation to scale the garment image to the user's shoulder width and hip coordinates *before* sending them to the generative model.
3. **Cloud Storage**: Implement AWS S3 or Google Cloud Storage in `image_utils.py` for persistent user/garment gallery retrieval and CDN caching for an iPhone frontend.
4. **Asynchronous Task Queueing**: Since VTON inference takes 10-20 seconds per generation, use a job-polling architecture `POST /tryon` -> returns `job_id`, followed by `GET /status/{job_id}` for mobile UX. 
