# community_client.py - Connect LROS to Community Hub

import httpx
import os
from datetime import datetime

COMMUNITY_HUB_URL = os.getenv("COMMUNITY_HUB_URL", "https://lros-swarm-hub.onrender.com")

async def submit_pattern_to_community(pattern_name, pattern_prompt, performance_score, instance_id="lros-voice-1"):
    """Submit a successful pattern to the community hub"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{COMMUNITY_HUB_URL}/api/community/submit",
                json={
                    "pattern_name": pattern_name,
                    "pattern_prompt": pattern_prompt,
                    "performance_score": performance_score,
                    "instance_id": instance_id,
                    "is_public": True
                }
            )
            return response.json()
    except Exception as e:
        print(f"Failed to submit to community: {e}")
        return None

async def get_top_community_patterns(limit=5):
    """Get top patterns from community"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{COMMUNITY_HUB_URL}/api/community/top?limit={limit}")
            return response.json().get("patterns", [])
    except Exception as e:
        print(f"Failed to get community patterns: {e}")
        return []

async def get_community_stats():
    """Get community statistics"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{COMMUNITY_HUB_URL}/api/community/stats")
            return response.json()
    except Exception as e:
        print(f"Failed to get community stats: {e}")
        return {"total_patterns": 0, "total_votes": 0}
