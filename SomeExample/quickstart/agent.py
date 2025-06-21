import random

from google.adk.agents import Agent


def get_weather(city: str) -> str:
  """Retrieves the current weather report for a specified city.
  Args:
      city (str): The name of the city for which to retrieve the weather report.
  Returns:
      str
  """
  return random.choice(["Sunny", "Rainy", "Snowy"])

root_agent = Agent(
    name="weather_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to answer questions about the time and weather in a city."
    ),
    instruction=(
        "I can answer your questions about the time and weather in a city."
    ),
    tools=[get_weather],
)
