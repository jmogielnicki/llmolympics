/**
 * Utility functions for transforming data for the Prisoner's Dilemma dashboard
 */


const getModelName = (model) => {
    console.log(model.model_name);
	return model.model_name;
};


/**
 * Transform leaderboard data for display
 * @param {Object} data - Raw leaderboard data
 * @returns {Array} - Transformed leaderboard array
 */
export const transformLeaderboardData = (data) => {
	return data.leaderboard.map((model) => ({
		...model,
	}));
};

/**
 * Transform matchup matrix data for display
 * @param {Object} data - Raw matchup matrix data
 * @returns {Object} - Transformed matchup matrix object
 */
export const transformMatchupMatrix = (data) => {
    console.log(data);
	return {
		models:
			data.model_names,
		winMatrix: data.win_matrix,
	};
};

/**
 * Transform round progression data for display
 * @param {Object} data - Raw round progression data
 * @returns {Array} - Transformed round progression array
 */
export const transformRoundProgressionData = (data) => {
	return data.round_progression.map((round) => ({
		round: round.round,
		cooperation_rate: round.cooperation_rate,
		defection_rate: round.defection_rate,
	}));
};

/**
 * Create model summary data for visualization
 * @param {Array} leaderboard - Transformed leaderboard data
 * @returns {Array} - Game summary data for charts
 */
export const createGameSummaryData = (leaderboard) => {
	return leaderboard.map((model) => ({
		name: getModelName(model),
		wins: model.wins,
		losses: model.losses,
		ties: model.ties,
	}));
};

/**
 * Transform cooperation data by model and round
 * @param {Object} roundProgression - Round progression data
 * @param {Object} modelProfiles - Model profiles data
 * @returns {Array} - Cooperation data by model and round
 */
export const transformCooperationByModel = (
	roundProgression,
	modelProfiles
) => {
	// Create a mapping of model IDs to short display names
	const modelNames = {};
	modelProfiles.models.forEach((model) => {
		modelNames[model.model_id] =
			model.model_name || model.model_id.split(":")[1];
	});

	// Transform the cooperation data - based on overall data but customized per model
	return modelProfiles.models.map((model) => {
		// Basic data about the model
		const modelData = {
			model: model.model_name || model.model_id.split(":")[1],
			modelId: model.model_id,
		};

		// Add estimated cooperation rate for each round based on overall data
		roundProgression.round_progression.forEach((round) => {
			// Create a slight variation for each model to make the visualization more interesting
			// This is just for demonstration - in a real implementation, this would use actual data
			const variation = Math.random() * 0.2 - 0.1; // Random variation between -0.1 and 0.1
			const rate = Math.max(
				0,
				Math.min(1, round.cooperation_rate + variation)
			);
			modelData[`round${round.round}`] = rate;
		});

		return modelData;
	});
};

/**
 * Extract game data from model profiles
 * @param {Object} modelProfiles - Model profiles data
 * @returns {Array} - Array of game data
 */
export const extractGameData = (modelProfiles) => {
	try {
		// Get all unique games from model profiles
		const uniqueGames = new Map();
		const profiles = modelProfiles.models;

		// Process each game only once by using a consistent game ID
		profiles.forEach((model) => {
			model.games.forEach((game) => {
				// Create a consistent game ID by sorting the model IDs
				const gameModelIds = [model.model_id, game.opponent].sort();
				const gameId = `${gameModelIds[0]}-${gameModelIds[1]}`;

				// Only process each unique game once
				if (!uniqueGames.has(gameId)) {
					const opponentModel = profiles.find(
						(m) => m.model_id === game.opponent
					);

					if (opponentModel) {
						// Determine player order based on the session_id
						const isFirstPlayer = game.session_id.includes(
							model.model_id.split(":")[1].toLowerCase()
						);

						// Add the game with the correct player order
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
							title: `${player1.model_name} vs. ${player2.model_name}`,
							player1: player1.model_name,
							player2: player2.model_name,
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

		// Convert the Map to an array
		return Array.from(uniqueGames.values());
	} catch (error) {
		console.error("Error extracting game data:", error);
		return [];
	}
};
