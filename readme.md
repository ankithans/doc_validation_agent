## Core components

### 1. FastAPI Service

### 2. Document Pre-processor

This component handles document preparation, including:

- Image optimization (contrast enhancement, denoising) - how? with which library
- Document type classification (ID card, utility bill, bank statement) - not sure, if this can be done without LLM surely?
- Image quality checks - how? with which library
- Document orientation correction - do we really need to do this? how? with which library

### 3. LLM-based OCR Engine

This is where PydanticAI and Gemini Flash 2.0 come in:

- Creating the Pydantic AI models for each document type - do we need to add field defination only in the desc? or we should add where to lookup this field? Like do this happen in the model itself or the agent prompt - little confused - which is better?
- Different Pydantic Agents for each document type

### 4. Confidence Analyzer

are we analyzing confidence with LLM or is it via some python library?

### 5. Validation Engine

## Implementation Approach

### Phase 1: MVP with Single Document Processing

1. Build a simple FastAPI endpoint that accepts document uploads
2. Create a document type classifier (start with a few common types) - okay again, is this LLM doing or some library?
3. Implement PydanticAI agents for each document type - do we need multiple agents for each document type? kindly draw the architecture
4. Add basic validation rules for each document type
5. Return structured responses with confidence scores

```python
async def process_document(file_bytes: bytes) -> OCRResponse:
    # Preprocess and detect document type
    processed_image, doc_type = await preprocess_document(file_bytes)

    # Select appropriate agent based on document type
    agent = get_agent_for_document_type(doc_type)

    # Convert image to base64 for LLM
    image_b64 = base64.b64encode(processed_image).decode('utf-8')

    # Run OCR via the agent
    result = await agent.run(image_b64)

    # Analyze confidence scores
    confidence_analysis = analyze_confidence(result.data)

    # Validate extracted data
    validation_errors = validate_document(doc_type, result.data)

    # Format response
    return OCRResponse(
        document_type=doc_type,
        confidence_scores={field: getattr(result.data, field).confidence
                           for field in result.data.__fields__ if field != 'document_type'},
        extracted_fields={field: getattr(result.data, field).value
                         for field in result.data.__fields__ if field != 'document_type'},
        validation_errors=validation_errors
    )
```

## gemini explicit confidence assessment

not sure if this will work out, like will the model hallucinate?

```python
system_prompt="""
For each extracted field, provide:
1. The extracted text value
2. A confidence score from 0.0 to 1.0 with these guidelines:
   - 0.9-1.0: Text is crystal clear, no ambiguity
   - 0.7-0.9: Text is readable with minor issues
   - 0.5-0.7: Text is partially readable with some uncertainty
   - 0.0-0.5: Text is illegible or highly uncertain
3. A boolean flag indicating if the text appears to be complete (not cut off/cropped)

Base your confidence scores on:
- Text clarity and contrast
- Whether characters are fully visible
- Presence of artifacts, smudges, or damage
- Alignment and perspective issues
"""
```

Consider using @agent.tool decorators to add helper functions:

```python
@id_card_agent.tool
def analyze_image_quality(image_section: str) -> dict:
    """
    Analyze the quality of a specific section of the image.
    Input is a base64 encoded image section.

    Returns quality metrics for this specific part of the document.
    """
    # This would be implemented in your actual code
    # For MVP, the LLM itself can provide these assessments
    pass
```

## Example usage of pydantic

```python
from __future__ import annotations as _annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any

import logfire
from devtools import debug
from httpx import AsyncClient

from pydantic_ai import Agent, ModelRetry, RunContext

# 'if-token-present' means nothing will be sent (and the example will work) if you don't have logfire configured
logfire.configure(send_to_logfire='if-token-present')


@dataclass
class Deps:
    client: AsyncClient
    weather_api_key: str | None
    geo_api_key: str | None


weather_agent = Agent(
    'openai:gpt-4o',
    # 'Be concise, reply with one sentence.' is enough for some models (like openai) to use
    # the below tools appropriately, but others like anthropic and gemini require a bit more direction.
    system_prompt=(
        'Be concise, reply with one sentence.'
        'Use the `get_lat_lng` tool to get the latitude and longitude of the locations, '
        'then use the `get_weather` tool to get the weather.'
    ),
    deps_type=Deps,
    retries=2,
    instrument=True,
)


@weather_agent.tool
async def get_lat_lng(
    ctx: RunContext[Deps], location_description: str
) -> dict[str, float]:
    """Get the latitude and longitude of a location.

    Args:
        ctx: The context.
        location_description: A description of a location.
    """
    if ctx.deps.geo_api_key is None:
        # if no API key is provided, return a dummy response (London)
        return {'lat': 51.1, 'lng': -0.1}

    params = {
        'q': location_description,
        'api_key': ctx.deps.geo_api_key,
    }
    with logfire.span('calling geocode API', params=params) as span:
        r = await ctx.deps.client.get('https://geocode.maps.co/search', params=params)
        r.raise_for_status()
        data = r.json()
        span.set_attribute('response', data)

    if data:
        return {'lat': data[0]['lat'], 'lng': data[0]['lon']}
    else:
        raise ModelRetry('Could not find the location')


@weather_agent.tool
async def get_weather(ctx: RunContext[Deps], lat: float, lng: float) -> dict[str, Any]:
    """Get the weather at a location.

    Args:
        ctx: The context.
        lat: Latitude of the location.
        lng: Longitude of the location.
    """
    if ctx.deps.weather_api_key is None:
        # if no API key is provided, return a dummy response
        return {'temperature': '21 °C', 'description': 'Sunny'}

    params = {
        'apikey': ctx.deps.weather_api_key,
        'location': f'{lat},{lng}',
        'units': 'metric',
    }
    with logfire.span('calling weather API', params=params) as span:
        r = await ctx.deps.client.get(
            'https://api.tomorrow.io/v4/weather/realtime', params=params
        )
        r.raise_for_status()
        data = r.json()
        span.set_attribute('response', data)

    values = data['data']['values']
    # https://docs.tomorrow.io/reference/data-layers-weather-codes
    code_lookup = {
        1000: 'Clear, Sunny',
        1100: 'Mostly Clear',
        1101: 'Partly Cloudy',
        1102: 'Mostly Cloudy',
        1001: 'Cloudy',
        2000: 'Fog',
        2100: 'Light Fog',
        4000: 'Drizzle',
        4001: 'Rain',
        4200: 'Light Rain',
        4201: 'Heavy Rain',
        5000: 'Snow',
        5001: 'Flurries',
        5100: 'Light Snow',
        5101: 'Heavy Snow',
        6000: 'Freezing Drizzle',
        6001: 'Freezing Rain',
        6200: 'Light Freezing Rain',
        6201: 'Heavy Freezing Rain',
        7000: 'Ice Pellets',
        7101: 'Heavy Ice Pellets',
        7102: 'Light Ice Pellets',
        8000: 'Thunderstorm',
    }
    return {
        'temperature': f'{values["temperatureApparent"]:0.0f}°C',
        'description': code_lookup.get(values['weatherCode'], 'Unknown'),
    }


async def main():
    async with AsyncClient() as client:
        # create a free API key at https://www.tomorrow.io/weather-api/
        weather_api_key = os.getenv('WEATHER_API_KEY')
        # create a free API key at https://geocode.maps.co/
        geo_api_key = os.getenv('GEO_API_KEY')
        deps = Deps(
            client=client, weather_api_key=weather_api_key, geo_api_key=geo_api_key
        )
        result = await weather_agent.run(
            'What is the weather like in London and in Wiltshire?', deps=deps
        )
        debug(result)
        print('Response:', result.data)


if __name__ == '__main__':
    asyncio.run(main())
```
