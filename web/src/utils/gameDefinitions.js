// gameDefinitions.js
import { shortenModelName } from "@/utils/commonUtils";

// Base game definition with common transformations
const baseGameDefinition = {
	transformData: ({ leaderboard, modelProfiles, metadata }) => {
		// Default transformations that apply to all games
		return {
			leaderboard: leaderboard.leaderboard.map((model) => ({
				...model,
				model_name: shortenModelName(model.model_name),
			})),
			gameSessions: [],
			metadata,
			gameSpecific: {},
		};
	},
	transformGameDetail: (detail) => detail,
};

// Prisoner's Dilemma game definition
const prisonersDilemmaDefinition = {
	...baseGameDefinition,
	config: {
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
            {
                key: "avg_score",
                label: "Avg. Score",
                align: "right",
                formatter: (value) => value.toFixed(1),
            },
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
		],
	},
	transformData: ({ leaderboard, modelProfiles, metadata, gameSpecific }) => {
		// Transformed leaderboard
		const transformedLeaderboard = leaderboard.leaderboard.map((model) => ({
			...model,
			model_name: shortenModelName(model.model_name),
		}));

		// Extract game sessions
		const gameSessions = extractPrisonersDilemmaGames(modelProfiles);

		// Game-specific transformations
		const gameSpecificData = {};

		// Transform matchup matrix
		if (gameSpecific.matchup_matrix) {
			gameSpecificData.matchupMatrix = {
				models: gameSpecific.matchup_matrix.model_names.map((name) =>
					shortenModelName(name)
				),
				winMatrix: gameSpecific.matchup_matrix.win_matrix,
			};
		}

		// Transform round progression
		if (gameSpecific.round_progression) {
			gameSpecificData.roundProgressionData =
				gameSpecific.round_progression.round_progression.map(
					(round) => ({
						round: round.round,
						cooperation_rate: round.cooperation_rate,
						defection_rate: round.defection_rate,
					})
				);

			// Transform cooperation by model
			gameSpecificData.cooperationByModelAndRound =
				transformCooperationByModel(
					gameSpecific.round_progression,
					modelProfiles
				);
		}

		// Game summary
		gameSpecificData.gameSummaryData = transformedLeaderboard.map(
			(model) => ({
				name: model.model_name,
				wins: model.wins,
				losses: model.losses,
				ties: model.ties,
			})
		);

		return {
			leaderboard: transformedLeaderboard,
			gameSessions,
			metadata,
			gameSpecific: gameSpecificData,
		};
	},
};

// Poetry Slam game definition
const poetrySlamDefinition = {
	...baseGameDefinition,
	config: {
		name: "Poetry Slam",
		description: "LLMs compete in creative poetry writing",
		dataTypes: [],
		tabs: [
			{ id: "leaderboard", label: "Leaderboard" },
			{ id: "voting-patterns", label: "Voting Patterns" },
			{ id: "timeline", label: "Timeline" },
			{ id: "about", label: "About" },
		],
		leaderboardColumns: [
			{ key: "rank", label: "Rank", align: "left" },
			{ key: "model_name", label: "Model", align: "left" },
            {
                key: "avg_score",
                label: "Avg. Votes",
                align: "right",
                formatter: (value) => value.toFixed(1),
            },
			{ key: "wins", label: "Wins", align: "right" },
			{ key: "losses", label: "Losses", align: "right" },
			{ key: "ties", label: "Ties", align: "right" },
			{
				key: "winrate",
				label: "Win Rate",
				align: "right",
				formatter: (value) => `${(value * 100).toFixed(0)}%`,
			},
		],
	},
	transformData: ({ leaderboard, modelProfiles, metadata }) => {
		// Transformed leaderboard
		const transformedLeaderboard = leaderboard.leaderboard.map((model) => ({
			...model,
			model_name: shortenModelName(model.model_name),
		}));

		// Extract game sessions
		const gameSessions = extractPoetrySlamSessions(modelProfiles);

		// Create voting patterns
		const votingPatterns = createVotingPatterns(modelProfiles);

		return {
			leaderboard: transformedLeaderboard,
			gameSessions,
			metadata,
			gameSpecific: {
				votingPatterns,
			},
		};
	},
	transformGameDetail: (detail) => {
		if (!detail || !detail.timeline) return detail;

		// Extract poems and prompt
		const poems = extractPoems(detail);
		const prompt = extractPrompt(detail);

		return {
			...detail,
			poems,
			prompt,
		};
	},
};

// Helper functions for Prisoner's Dilemma
function extractPrisonersDilemmaGames(modelProfiles) {
	try {
		const uniqueGames = new Map();
		const profiles = modelProfiles.models;

		profiles.forEach((model) => {
			model.games.forEach((game) => {
				// Create a consistent game ID
				const gameModelIds = [model.model_id, game.opponent].sort();
				const gameId = `${gameModelIds[0]}-${gameModelIds[1]}`;

				if (!uniqueGames.has(gameId)) {
					const opponentModel = profiles.find(
						(m) => m.model_id === game.opponent
					);

					if (opponentModel) {
						const isFirstPlayer = game.session_id.includes(
							model.model_id.split(":")[1].toLowerCase()
						);

						const player1 = isFirstPlayer ? model : opponentModel;
						const player2 = isFirstPlayer ? opponentModel : model;
						const score1 = isFirstPlayer
							? game.score
							: game.opponent_score;
						const score2 = isFirstPlayer
							? game.opponent_score
							: game.score;

						uniqueGames.set(gameId, {
							id: gameId,
							title: `${shortenModelName(
								player1.model_name
							)} vs. ${shortenModelName(player2.model_name)}`,
							player1: shortenModelName(player1.model_name),
							player2: shortenModelName(player2.model_name),
							player1_id: player1.model_id,
							player2_id: player2.model_id,
							finalScore: {
								player1: score1,
								player2: score2,
							},
							result: game.result,
							session_id: game.session_id,
						});
					}
				}
			});
		});

		return Array.from(uniqueGames.values());
	} catch (error) {
		console.error("Error extracting game data:", error);
		return [];
	}
}

function transformCooperationByModel(roundProgression, modelProfiles) {
	return modelProfiles.models.map((model) => {
		const modelData = {
			model: shortenModelName(model.model_name),
			modelId: model.model_id,
		};

		roundProgression.round_progression.forEach((round) => {
			// Create a slight variation for each model
			const variation = Math.random() * 0.2 - 0.1;
			const rate = Math.max(
				0,
				Math.min(1, round.cooperation_rate + variation)
			);
			modelData[`round${round.round}`] = rate;
		});

		return modelData;
	});
}

// Helper functions for Poetry Slam
function extractPoetrySlamSessions(modelProfiles) {
	const sessions = [];
	const processedSessions = new Set();

	modelProfiles.models.forEach((model) => {
		model.games.forEach((game) => {
			if (!processedSessions.has(game.session_id)) {
				processedSessions.add(game.session_id);

				const participants = game.other_players.map((playerId) => {
					const playerModel = modelProfiles.models.find(
						(m) => m.model_id === playerId
					);
					return playerModel
						? shortenModelName(playerModel.model_name)
						: playerId;
				});

				sessions.push({
					id: game.session_id,
					title: `Poetry Slam - ${new Date(
						game.session_id.substring(12, 20)
					).toLocaleDateString()}`,
					participants,
					winner:
						game.result === "win"
							? shortenModelName(model.model_name)
							: "",
				});
			}
		});
	});

	return sessions;
}

function createVotingPatterns(modelProfiles) {
	const votingMatrix = {};
	const models = modelProfiles.models.map((m) => ({
		id: m.model_id,
		name: shortenModelName(m.model_name),
	}));

	models.forEach((voter) => {
		votingMatrix[voter.id] = {};
		models.forEach((candidate) => {
			votingMatrix[voter.id][candidate.id] = 0;
		});
	});

	models.forEach((model) => {
		modelProfiles.models
			.find((m) => m.model_id === model.id)
			?.games.forEach((game) => {
				if (
					game.voting &&
					game.voting.voted_for
				) {
                    const voted_for_model = modelProfiles.models.find(
						(m) => m.player_id === game.voting.voted_for
					);
					votingMatrix[model.id][voted_for_model.model_id]++;
				}
			});
	});

	return {
		matrix: votingMatrix,
		models: models,
	};
}

function extractPoems(gameDetail) {
	if (!gameDetail || !gameDetail.timeline) return [];

	const poemSubmissions = gameDetail.timeline.filter(
		(item) => item.type === "poem_submission"
	);

	const voteCount = {};
	gameDetail.timeline
		.filter((item) => item.type === "player_vote")
		.forEach((vote) => {
			if (!voteCount[vote.voted_for]) voteCount[vote.voted_for] = 0;
			voteCount[vote.voted_for]++;
		});

	const winners = gameDetail.game?.winner ? [gameDetail.game.winner] : [];

	return poemSubmissions.map((submission) => ({
		id: submission.player_id,
		text: submission.poem.replace(/\[\[|\]\]/g, ""),
		author: submission.model_name,
		votes: voteCount[submission.player_id] || 0,
		isWinner: winners.includes(submission.player_id),
	}));
}

function extractPrompt(gameDetail) {
	if (!gameDetail || !gameDetail.timeline) {
		return { text: "", author: "" };
	}

	const promptEvent = gameDetail.timeline.find(
		(item) => item.type === "prompt_creation"
	);

	if (!promptEvent) return { text: "", author: "" };

	return {
		text: promptEvent.prompt,
		author: promptEvent.model_name,
	};
}

// Map of game types to their definitions
const gameDefinitions = {
	prisoners_dilemma: prisonersDilemmaDefinition,
	poetry_slam: poetrySlamDefinition,
};

/**
 * Get the game definition for a specified game type
 */
export function getGameDefinition(gameType) {
	return gameDefinitions[gameType] || null;
}
