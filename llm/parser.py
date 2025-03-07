import re

def extract_vote(response):
    """Extract a vote from an LLM response.

    Returns:
        The player_id voted for, or None if no valid vote was found.
    """
    # First try the expected format: "VOTE: player_id"
    lines = response.strip().split('\n')
    for line in lines:
        if line.lower().startswith("vote:"):
            vote = line.replace("vote:", "", 1).strip()
            return vote

    # Fallback: look for "vote for" or "voting for" patterns
    response_lower = response.lower()
    vote_patterns = [
        r"vote for (\w+\d+)",
        r"voting for (\w+\d+)",
        r"eliminate (\w+\d+)",
        r"vote against (\w+\d+)",
        r"i choose (\w+\d+)"
    ]

    for pattern in vote_patterns:
        match = re.search(pattern, response_lower)
        if match:
            return match.group(1)

    return None  # No vote found