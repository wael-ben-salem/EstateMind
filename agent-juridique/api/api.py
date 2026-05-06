import os
import sys
import logging
import asyncio
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Request, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import tempfile
from pathlib import Path
from dotenv import load_dotenv

from src.ingestion.law_parser import LawParser
from src.database.session_manager import SessionManager

from src.agents.rag_agent import RAGAgent
from src.tools.doc_analyzer import DocumentAnalyzer
from src.utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

# ============================================================================
# Cancellation Token Management
# ============================================================================
db_manager = SessionManager()

class CancellationToken:
    """Token for tracking and managing request cancellation."""
    def __init__(self):
        self.is_cancelled = False
        self.reason = None
    
    def cancel(self, reason: str = "Request cancelled by client"):
        """Mark the token as cancelled."""
        self.is_cancelled = True
        self.reason = reason
        logger.info("Cancellation token set: %s", reason)
    
    def check(self):
        """Raise CancelledError if token is cancelled."""
        if self.is_cancelled:
            raise asyncio.CancelledError(self.reason)


# Track active requests for cancellation
_active_requests: Dict[str, CancellationToken] = {}



def get_cancellation_token(request_id: str) -> CancellationToken:
    """Get or create a cancellation token for a request."""
    if request_id not in _active_requests:
        _active_requests[request_id] = CancellationToken()
    return _active_requests[request_id]


def cleanup_token(request_id: str):
    """Remove cancellation token when request completes."""
    if request_id in _active_requests:
        del _active_requests[request_id]
        logger.debug("Cleaned up cancellation token for request: %s", request_id)


# ============================================================================
# FastAPI App Setup
# ============================================================================
app = FastAPI(
    title="Legal Agent API",
    description="Legal document analysis and contract review using RAG Agent",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Request/Response Models
# ============================================================================

class AgentQueryRequest(BaseModel):
    """Request model for agent interaction."""
    query: str = Field(..., min_length=1, max_length=5000, description="Legal question for the agent")
    max_iterations: int = Field(default=5, ge=1, le=10, description="Maximum reasoning iterations")
    max_context_size: int = Field(default=50, ge=10, le=200, description="Maximum context items to keep")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Quelles sont les obligations d'un tuteur légal en Tunisie ?",
                "max_iterations": 5,
                "max_context_size": 50
            }
        }


class AgentResponse(BaseModel):
    """Response model for agent interaction."""
    status: str = Field(description="Status of the request (success/error)")
    result: Optional[str] = Field(description="Generated legal response from agent")
    session_id: str = Field(description="ID of the session")
    reasoning_steps: List[str] = Field(description="Step-by-step reasoning history")
    context_count: int = Field(description="Number of context items used")
    iterations_used: int = Field(description="Number of iterations used")
    reference_articles: List[Dict[str, str]] = Field(description="Retrieved reference articles with IDs and text snippets")
    error: Optional[str] = Field(None, description="Error message if failed")


class ContractAnalysisResponse(BaseModel):
    """Response model for contract analysis."""
    status: str = Field(description="Status of the request (success/error)")
    file_name: str = Field(description="Name of analyzed file")
    overall_risk_score: float = Field(description="Overall risk score (0.0-1.0)")
    risk_level: str = Field(description="Risk level (Low/Medium/High/Critical)")
    loopholes: List[Dict[str, Any]] = Field(description="Identified loopholes")
    errors: List[Dict[str, Any]] = Field(description="Identified errors")
    missing_elements: List[str] = Field(description="Missing required elements")
    suggestions: List[Dict[str, str]] = Field(description="Improvement suggestions")
    summary: Optional[str] = Field(None, description="Analysis summary")
    error: Optional[str] = Field(None, description="Error message if failed")


# ============================================================================
# Singleton Instances
# ============================================================================

_analyzer_instance: Optional[DocumentAnalyzer] = None
_parser_instance: Optional[LawParser] = None  # Reusing DocumentAnalyzer for parsing as well

def get_parser() -> LawParser:
    """Get or initialize the LawParser singleton."""
    global _parser_instance
    if _parser_instance is None:
        logger.info("Initializing LawParser")
        _parser_instance = LawParser()
    return _parser_instance

def get_analyzer() -> DocumentAnalyzer:
    """Get or initialize the DocumentAnalyzer singleton."""
    global _analyzer_instance
    if _analyzer_instance is None:
        logger.info("Initializing DocumentAnalyzer")
        _analyzer_instance = DocumentAnalyzer()
    return _analyzer_instance


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Check API health and component availability."""
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "service": "Legal Agent API",
        "version": "1.0.0"
    }


@app.post("/cancel/{request_id}", tags=["Health"])
async def cancel_request(request_id: str):
    """
    Cancel an ongoing request.
    
    Parameters:
    - request_id: The ID of the request to cancel
    
    Returns:
    - Confirmation of cancellation
    """
    try:
        token = get_cancellation_token(request_id)
        token.cancel("Request cancelled by client")
        logger.info("Cancellation request received for request_id: %s", request_id)
        return {
            "status": "cancelled",
            "request_id": request_id,
            "message": "Request cancellation signal sent"
        }
    except Exception as e:
        logger.error("Error cancelling request: %s", str(e))
        return {
            "status": "error",
            "request_id": request_id,
            "message": str(e)
        }


# ============================================================================
# Agent Endpoints
# ============================================================================

# Stockage simple en mémoire vive. Clé = session_id, Valeur = Liste de messages
active_sessions: Dict[str, Dict[str, Any]] = {}


@app.post("/agent/ask", response_model=AgentResponse, tags=["Agent"])
async def agent_ask(
    query: str = Form(..., min_length=1, max_length=5000, description="Legal question"),
    session_id: Optional[str] = Form(None, description="Session ID for continuous conversation"),
    max_iterations: int = Form(default=5, ge=1, le=10),
    max_context_size: int = Form(default=50, ge=10, le=200),
    file: Optional[UploadFile] = File(None, description="Optional PDF or image for context"),
    http_request: Request = None
):
    """
    Interact with the legal agent for complex queries with optional document context.
    
    The agent will:
    - Search for relevant legal context from knowledge base
    - Analyze any provided document for additional context
    - Draft a response based on accumulated context
    - Automatically audit the draft for accuracy
    - Submit only if audit passes
    
    Parameters:
    - query: Legal question (required)
    - max_iterations: Maximum reasoning loops (default: 5)
    - max_context_size: Maximum context items to retain (default: 50)
    - file: Optional PDF or image file for additional context (PNG, JPEG, WebP)
    - session_id: Optional session ID for maintaining conversation history across requests
    - http_request: The incoming HTTP request object (used for cancellation tracking)
    
    Returns:
    - Structured response with agent result, reasoning steps, reference articles, and metadata
    """
    temp_file_path = None
    try:
        request_id = id(http_request) if http_request else 0
        cancellation_token = get_cancellation_token(str(request_id))
        
        # 1. GESTION DE LA SESSION (Persistance DB)
        if not session_id:
            session_id = str(uuid.uuid4())
            current_session = {"history": [], "context": []}
        else:
            # Tenter de récupérer depuis la RAM (Session active)
            current_session = active_sessions.get(session_id)
            if current_session is None:
                # La session n'est pas en RAM (serveur redémarré ou session ancienne)
                # On va la chercher en DB
                logger.info("Session %s not in RAM, fetching from DB...", session_id)
                db_data = db_manager.get_session(session_id)
                current_session = {
                    "history": db_data["history"],
                    "context": db_data["context"]
                }
                # On la remet en RAM pour les prochains messages
                active_sessions[session_id] = current_session
                
                
        # Charger l'historique et le contexte légal précédent depuis la DB
        history = current_session["history"]
        offline_context = current_session["context"]
        
        logger.info("Agent query received: %s (session_id: %s)", query[:100], session_id)
        
        # 2. INITIALISATION DE L'AGENT
        agent = RAGAgent()
        agent.cancellation_token = cancellation_token
        
        # Réinitialisation de la mémoire de travail pour cette itération
        agent.memory = {
            "accumulated_context": list(offline_context), # Copie du contexte existant
            "drafts": [],
            #"audit_feedback": None,
            "steps": [],
            "search_queries": []
        }
        
        # Ré-injecter le contexte "Offline" (les lois trouvées précédemment dans cette session)
        if offline_context:
            agent.memory["accumulated_context"].extend(offline_context)
            logger.info("Re-injected %d previous legal context items", len(offline_context))
        
        agent.max_iterations = max_iterations
        agent.max_context_size = max_context_size
        
        # If document file provided, extract and add context
        if file:
            allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg", "image/webp"]
            if file.content_type not in allowed_types:
                logger.warning("Invalid file type for agent: %s", file.content_type)
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type. Allowed types: PDF, PNG, JPEG, WebP"
                )
            
            content = await file.read()
            
            logger.info("Document provided for context: %s (size: %d bytes)", file.filename, len(content))
            try:
                parser = get_parser()
                markdown = parser.export_markdown(content, filename=file.filename)
                # Add markup directly to context (chunked to fit context_chunk_size)
                markup_chunks = [markdown[i:i+agent.context_chunk_size] for i in range(0, len(markdown), agent.context_chunk_size)]
                for idx, chunk in enumerate(markup_chunks[:5]):  # Limit to 5 chunks
                    agent.memory["accumulated_context"].append({
                        "id": f"document_{idx}",
                        "text": f"DOCUMENT CONTENT : {chunk}"
                    })
                logger.info("Document markup added to agent memory: %d chunks", len(markup_chunks[:5]))
            except Exception as e:
                logger.warning("Could not extract document markup for context: %s", str(e))
                # Continue without document context
        
        # Call agent
        result = agent.ask(query, chat_history=history)

        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": result})
        
        active_sessions[session_id] = {
            "history": history[-10:], 
            "context": agent.memory["accumulated_context"]
        }
        # Extract reference articles from accumulated context
        db_manager.save_session(
            session_id=session_id, 
            history=history[-10:], # Garder les 10 derniers messages
            context=agent.memory["accumulated_context"] # Garder les lois trouvées
        )
        
        
        reference_articles = [
            {"id": item.get("id", "unknown"), "text": item.get("text", "")[:500]}
            for item in agent.memory["accumulated_context"]
        ]
        
        logger.info("Agent query completed successfully with %d reference articles", len(reference_articles))
        
        return AgentResponse(
            status="success",
            result=result,
            session_id=session_id,
            reasoning_steps=agent.memory["steps"],
            context_count=len(agent.memory["accumulated_context"]),
            iterations_used=len(agent.memory["steps"]),
            reference_articles=reference_articles,
            error=None
        )
        
    except asyncio.CancelledError:
        logger.warning("Agent query was cancelled")
        return AgentResponse(
            status="cancelled",
            result=None,
            reasoning_steps=agent.memory.get("steps", []) if 'agent' in locals() else [],
            context_count=len(agent.memory.get("accumulated_context", [])) if 'agent' in locals() else 0,
            iterations_used=0,
            reference_articles=[],
            error="Request cancelled by client"
        )
    except ValueError as e:
        logger.error("Validation error in agent query: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Fatal error in agent query: %s", str(e), exc_info=True)
        
        # Ensure we ALWAYS have a session_id so Pydantic doesn't crash
        safe_session_id = session_id if session_id else "error-session"
        
        return AgentResponse(
            status="error",
            result=None,
            session_id=safe_session_id,
            reasoning_steps=[],
            context_count=0,
            iterations_used=0,
            reference_articles=[],
            error=str(e)
        )
    finally:
        # Cleanup temp file if created
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.debug("Cleaned up temp file: %s", temp_file_path)
            except Exception as e:
                logger.warning("Failed to clean up temp file: %s", str(e))
        
        # Cleanup token on request completion
        if http_request:
            cleanup_token(str(id(http_request)))


# ============================================================================
# Contract Analysis Endpoints
# ============================================================================

@app.post("/analyze/contract", response_model=ContractAnalysisResponse, tags=["Analysis"])
async def analyze_contract(file: UploadFile = File(...)):
    """
    Analyze a contract document (PDF or image) for risks and loopholes.
    
    The analyzer will:
    - Extract text from PDF/image
    - Identify loopholes and legal risks
    - Score the document (0.0 = safe, 1.0 = critical risk)
    - Provide actionable improvement suggestions
    
    Parameters:
    - file: PDF or image file (required)
    
    Returns:
    - Detailed analysis including risk score, loopholes, errors, and suggestions
    """
    try:
        # Validate file type
        allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg", "image/webp"]
        if file.content_type not in allowed_types:
            logger.warning("Invalid file type: %s", file.content_type)
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: PDF, PNG, JPEG, WebP"
            )
        
        # Read file content
        content = await file.read()
        
        logger.info("Analyzing contract: %s (size: %d bytes)", file.filename, len(content))
        
        # Perform analysis directly with bytes
        analyzer = get_analyzer()
        report = analyzer.analyze(content, file.filename, document_type="contract")
        
        # Extract relevant fields
        risk_analysis = report.get("risk_analysis", {})
        
        logger.info("Contract analysis completed: risk_score=%.2f, risk_level=%s",
                    report.get("overall_risk_score", 0.0),
                    risk_analysis.get("risk_level", "Unknown"))
        
        return ContractAnalysisResponse(
            status="success",
            file_name=file.filename,
            overall_risk_score=report.get("overall_risk_score", 0.0),
            risk_level=risk_analysis.get("risk_level", "Unknown"),
            loopholes=risk_analysis.get("loopholes", []),
            errors=risk_analysis.get("errors", []),
            missing_elements=risk_analysis.get("missing_elements", []),
            suggestions=risk_analysis.get("suggestions", []),
            summary=risk_analysis.get("summary", ""),
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error analyzing contract: %s", str(e), exc_info=True)
        return ContractAnalysisResponse(
            status="error",
            file_name=file.filename if file else "unknown",
            overall_risk_score=0.0,
            risk_level="Unknown",
            loopholes=[],
            errors=[],
            missing_elements=[],
            suggestions=[],
            summary=None,
            error=str(e)
        )



# ============================================================================
# Documentation Endpoint
# ============================================================================

@app.get("/docs-custom", tags=["Documentation"])
async def custom_docs():
    """Get API usage documentation and examples."""
    return {
        "title": "Legal Agent API Documentation",
        "version": "1.0.0",
        "endpoints": {
            "agent": {
                "path": "/agent/ask",
                "method": "POST",
                "description": "Ask the legal agent a question and get expert analysis",
                "example": {
                    "query": "Quelles sont les obligations d'un tuteur légal en Tunisie ?",
                    "max_iterations": 5
                }
            },
            "contract_analysis": {
                "path": "/analyze/contract",
                "method": "POST",
                "description": "Analyze a contract or legal document for risks and loopholes",
                "parameters": ["file (PDF or image)"]
            },
            "batch_analysis": {
                "path": "/analyze/batch",
                "method": "POST",
                "description": "Analyze multiple documents in batch",
                "parameters": ["files (list of PDF or image)"]
            }
        }
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    logger.error("HTTP exception: %s", exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error("Unhandled exception: %s", str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "detail": "Internal server error"}
    )




if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    logger.info("Starting FastAPI server on %s:%d", host, port)
    uvicorn.run(app, host=host, port=port)
