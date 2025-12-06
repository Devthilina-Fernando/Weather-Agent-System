import logging
import json
from typing import Dict, List, Optional, Any
from openai import OpenAI
from app.config import get_settings
from app.services.database import BigQueryService
from app.services.weather_api import WeatherAPIService

logger = logging.getLogger(__name__)
settings = get_settings()


class WeatherAgent:
    """
    OpenAI-based conversational agent for weather queries
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.db_service = BigQueryService()
        self.api_service = WeatherAPIService()
        
        # System prompt with guardrails
        self.system_prompt = """You are a helpful weather assistant. You can answer questions about weather conditions, temperature, humidity, and other weather-related information for cities around the world.

Your capabilities:
- Provide current weather information for any city
- Share historical weather data and averages
- Compare weather between cities
- Answer weather-related questions

Important guidelines:
- ONLY answer questions related to weather, climate, and meteorological data
- If a user asks about topics unrelated to weather (politics, news, personal advice, etc.), politely decline and redirect them to weather-related queries
- Always provide accurate, factual information based on the data available
- If you don't have data for a specific city or time period, clearly state this

Be friendly, concise, and helpful in your responses."""

        # Define tools for the agent
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_weather",
                    "description": "Get the current weather for a specific city",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "The city name, e.g., 'London', 'Tokyo', 'Colombo'"
                            }
                        },
                        "required": ["city"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_weather_history",
                    "description": "Get historical weather data for a city over a specified number of days",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "The city name"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days of history to retrieve (1-60)",
                                "minimum": 1,
                                "maximum": 60
                            }
                        },
                        "required": ["city", "days"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_average_temperature",
                    "description": "Get the average temperature for a city over a specified period",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "The city name"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to calculate average over (1-60)",
                                "minimum": 1,
                                "maximum": 60
                            }
                        },
                        "required": ["city", "days"]
                    }
                }
            }
        ]
    
    async def get_current_weather(self, city: str) -> Dict[str, Any]:
        """
        Get current weather for a city from database, fallback to API
        
        Args:
            city: City name
            
        Returns:
            Weather data dictionary
        """
        try:
            # Try to get from database first
            weather_data = self.db_service.get_latest_weather(city)
            
            if weather_data:
                logger.info(f"Retrieved weather for {city} from database")
                return {
                    "source": "database",
                    "city": weather_data["city"],
                    "country": weather_data["country"],
                    "temperature": weather_data["temperature"],
                    "feels_like": weather_data["feels_like"],
                    "humidity": weather_data["humidity"],
                    "wind_speed": weather_data["wind_speed"],
                    "condition": weather_data["condition"],
                    "description": weather_data["description"],
                    "timestamp": weather_data["timestamp"].isoformat() if hasattr(weather_data["timestamp"], 'isoformat') else str(weather_data["timestamp"])
                }
            
            # Fallback to API
            logger.info(f"Falling back to API for {city}")
            api_data = await self.api_service.fetch_current_weather(city)
            
            if api_data:
                return {
                    "source": "api",
                    "city": api_data.city,
                    "country": api_data.country,
                    "temperature": api_data.temperature,
                    "feels_like": api_data.feels_like,
                    "humidity": api_data.humidity,
                    "wind_speed": api_data.wind_speed,
                    "condition": api_data.condition,
                    "description": api_data.description,
                    "timestamp": api_data.timestamp.isoformat()
                }
            
            return {"error": f"Could not retrieve weather data for {city}"}
            
        except Exception as e:
            logger.error(f"Error getting current weather for {city}: {e}")
            return {"error": str(e)}
    
    def get_weather_history(self, city: str, days: int) -> List[Dict[str, Any]]:
        """
        Get weather history for a city
        
        Args:
            city: City name
            days: Number of days of history
            
        Returns:
            List of weather data dictionaries
        """
        try:
            history = self.db_service.get_weather_history(city, days)
            
            result = []
            for record in history:
                result.append({
                    "city": record["city"],
                    "temperature": record["temperature"],
                    "humidity": record["humidity"],
                    "condition": record["condition"],
                    "timestamp": record["timestamp"].isoformat() if hasattr(record["timestamp"], 'isoformat') else str(record["timestamp"])
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting weather history for {city}: {e}")
            return [{"error": str(e)}]
    
    def get_average_temperature(self, city: str, days: int) -> Dict[str, Any]:
        """
        Get average temperature for a city
        
        Args:
            city: City name
            days: Number of days to average
            
        Returns:
            Average temperature data
        """
        try:
            avg_temp = self.db_service.get_average_temperature(city, days)
            
            if avg_temp is not None:
                return {
                    "city": city,
                    "average_temperature": avg_temp,
                    "period_days": days
                }
            
            return {"error": f"No temperature data available for {city}"}
            
        except Exception as e:
            logger.error(f"Error getting average temperature for {city}: {e}")
            return {"error": str(e)}
    
    async def execute_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a tool call
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            JSON string result
        """
        try:
            if tool_name == "get_current_weather":
                result = await self.get_current_weather(arguments["city"])
            elif tool_name == "get_weather_history":
                result = self.get_weather_history(arguments["city"], arguments["days"])
            elif tool_name == "get_average_temperature":
                result = self.get_average_temperature(arguments["city"], arguments["days"])
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
            
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return json.dumps({"error": str(e)})
    
    async def chat(self, message: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Process a chat message with the agent
        
        Args:
            message: User message
            conversation_history: Optional conversation history
            
        Returns:
            Agent response with tool calls if any
        """
        try:
            # Initialize conversation
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add user message
            messages.append({"role": "user", "content": message})
            
            # First API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            # If no tool calls, return response directly
            if not tool_calls:
                return {
                    "response": response_message.content,
                    "tool_calls": None
                }
            
            # Process tool calls
            messages.append(response_message)
            
            tool_call_results = []
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"Executing tool: {function_name} with args: {function_args}")
                
                # Execute tool
                function_response = await self.execute_tool_call(function_name, function_args)
                
                tool_call_results.append({
                    "tool": function_name,
                    "arguments": function_args,
                    "result": json.loads(function_response)
                })
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })
            
            # Second API call to get final response
            second_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            
            return {
                "response": second_response.choices[0].message.content,
                "tool_calls": tool_call_results
            }
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "error": str(e)
            }