# Project Technical Summary: AI Virtual Try-On (VITON)

This document provides a comprehensive list of the technologies, tools, data, and libraries used in the VITON project, suitable for inclusion in a research paper or technical publication.

## 1. Programming Languages
- **Backend**: Python 3.10+ (Core logic, API development, and AI orchestration)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)

## 2. Frameworks & Architecture
- **Web Framework**: **FastAPI** (High-performance ASGI framework for building APIs with Python)
- **Server**: **Uvicorn** (Lightning-fast ASGI server implementation)
- **Architecture**: Modular Monolith with separate layers for API routes, service orchestration, and specialized garment pipelines.

## 3. Core Libraries & Dependencies
- **API & Data**: `fastapi`, `pydantic`, `pydantic-settings`, `python-multipart`
- **Image Processing**:
    - **Pillow (PIL)**: Used for image manipulation, resizing, and composite blending.
    - **OpenCV (opencv-python-headless)**: Utilized for advanced computer vision tasks and masking logic.
- **AI Client**: `gradio-client` (For seamless interaction with Hugging Face ZeroGPU spaces).
- **Utilities**: `requests`, `python-dotenv`, `uuid`.

## 4. AI Models & Inference Stack
- **Primary Model**: **IDM-VTON** (Identity-Preserving Realistic Virtual Try-On)
    - Source: `yisol/IDM-VTON` (Hugging Face Space)
- **Secondary Reference**: **OOTDiffusion** (Used for outfit-based try-on logic).
- **Inference Platform**: **Hugging Face Inference API** utilizing **ZeroGPU** hardware for high-speed diffusion-based generation.

## 5. Specialized Algorithms & Logic
- **Indian Ethnic Wear Optimization**: 
    - Custom masking algorithms for non-Western garments (Kurtis and Lehengas).
    - Dynamic masking ratios: `0.60` for knee-length garments (Kurtis) and `0.95` for floor-length garments (Lehengas) to prevent limb artifacts.
- **Identity Preservation**:
    - Post-processing stitching algorithm using Gaussian-blurred feathering to blend original facial identity and body pose back onto AI-generated results.
- **Denoising Strategy**: Category-specific denoising steps (30-40 steps) optimized for garment complexity.

## 6. Data Specifications
- **Human Input**: High-resolution (max 1024px) RGB portraits with consistent lighting.
- **Garment Input**: Product images on flat backgrounds or mannequins.
- **Masking Data**: Dynamically generated binary/alpha masks centered on garment regions.

## 7. Development Tools
- **Operating System**: Windows / Linux
- **Deployment**: Scalable API architecture designed for cloud deployment (Docker-ready).
- **Environment Management**: [.env](file:///c:/Users/Pooja/OneDrive/Desktop/VITON/.env) based configuration for API security and model parameters.
