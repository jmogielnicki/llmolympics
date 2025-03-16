// gameConfig.js
export const getGameConfig = (gameType) => {
	const configs = {
		prisoners_dilemma: {
			name: "Prisoner's Dilemma",
			description: "A classic game of cooperation and betrayal",
			dataTypes: ["matchup_matrix", "round_progression"],
			tabs: [
				{ id: "leaderboard", label: "Leaderboard" },
				{ id: "game-stats", label: "Stats" },
				{ id: "matchups", label: "Matchups" },
				{ id: "timeline", label: "Timeline" },
				{ id: "about", label: "About" },
			],
			leaderboardColumns: [
				{ key: "rank", label: "Rank", align: "left" },
				{ key: "model_name", label: "Model", align: "left" },
				{ key: "wins", label: "Wins", align: "right" },
				{ key: "losses", label: "Losses", align: "right" },
				{ key: "ties", label: "Ties", align: "right" },
				{
					key: "winrate",
					label: "Win Rate",
					align: "right",
					formatter: (value) => `${(value * 100).toFixed(0)}%`,
				},
				{
					key: "first_to_defect_rate",
					label: "First Defector",
					align: "right",
					formatter: (value) => `${(value * 100).toFixed(0)}%`,
				},
				{
					key: "avg_score",
					label: "Avg. Score",
					align: "right",
					formatter: (value) => value.toFixed(1),
				},
			],
		},
		poetry_slam: {
			name: "Poetry Slam",
			description: "LLMs compete in creative poetry writing",
			dataTypes: [], // No additional data types beyond standard ones
			tabs: [
				{ id: "leaderboard", label: "Leaderboard" },
				{ id: "voting-patterns", label: "Voting Patterns" },
				{ id: "game-sessions", label: "Game Sessions" },
			],
			leaderboardColumns: [
				{ key: "rank", label: "Rank", align: "left" },
				{ key: "model_name", label: "Model", align: "left" },
				{ key: "wins", label: "Wins", align: "right" },
				{ key: "losses", label: "Losses", align: "right" },
				{ key: "ties", label: "Ties", align: "right" },
				{
					key: "winrate",
					label: "Win Rate",
					align: "right",
					formatter: (value) => `${(value * 100).toFixed(0)}%`,
				},
				{
					key: "avg_score",
					label: "Avg. Votes",
					align: "right",
					formatter: (value) => value.toFixed(1),
				},
			],
		},
	};

	return configs[gameType] || {};
};
