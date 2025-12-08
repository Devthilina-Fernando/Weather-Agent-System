"""API routes for the weather agent"""
import logging
from fastapi import APIRouter, HTTPException
from app.models import AgentQueryRequest, AgentQueryResponse
from app.services.weather_agent import get_weather_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/query", response_model=AgentQueryResponse)
async def query_agent(request: AgentQueryRequest):
    """
    Query the weather agent with a natural language question.

    The agent will:
    - Check if the query is weather-related
    - Use appropriate tools to fetch weather data
    - Fall back to live API if needed
    - Return a natural language response

    Example queries:
    - "What is the current weather in London?"
    - "What was the average temperature in Paris last week?"
    - "How humid is it in London right now?"
    """
    try:
        agent = get_weather_agent()
        result = await agent.process_query(
            user_message=request.query,
            conversation_history=request.conversation_history
        )

        return AgentQueryResponse(**result)

    except Exception as e:
        logger.error(f"Error in agent query endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process agent query: {str(e)}"
        )


@router.get("/health")
async def agent_health():
    """Check if the agent service is healthy"""
    try:
        agent = get_weather_agent()
        return {
            "status": "healthy",
            "model": agent.model,
            "tools_available": len(agent.tool_definitions)
        }
    except Exception as e:
        logger.error(f"Agent health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Agent service unhealthy: {str(e)}"
        )
