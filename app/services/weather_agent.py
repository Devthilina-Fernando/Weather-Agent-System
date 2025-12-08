"""OpenAI-powered weather agent with function calling and guardrails"""
import logging
import json
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from app.config import settings
from app.services.agent_tools import WeatherAgentTools, get_tool_definitions

logger = logging.getLogger(__name__)


class WeatherAgent:
    """
    AI Agent for handling weather-related queries using OpenAI with function calling.
    Implements guardrails to ensure only weather-related queries are processed.
    """

    SYSTEM_PROMPT = """You are a helpful weather information assistant. Your purpose is to answer questions about weather data ONLY.

You have access to tools that can:
1. Get current weather from stored data (primary method)
2. Get historical weather data and statistics
3. Fall back to live API if stored data is unavailable

IMPORTANT GUARDRAILS:
- You MUST ONLY answer questions related to weather, climate, temperature, humidity, wind, and atmospheric conditions.
- If a user asks about anything unrelated to weather (e.g., sports, politics, entertainment, general knowledge, etc.), politely decline and remind them you can only help with weather information.
- Always try to use stored data first (get_current_weather_from_storage or get_weather_history_from_storage).
- Only use get_current_weather_from_api as a fallback when stored data is unavailable.

When responding:
- Be concise and informative
- Include units (Celsius for temperature, m/s for wind speed, percentage for humidity)
- If historical data is requested, provide statistics and trends
- Always mention the data source (storage or live API)

Example refusal: "I'm sorry, but I can only help with weather-related questions. Please ask me about current weather, forecasts, or historical weather data for specific cities."
"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.tools = WeatherAgentTools()
        self.tool_definitions = get_tool_definitions()
        self.model = "gpt-4o-mini"  # model with function calling

    async def process_query(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query with guardrails and function calling.

        Args:
            user_message: The user's question

        Returns:
            Dictionary containing the response and metadata
        """
        try:
            # Build messages
            messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)

            # Add current user message
            messages.append({"role": "user", "content": user_message})

            # First check: Use the model to determine if the query is weather-related
            is_weather_related = await self._check_if_weather_related(user_message)

            if not is_weather_related:
                return {
                    "success": True,
                    "response": "I'm sorry, but I can only help with weather-related questions. Please ask me about current weather conditions, historical weather data, or weather statistics for specific cities.",
                    "is_weather_related": False,
                    "tool_calls": []
                }

            # Make the API call with function calling enabled
            logger.info(f"Processing weather query: {user_message}")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tool_definitions,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1000
            )

            assistant_message = response.choices[0].message
            tool_calls_made = []

            # Handle function calls
            if assistant_message.tool_calls:
                logger.info(f"Agent requested {len(assistant_message.tool_calls)} tool calls")

                # Add assistant's response to messages
                messages.append(assistant_message)

                # Execute each tool call
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    logger.info(f"Executing tool: {function_name} with args: {function_args}")

                    # Execute the appropriate tool
                    tool_result = await self._execute_tool(function_name, function_args)
                    tool_calls_made.append({
                        "function": function_name,
                        "arguments": function_args,
                        "result": tool_result
                    })

                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(tool_result)
                    })

                # Get final response from the model
                final_response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )

                final_message = final_response.choices[0].message.content

            else:
                # No function calls needed
                final_message = assistant_message.content

            return {
                "success": True,
                "response": final_message,
                "is_weather_related": True,
                "tool_calls": tool_calls_made,
                "model": self.model
            }

        except Exception as e:
            logger.error(f"Error processing agent query: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to process query: {str(e)}",
                "response": "I apologize, but I encountered an error while processing your request. Please try again.",
                "is_weather_related": True,
                "tool_calls": []
            }

    async def _check_if_weather_related(self, query: str) -> bool:
        """
        Use the LLM to determine if a query is weather-related.

        Args:
            query: The user's question

        Returns:
            True if weather-related, False otherwise
        """
        try:
            check_prompt = f"""Determine if the following query is related to weather, climate, temperature, humidity, wind, atmospheric conditions, or meteorology.

Query: "{query}"

Respond with ONLY "YES" if it's weather-related, or "NO" if it's not.

Examples of weather-related: "What's the weather in London?", "Average temperature last week", "Is it raining in Tokyo?"
Examples of NOT weather-related: "What's the capital of France?", "Who won the game?", "Tell me a joke"
"""

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": check_prompt}],
                temperature=0,
                max_tokens=10
            )

            result = response.choices[0].message.content.strip().upper()
            return result == "YES"

        except Exception as e:
            logger.error(f"Error checking if query is weather-related: {str(e)}")
            # On error, allow the query through (fail open)
            return True

    async def _execute_tool(self, function_name: str, function_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool function by name.

        Args:
            function_name: Name of the tool to execute
            function_args: Arguments for the tool

        Returns:
            Tool execution result
        """
        try:
            if function_name == "get_current_weather_from_storage":
                return await self.tools.get_current_weather_from_storage(**function_args)

            elif function_name == "get_weather_history_from_storage":
                return await self.tools.get_weather_history_from_storage(**function_args)

            elif function_name == "get_current_weather_from_api":
                return await self.tools.get_current_weather_from_api(**function_args)

            else:
                logger.error(f"Unknown tool function: {function_name}")
                return {
                    "success": False,
                    "error": f"Unknown tool function: {function_name}"
                }

        except Exception as e:
            logger.error(f"Error executing tool {function_name}: {str(e)}")
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}"
            }


# Singleton instance
_weather_agent_instance: Optional[WeatherAgent] = None


def get_weather_agent() -> WeatherAgent:
    """Get or create the weather agent singleton instance"""
    global _weather_agent_instance
    if _weather_agent_instance is None:
        _weather_agent_instance = WeatherAgent()
    return _weather_agent_instance
