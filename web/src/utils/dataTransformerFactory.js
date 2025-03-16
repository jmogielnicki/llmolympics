// dataTransformerFactory.js
import * as prisonersDilemmaTransformers from "./prisonersDilemmaTransformers";
import * as poetrySlamTransformers from "./poetrySlamTransformers";
import { shortenModelName } from "@/utils/commonUtils";

// Common transformer functions shared across games
export const commonTransformers = {
	shortenModelName,
};

// Factory function to get game-specific transformers
export const getGameSpecificTransformers = (gameType) => {
	const transformers = {
		prisoners_dilemma: {
			transformLeaderboard:
				prisonersDilemmaTransformers.transformLeaderboardData,
			extractGameSessions: prisonersDilemmaTransformers.extractGameData,
			gameSpecific: {
				matchupMatrix:
					prisonersDilemmaTransformers.transformMatchupMatrix,
				roundProgression:
					prisonersDilemmaTransformers.transformRoundProgressionData,
				gameSummary: prisonersDilemmaTransformers.createGameSummaryData,
				cooperationByModel:
					prisonersDilemmaTransformers.transformCooperationByModel,
			},
		},
		poetry_slam: {
			transformLeaderboard:
				poetrySlamTransformers.transformLeaderboardData,
			extractGameSessions: poetrySlamTransformers.extractGameSessions,
			gameSpecific: {
				votingPatterns: poetrySlamTransformers.createVotingPatterns,
			},
		},
	};

	return transformers[gameType] || {};
};
