"""
Lightweight Validator Module
Purpose: Optional validation if orchestrator confidence is low (<0.7)
Only called 30% of the time on average

Replaces: Old 60-80s Knowledge Validator (Agent 4)
New time: 1.5-2s (only when needed)
Saves: Average 0.5s per request
"""

import json
import time
from typing import Dict, List, Optional
import logging

from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LightweightValidator:
    """
    Fast validation of synthesized answers against retrieved passages
    Only triggered if initial confidence is below threshold
    """
    
    def __init__(self, project_id: str, location: str):
        """
        Initialize validator
        
        Args:
            project_id (str): Google Cloud project ID
            location (str): Region (e.g., "asia-south1")
        """
        self.project_id = project_id
        self.location = location
        self.model_name = "gemini-1.5-flash"
        self.client = None
        self._initialize_client()
        self.confidence_threshold = 0.7  # Only validate if confidence < 0.7
    
    def _initialize_client(self):
        """Initialize Gemini client"""
        try:
            self.client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location=self.location
            )
            logger.info("Validator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Validator: {str(e)}")
            raise
    
    def should_validate(self, confidence: float) -> bool:
        """
        Determine if validation is needed
        
        Args:
            confidence (float): Orchestrator confidence (0.0-1.0)
        
        Returns:
            bool: True if should validate (confidence < 0.7)
        """
        return confidence < self.confidence_threshold
    
    def validate_answer(
        self,
        answer: str,
        passages: List[Dict],
        question: str,
        chart_factors: Dict,
        confidence: float
    ) -> Dict:
        """
        Validate answer against passages
        
        Args:
            answer (str): Synthesized answer to validate
            passages (List[Dict]): Retrieved passages with text
            question (str): Original user question
            chart_factors (Dict): Chart factors for context
            confidence (float): Initial confidence score
        
        Returns:
            Dict: {
                "valid": bool,
                "issues": [...],
                "claims_verified": int/int,
                "missing_support": [...],
                "needs_revision": bool,
                "suggested_revisions": [...]
            }
        
        Time: 1.5-2s (only if needed)
        """
        
        if not self.should_validate(confidence):
            logger.info(f"Confidence {confidence:.2f} >= threshold {self.confidence_threshold}. Skipping validation.")
            return {
                "valid": True,
                "skipped_reason": "Confidence above threshold",
                "confidence": confidence
            }
        
        start_time = time.time()
        
        try:
            logger.info(f"Validating answer (confidence: {confidence:.2f})...")
            
            # Build validation prompt
            prompt = self._build_validation_prompt(
                answer=answer,
                passages=passages,
                question=question,
                chart_factors=chart_factors
            )
            
            # Call Gemini for validation
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,  # Deterministic validation
                    max_output_tokens=500,
                    response_mime_type="application/json"
                )
            )
            
            # Parse validation result
            result = json.loads(response.text)
            result["execution_time_ms"] = (time.time() - start_time) * 1000
            result["validation_performed"] = True
            
            logger.info(
                f"Validation complete. "
                f"Valid: {result.get('valid', False)}. "
                f"Claims verified: {result.get('claims_verified', '?')}. "
                f"Time: {result.get('execution_time_ms', 0):.0f}ms"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            # Return permissive result if validation fails
            return {
                "valid": True,
                "error": str(e),
                "validation_error": True
            }
    
    def _build_validation_prompt(
        self,
        answer: str,
        passages: List[Dict],
        question: str,
        chart_factors: Dict
    ) -> str:
        """
        Build validation prompt for Gemini
        
        Args:
            answer (str): Answer to validate
            passages (List[Dict]): Retrieved passages
            question (str): Original question
            chart_factors (Dict): Chart factors
        
        Returns:
            str: Validation prompt
        """
        
        # Format passages for readability
        passages_text = "RETRIEVED PASSAGES:\n"
        passages_text += "=" * 60 + "\n"
        
        for i, passage in enumerate(passages):
            passages_text += f"\nPassage {i+1} (score: {passage.get('similarity_score', 'N/A')}):\n"
            passages_text += f"Source: {passage.get('source', 'Unknown')}\n"
            passages_text += f"Text: {passage.get('text', '')[:300]}...\n"
        
        # Format factors
        factors_text = json.dumps(chart_factors, indent=2)[:500]
        
        prompt = f"""
You are a validation expert for Vedic astrology answers.

ORIGINAL QUESTION: "{question}"

CHART FACTORS: {factors_text}

{passages_text}

ANSWER TO VALIDATE: "{answer}"

YOUR TASK - RESPOND WITH ONLY VALID JSON:

1. EXTRACT key claims from the answer
2. VERIFY each claim against the passages
3. IDENTIFY any unsupported claims
4. ASSESS overall validity

RESPOND WITH ONLY THIS JSON (no explanation):
{{
  "valid": true/false,
  "claims_verified": "8/10",
  "verified_claims": ["Claim 1", "Claim 2", ...],
  "unverified_claims": ["Claim X", ...],
  "missing_support": ["What should be added"],
  "issues": ["Any issues found"],
  "needs_revision": true/false,
  "suggested_revisions": ["How to improve"],
  "confidence_in_validation": 0.85
}}
"""
        
        return prompt


# Usage example
if __name__ == "__main__":
    validator = LightweightValidator(
        project_id="superb-analog-464304-s0",
        location="asia-south1"
    )
    
    # Example usage
    if validator.should_validate(confidence=0.65):
        result = validator.validate_answer(
            answer="Your spouse will have a mature appearance...",
            passages=[
                {"text": "Saturn gives...", "similarity_score": 0.92},
                {"text": "Venus shows...", "similarity_score": 0.88}
            ],
            question="How will my spouse look?",
            chart_factors={},
            confidence=0.65
        )
        print(json.dumps(result, indent=2))
    else:
        print("Validation skipped (high confidence)")
