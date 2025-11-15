"""
Quick script to clear response cache and test SYN integration
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_cache():
    """Clear the response cache directory"""
    import os
    import shutil
    
    cache_dir = "/Users/mac/git new/astrologyfinalrk/.cache"
    if os.path.exists(cache_dir):
        logger.info(f"Removing cache directory: {cache_dir}")
        shutil.rmtree(cache_dir)
        logger.info("✅ Cache cleared")
    else:
        logger.info("No cache directory found - nothing to clear")

if __name__ == "__main__":
    clear_cache()
