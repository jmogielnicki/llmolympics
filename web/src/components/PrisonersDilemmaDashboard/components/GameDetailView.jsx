import React from "react";

/**
 * Component to display detailed game information
 *
 * @param {Object} props
 * @param {Object} props.matchup - The selected matchup data
 * @param {Object} props.gameDetail - The detailed game data
 * @param {boolean} props.isLoading - Whether the game details are loading
 */
const GameDetailView = ({ matchup, gameDetail, isLoading }) => {
	if (isLoading) {
		return (
			<div className="flex items-center justify-center p-12">
				<div className="text-center">
					<div
						className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]"
						role="status"
					>
						<span className="!absolute !-m-px !h-px !w-px !overflow-hidden !whitespace-nowrap !border-0 !p-0 ![clip:rect(0,0,0,0)]">
							Loading...
						</span>
					</div>
					<p className="mt-2 text-gray-600">
						Loading game details...
					</p>
				</div>
			</div>
		);
	}

	if (!matchup) {
		return (
			<div className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-center">
				<p>No matchup data available</p>
			</div>
		);
	}

	// Show matchup header
	return (
		<div>
			<div className="flex justify-between items-center mb-4">
				<div>
					<h3 className="text-lg font-medium">{matchup.title}</h3>
					<p className="text-sm text-gray-500">
						Session ID: {matchup.session_id || "Not available"}
					</p>
					<p className="text-sm text-gray-500">
						Final score: {matchup.player1}{" "}
						{matchup.finalScore.player1} -{" "}
						{matchup.finalScore.player2} {matchup.player2}
					</p>
				</div>
				<div className="text-sm px-3 py-1 rounded-full bg-gray-100">
					{matchup.finalScore.player1 > matchup.finalScore.player2
						? `${matchup.player1} wins`
						: matchup.finalScore.player1 <
						  matchup.finalScore.player2
						? `${matchup.player2} wins`
						: "Tie game"}
				</div>
			</div>

			{!gameDetail ? (
				<div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
					<p className="mb-4">
						No detailed timeline data available for this game.
					</p>
				</div>
			) : (
				<GameRounds gameDetail={gameDetail} />
			)}
		</div>
	);
};

/**
 * Component to display rounds in a game
 *
 * @param {Object} props
 * @param {Object} props.gameDetail - The detailed game data
 */
const GameRounds = ({ gameDetail }) => {
	// Group timeline items by round for cleaner display
	// Extract player decision events from the timeline
	const playerDecisionEvents = gameDetail.timeline.filter(
		(item) => item.type === "player_decision"
	);

	// Group decisions by round
	const roundsData = {};
	playerDecisionEvents.forEach((item) => {
		if (!roundsData[item.round]) {
			roundsData[item.round] = {
				decisions: {},
			};
		}
		roundsData[item.round].decisions[item.player_id] = item;
	});

	// Add resolution events to round data
	gameDetail.timeline
		.filter((item) => item.type === "round_resolution")
		.forEach((item) => {
			if (roundsData[item.round]) {
				roundsData[item.round].resolution = item;
			}
		});

	// Convert to sorted array
	const rounds = Object.entries(roundsData)
		.sort(([a], [b]) => Number(a) - Number(b))
		.map(([roundNumber, roundData]) => ({ roundNumber, ...roundData }));

	return (
		<div className="space-y-6">
			{rounds.map((round) => (
				<RoundDetail
					key={round.roundNumber}
					round={round}
					gameDetail={gameDetail}
				/>
			))}
		</div>
	);
};

/**
 * Component to display a single round's details
 *
 * @param {Object} props
 * @param {Object} props.round - The round data
 * @param {Object} props.gameDetail - The complete game detail data
 */
const RoundDetail = ({ round, gameDetail }) => {
	const { roundNumber, decisions, resolution } = round;

	// Find all player decisions for this round
	const playerDecisions = Object.values(decisions || {});

	return (
		<div className="border border-gray-200 rounded-lg overflow-hidden">
			<div className="bg-gray-50 px-4 py-2 flex justify-between items-center">
				<h4 className="font-medium">Round {roundNumber}</h4>
				{resolution && (
					<div className="text-sm text-gray-600">
						Score:{" "}
						{Object.entries(resolution.scores || {})
							.map(([id, score]) => {
								const player = gameDetail.game.players.find(
									(p) => p.id === id
								);
								return `${player?.model_name || id}: ${score}`;
							})
							.join(" - ")}
					</div>
				)}
			</div>

			<div className="grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-gray-200">
				{playerDecisions.map((decisionEvent, idx) => (
					<div key={idx} className="p-4">
						<div className="flex items-center gap-2 mb-2">
							<div
								className={`w-3 h-3 rounded-full ${
									decisionEvent.decision_context?.css_class ||
									(decisionEvent.decision === "cooperate"
										? "bg-green-500"
										: "bg-red-500")
								}`}
							></div>
							<h5 className="font-medium">
								{decisionEvent.model_name}
							</h5>
							<span className="text-sm text-gray-500 ml-auto">
								{decisionEvent.decision_context?.display_text ||
									(decisionEvent.decision === "cooperate"
										? "Cooperated"
										: "Defected")}
							</span>
						</div>
						<p className="text-sm text-gray-600">
							{decisionEvent.reasoning}
						</p>
					</div>
				))}
			</div>
		</div>
	);
};

export default GameDetailView;
