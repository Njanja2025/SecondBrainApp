from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="SecondBrain API",
    description="API for controlling and interacting with SecondBrain assistant",
    version="0.1.0",
)

class Command(BaseModel):
    """Command model for API requests."""
    command: str
    parameters: Optional[dict] = None

class Response(BaseModel):
    """Response model for API requests."""
    status: str
    message: str
    data: Optional[dict] = None

@app.get("/", response_model=Response)
async def root():
    """Root endpoint returning API status."""
    return Response(
        status="success",
        message="SecondBrain API is running",
        data={"version": "0.1.0"}
    )

@app.post("/command", response_model=Response)
async def execute_command(command: Command):
    """Execute a command on the SecondBrain assistant."""
    try:
        # Here you would integrate with your assistant logic
        logger.info(f"Executing command: {command.command}")
        return Response(
            status="success",
            message=f"Command {command.command} executed successfully",
            data={"command": command.dict()}
        )
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status", response_model=Response)
async def get_status():
    """Get the current status of the SecondBrain assistant."""
    try:
        # Here you would get actual status from your assistant
        return Response(
            status="success",
            message="Status retrieved successfully",
            data={
                "running": True,
                "voice_enabled": True,
                "last_command": None
            }
        )
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 