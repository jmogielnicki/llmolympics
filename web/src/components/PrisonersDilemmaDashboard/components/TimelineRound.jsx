import React from "react";
import { PlayerDecision } from "./PlayerDecision";

export const TimelineRound = ({
	round,
	leftModelId,
	rightModelId,
	leftModelName,
	rightModelName,
}) => {
	if (!round) return null;

	// Find decision events for each model
	const leftModelDecision = round.decisions.find(
		(d) => d.model_id === leftModelId
	);

	const rightModelDecision = round.decisions.find(
		(d) => d.model_id === rightModelId
	);

	// Get scores for this round
	const roundScore = round.score || {};
	const leftPlayerId = leftModelDecision?.player_id;
	const rightPlayerId = rightModelDecision?.player_id;
	const leftPlayerScore = leftPlayerId && roundScore[leftPlayerId];
	const rightPlayerScore = rightPlayerId && roundScore[rightPlayerId];

	// Format the score display
	const scoreDisplay =
		leftPlayerScore !== undefined && rightPlayerScore !== undefined
			? `Score: ${leftModelName}: ${leftPlayerScore} - ${rightModelName}: ${rightPlayerScore}`
			: "";

    const bothDecisionsLoaded = leftModelDecision && rightModelDecision;

    if (!bothDecisionsLoaded) {
        return null;
    }

	return (
		<div className="mb-6">
			<div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1 sm:gap-0 mb-2">
				<h4 className="text-lg font-semibold">
					Round {round.roundNumber}
				</h4>
				{scoreDisplay && (
					<span className="text-sm text-gray-600">
						{scoreDisplay}
					</span>
				)}
			</div>

			<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
				{bothDecisionsLoaded && (
					<PlayerDecision
						modelName={leftModelName}
						decision={leftModelDecision}
					/>
				)}

				{bothDecisionsLoaded && (
					<PlayerDecision
						modelName={rightModelName}
						decision={rightModelDecision}
					/>
				)}
			</div>
		</div>
	);
};
