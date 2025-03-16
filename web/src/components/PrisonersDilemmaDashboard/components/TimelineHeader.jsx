import React from "react";
import { shortenModelName } from "@/utils/commonUtils";

export const TimelineHeader = ({ gameDetail, leftModel, rightModel }) => {
	if (!gameDetail || !gameDetail.game) return null;

	const { game } = gameDetail;
	const sessionId = game.session_id;

	// Find the players by model ID
	const getPlayerId = (modelId) => {
		return game.players?.find((p) => p.model_id === modelId)?.id;
	};

	const leftPlayerId = getPlayerId(leftModel.id);
	const rightPlayerId = getPlayerId(rightModel.id);

	// Get final scores
	const leftScore =
		leftPlayerId && game.final_scores
			? game.final_scores[leftPlayerId]
			: null;
	const rightScore =
		rightPlayerId && game.final_scores
			? game.final_scores[rightPlayerId]
			: null;

	// Determine game outcome
	const isTie = leftScore === rightScore;
	const isLeftWinner = game.winner === leftPlayerId;

	return (
		<div className="border border-gray-200 rounded-md p-4 bg-gray-50">
			<h3 className="text-xl font-bold mb-2">
				{shortenModelName(leftModel.name)} vs{" "}
				{shortenModelName(rightModel.name)}
			</h3>
			<div className="text-sm text-gray-600">
				<p className="flex justify-between">
					<span>
						Final score: {shortenModelName(leftModel.name)}{" "}
						{leftScore !== null ? leftScore : "?"} -{" "}
						{rightScore !== null ? rightScore : "?"}{" "}
						{shortenModelName(rightModel.name)}
					</span>
					{leftScore !== null &&
						rightScore !== null &&
						(isTie ? (
							<span className="px-2 py-1 bg-gray-200 text-gray-800 rounded-md text-xs">
								Tie game
							</span>
						) : (
							<span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-md text-xs">
								{isLeftWinner
									? shortenModelName(leftModel.name)
									: shortenModelName(rightModel.name)}{" "}
								won
							</span>
						))}
				</p>
			</div>
		</div>
	);
};
