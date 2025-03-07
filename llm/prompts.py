class PromptTemplates:
    @staticmethod
    def get_discussion_prompt(player_id, active_players, eliminated_players, round_num, previous_messages):
        """Generate a prompt for the discussion phase."""
        active_str = ", ".join(active_players)
        eliminated_str = ", ".join(eliminated_players) if eliminated_players else "None"

        prompt = f"""
You are Player {player_id} in a game of diplomacy and elimination. Your goal is to avoid being eliminated and be the last player remaining.

Current players: {active_str}
Eliminated players: {eliminated_str}

Round: {round_num}

Previous discussion:
{previous_messages}

Share your thoughts, form alliances, or make your case. Be strategic in your communications.
Try to form alliances with other players and convince them not to vote for you.
Analyze the behavior of other players and identify who might be a threat.
Keep your message concise and focused on your strategy for this round.
"""
        return prompt

    @staticmethod
    def get_voting_prompt(player_id, active_players, eliminated_players, round_num, previous_messages):
        """Generate a prompt for the voting phase."""
        active_str = ", ".join(active_players)
        eliminated_str = ", ".join(eliminated_players) if eliminated_players else "None"

        prompt = f"""
You are Player {player_id} in a game of diplomacy and elimination. Your goal is to avoid being eliminated and be the last player remaining.

Current players: {active_str}
Eliminated players: {eliminated_str}

Round: {round_num}

Previous discussion:
{previous_messages}

It's time to vote. You must vote to eliminate one player (you cannot vote for yourself).

IMPORTANT: Start your response with "VOTE: [player_id]" followed by your reasoning.
Example:
VOTE: player3
I'm voting for player3 because they seem to be forming alliances against me...
"""
        return prompt