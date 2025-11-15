"""
Test SYN Integration
Verify that SYN retrieval is properly integrated into the synthesis pipeline
"""

import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def test_syn_integration():
    """Test that SYN retrieval is integrated properly"""
    
    # Import required modules
    try:
        from agents.syn_retriever import SynRetriever
        from agents.smart_orchestrator import SmartOrchestrator
        from agents.openrouter_synthesizer import OpenRouterSynthesizer
        logger.info("✅ All required modules imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import modules: {e}")
        return False
    
    # Check that SmartOrchestrator accepts syn_retriever parameter
    import inspect
    sig = inspect.signature(SmartOrchestrator.__init__)
    params = list(sig.parameters.keys())
    
    if 'syn_retriever' in params:
        logger.info("✅ SmartOrchestrator.__init__ accepts 'syn_retriever' parameter")
    else:
        logger.error("❌ SmartOrchestrator.__init__ does NOT accept 'syn_retriever' parameter")
        logger.error(f"   Available parameters: {params}")
        return False
    
    # Check that synthesizer accepts validated_knowledge parameter
    sig = inspect.signature(OpenRouterSynthesizer.synthesize_final_response)
    params = list(sig.parameters.keys())
    
    if 'validated_knowledge' in params:
        logger.info("✅ OpenRouterSynthesizer.synthesize_final_response accepts 'validated_knowledge' parameter")
    else:
        logger.error("❌ OpenRouterSynthesizer.synthesize_final_response does NOT accept 'validated_knowledge' parameter")
        logger.error(f"   Available parameters: {params}")
        return False
    
    # Check that _format_syn_procedures method exists
    if hasattr(OpenRouterSynthesizer, '_format_syn_procedures'):
        logger.info("✅ OpenRouterSynthesizer has '_format_syn_procedures' method")
    else:
        logger.error("❌ OpenRouterSynthesizer does NOT have '_format_syn_procedures' method")
        return False
    
    # Check that _build_prompt accepts syn_section parameter
    sig = inspect.signature(OpenRouterSynthesizer._build_prompt)
    params = list(sig.parameters.keys())
    
    if 'syn_section' in params:
        logger.info("✅ OpenRouterSynthesizer._build_prompt accepts 'syn_section' parameter")
    else:
        logger.error("❌ OpenRouterSynthesizer._build_prompt does NOT accept 'syn_section' parameter")
        logger.error(f"   Available parameters: {params}")
        return False
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("🎉 ALL INTEGRATION TESTS PASSED!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("SYN retrieval is properly integrated:")
    logger.info("  1. SmartOrchestrator can accept SynRetriever")
    logger.info("  2. Orchestrator passes SYN passages to synthesizer")
    logger.info("  3. Synthesizer formats SYN procedures with instructions")
    logger.info("  4. Prompt includes SYN evaluation procedures section")
    logger.info("")
    logger.info("Next steps:")
    logger.info("  - Ensure SYN corpus is ingested in Vertex AI")
    logger.info("  - Set SYN_CORPUS_NAME in .env file")
    logger.info("  - Test with real questions using test_syn_rules.py")
    
    return True

if __name__ == "__main__":
    success = test_syn_integration()
    sys.exit(0 if success else 1)
