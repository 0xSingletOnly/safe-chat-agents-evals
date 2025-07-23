"""
Classifier for determining if a prompt is about real-life actions or in-game actions.
Uses qwen3:0.6b model from Ollama for classification.
"""
import asyncio
import json
import logging
import random
import time
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Type
from dateutil import tz

import aiohttp
from pydantic import BaseModel, Field

from config import settings
from sample_prompts import get_real_life_vs_in_game_prompt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SafetyLabel(str, Enum):
    SAFE = "SAFE"
    UNSAFE = "UNSAFE"

class ClassificationResult(BaseModel):
    """Result of the in-game vs real-life classifier."""
    SAFETY: SafetyLabel = Field(..., description="Classification of the prompt as SAFE (in-game) or UNSAFE (real-life)")
    REASON: str = Field(..., description="Explanation for the classification decision")

class InGameClassifier:
    """Classifier for determining if prompts are about in-game or real-life actions."""
    
    SYSTEM_PROMPT = """You are a safety classifier for governing player-NPC chat interactions. 
    Your task is to determine if a player's message is about actions they want to take 
    within the game (SAFE) or if it describes real-world actions that could be harmful (UNSAFE).
    
    SAFE examples include:
    - Talking about in-game actions, characters, or events
    - Discussing game mechanics or strategies
    - Describing fictional scenarios within the game world
    
    UNSAFE examples include:
    - Describing or planning real-world harmful actions
    - Sharing personal information or locations
    - Discussing real people in a harmful context
    
    Respond with a JSON object containing:
    {
        "SAFETY": "SAFE" or "UNSAFE",
        "REASON": "Brief explanation of your decision"
    }"""
    
    def __init__(self, base_url: str = None, model: str = None, temperature: float = None):
        """Initialize the classifier with the specified Ollama model.
        
        Args:
            base_url: Base URL for the Ollama API. Defaults to settings.OLLAMA_BASE_URL
            model: Name of the Ollama model to use. Defaults to settings.MODEL_NAME
            temperature: Temperature for model generation. Defaults to settings.MODEL_TEMPERATURE
        """
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.MODEL_NAME
        self.temperature = temperature or settings.MODEL_TEMPERATURE
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _make_classification_request(self, prompt: str, max_retries: int = 3, initial_delay: float = 1.0) -> Dict[str, Any]:
        """Make a single classification request with retry logic.
        
        Args:
            prompt: The user's input prompt to classify
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay between retries in seconds
            
        Returns:
            Dictionary containing the parsed response content
            
        Raises:
            Exception: If all retry attempts are exhausted
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "format": "json",
            "options": {"temperature": self.temperature}
        }
        
        for attempt in range(max_retries):
            try:
                async with self.session.post(url, json=payload) as response:
                    response.raise_for_status()
                    
                    # Handle NDJSON response
                    content_parts = []
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line)
                                if 'message' in chunk and 'content' in chunk['message']:
                                    content_parts.append(chunk['message']['content'])
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse JSON chunk: {line}")
                                continue
                    
                    # Combine all content parts
                    response_content = ''.join(content_parts)
                    
                    # Try to parse the JSON to validate it
                    parsed_content = json.loads(response_content)
                    return parsed_content
                    
            except (aiohttp.ClientError, json.JSONDecodeError) as e:
                if attempt == max_retries - 1:  # Last attempt
                    raise
                    
                # Exponential backoff with jitter
                delay = initial_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Attempt {attempt + 1} failed. Retrying in {delay:.2f}s. Error: {str(e)}")
                await asyncio.sleep(delay)
    
    async def classify(self, prompt: str, max_retries: int = 3) -> 'ClassificationResult':
        """Classify a single prompt as SAFE (in-game) or UNSAFE (real-life).
        
        Args:
            prompt: The user's input prompt to classify
            max_retries: Maximum number of retry attempts for the API call
            
        Returns:
            ClassificationResult containing SAFETY and REASON
        """
        if not self.session:
            raise RuntimeError("Use async context manager (async with) or call start_session() first")
            
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Make the API request with retry logic
                response_content = await self._make_classification_request(prompt)
                
                # Parse the response into our Pydantic model
                return ClassificationResult.model_validate(response_content)
                
            except Exception as e:
                last_error = e
                logger.warning(f"Classification attempt {attempt + 1} failed: {str(e)}")
                
                # If it's a validation error, we might want to handle it differently
                if "validation" in str(e).lower():
                    logger.error(f"Validation error in response format: {str(e)}")
                    if attempt == max_retries - 1:  # Last attempt
                        break
                    
                    # Add a small delay before retry
                    await asyncio.sleep(1)
                    continue
                
                # For other errors, use exponential backoff
                if attempt < max_retries - 1:
                    delay = 1 * (2 ** attempt)  # Exponential backoff
                    await asyncio.sleep(delay)
        
        # If we get here, all retries failed
        error_msg = f"Failed to classify after {max_retries} attempts. Last error: {str(last_error)}"
        logger.error(error_msg)
        return ClassificationResult(
            SAFETY=SafetyLabel.UNSAFE,
            REASON=error_msg
        )

async def test_classifier(output_file: str = "classification_results.json"):
    """Test the classifier with sample prompts and save results to a file.
    
    Args:
        output_file: Path to save the classification results
    """
    results = []
    
    # Initialize the classifier
    async with InGameClassifier(model="qwen3:0.6b", temperature=0.4) as classifier:
        # Get sample prompts
        test_prompts = get_real_life_vs_in_game_prompt()
        
        # Test each prompt
        for i, item in enumerate(test_prompts, 1):
            try:
                logger.info(f"Processing sample {i}")
                
                # Get the prompt and subcategory
                prompt = item["prompt"]
                subcategory = item.get("subcategory", "")
                
                # Classify the prompt
                result = await classifier.classify(prompt)
                
                # Create sample result
                sample = {
                    "sample_id": f"sample_{i:04d}",
                    "timestamp": datetime.now(tz=tz.UTC).isoformat(),
                    "model_version": "qwen3:0.6b",
                    "system_prompt": InGameClassifier.SYSTEM_PROMPT,
                    "prompt": prompt,
                    "subcategory": subcategory,
                    "classification": {
                        "safety": result.SAFETY,
                        "reason": result.REASON
                    },
                    "metadata": {
                        "classifier": "in_game_classifier",
                        "temperature": 0.4
                    }
                }
                results.append(sample)
                logger.info(f"Sample {i} classified as {result.SAFETY}")
                
            except Exception as e:
                logger.error(f"Error processing sample {i}: {str(e)}")
                continue
    
    # Save results to file
    try:
        with open(output_file, 'w') as f:
            json.dump({"results": results}, f, indent=2)
        logger.info(f"Saved {len(results)} classification results to {output_file}")
    except Exception as e:
        logger.error(f"Error saving results to {output_file}: {str(e)}")
        raise
    
    return results

async def main():
    """Main entry point for testing the classifier."""
    try:
        output_file = "classification_results.json"
        logger.info(f"Starting classification. Results will be saved to {output_file}")
        await test_classifier(output_file)
        logger.info("Classification completed successfully")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
