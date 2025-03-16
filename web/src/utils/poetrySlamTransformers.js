// poetrySlamTransformers.js
import { shortenModelName } from "./commonTransformers";

export const transformLeaderboardData = (data) => {
	return data.leaderboard.map((model) => ({
		...model,
		model_name: shortenModelName(model.model_name),
	}));
};

export const extractGameSessions = (modelProfiles) => {
	// Process all games from model profiles
	// Create a list of unique game sessions with metadata
	const sessions = [];
	const processedSessions = new Set();

	modelProfiles.models.forEach((model) => {
		model.games.forEach((game) => {
			if (!processedSessions.has(game.session_id)) {
				processedSessions.add(game.session_id);

				// Extract participants
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
};

export const createVotingPatterns = (_, modelProfiles) => {
	// Create voting matrix - who votes for whom
	const votingMatrix = {};
	const models = modelProfiles.models.map((m) => ({
		id: m.model_id,
		name: shortenModelName(m.model_name),
	}));

	// Initialize the matrix
	models.forEach((voter) => {
		votingMatrix[voter.id] = {};
		models.forEach((candidate) => {
			votingMatrix[voter.id][candidate.id] = 0;
		});
	});

	// Count votes
	models.forEach((model) => {
		model.games.forEach((game) => {
			if (
				game.voting &&
				game.voting.voted_for &&
				game.other_players.includes(game.voting.voted_for)
			) {
				votingMatrix[model.id][game.voting.voted_for]++;
			}
		});
	});

	return {
		matrix: votingMatrix,
		models: models,
	};
};

// Extract poems from game detail
export const extractPoems = (gameDetail) => {
	if (!gameDetail || !gameDetail.timeline) return [];

	// Find poem submissions
	const poemSubmissions = gameDetail.timeline.filter(
		(item) => item.type === "poem_submission"
	);

	// Get vote counts for each player
	const voteCount = {};
	gameDetail.timeline
		.filter((item) => item.type === "player_vote")
		.forEach((vote) => {
			if (!voteCount[vote.voted_for]) voteCount[vote.voted_for] = 0;
			voteCount[vote.voted_for]++;
		});

	// Find winner(s)
	const winners = gameDetail.game?.winner ? [gameDetail.game.winner] : [];

	return poemSubmissions.map((submission) => ({
		id: submission.player_id,
		text: submission.poem.replace(/\[\[|\]\]/g, ""), // Remove [[ ]] delimiters
		author: submission.model_name,
		votes: voteCount[submission.player_id] || 0,
		isWinner: winners.includes(submission.player_id),
	}));
};

// Extract prompt from game detail
export const extractPrompt = (gameDetail) => {
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
};
