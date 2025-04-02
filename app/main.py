from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.frontend.gradio_interface import create_interface
import gradio as gr

app = FastAPI(
    title="Document Validation System",
    description="API for document validation and information extraction",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

# Create Gradio interface
interface = create_interface()

# Mount Gradio interface to root route
app = gr.mount_gradio_app(app, interface, path="/")
