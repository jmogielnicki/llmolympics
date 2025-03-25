import React, { useState, useEffect } from "react";
import { useGameData } from "../../../context/GameDataContext";
import { TimelineHeader } from "../components/TimelineHeader";
import { TimelineRound } from "../components/TimelineRound";
import { shortenModelName } from "@/utils/commonUtils";
import { useParams, useNavigate, useLocation } from "react-router-dom";

const TimelineTab = () => {
	const { gameSessions, loadGameDetail } = useGameData();
	const [gameDetail, setGameDetail] = useState(null);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState(null);

	// Get model IDs from URL params
	const { leftModelId, rightModelId } = useParams();
	const navigate = useNavigate();
	const location = useLocation();

	// Handle model initialization and URL updates
	useEffect(() => {
		if (
			!gameSessions ||
			!Array.isArray(gameSessions) ||
			gameSessions.length === 0
		) {
			return; // Wait for sessions to load
		}

		// If we're on the base timeline path without model IDs
		if (location.pathname === "/games/prisoners-dilemma/timeline") {
			// Navigate to the first matchup
			const firstMatchup = gameSessions[0];
			navigate(
				`/games/prisoners-dilemma/timeline/${firstMatchup.player1_id}/${firstMatchup.player2_id}`,
				{ replace: true }
			);
			return;
		}

		// If we have model IDs in the URL
		if (leftModelId && rightModelId) {
			// Check if it's a valid matchup
			const isValidMatchup = gameSessions.some(
				(matchup) =>
					(matchup.player1_id === leftModelId &&
						matchup.player2_id === rightModelId) ||
					(matchup.player1_id === rightModelId &&
						matchup.player2_id === leftModelId)
			);

			if (isValidMatchup) {
				// Load this matchup
				loadMatchupDetails(leftModelId, rightModelId);
			} else {
				// Invalid matchup - redirect to first matchup with error message
				setError(
					`Invalid model matchup. Redirecting to a valid matchup.`
				);
				const firstMatchup = gameSessions[0];
				navigate(
					`/games/prisoners-dilemma/timeline/${firstMatchup.player1_id}/${firstMatchup.player2_id}`,
					{ replace: true }
				);
			}
		}
	}, [gameSessions, leftModelId, rightModelId, navigate, location.pathname]);

	// Function to load matchup details
	const loadMatchupDetails = async (leftId, rightId) => {
		if (!leftId || !rightId) return;

		setLoading(true);
		setError(null);

		// Find the current matchup based on selected models
		const currentMatchup = gameSessions?.find(
			(matchup) =>
				(matchup?.player1_id === leftId &&
					matchup?.player2_id === rightId) ||
				(matchup?.player1_id === rightId &&
					matchup?.player2_id === leftId)
		);

		if (!currentMatchup?.session_id) {
			setLoading(false);
			setError("Matchup not found.");
			return;
		}

		try {
			const detail = await loadGameDetail(currentMatchup.session_id);
			setGameDetail(detail);
		} catch (err) {
			console.error("Error loading game detail:", err);
			setError("Failed to load game details. Please try again.");
		} finally {
			setLoading(false);
		}
	};

	// Handle model selection change
	const handleLeftModelChange = (newLeftModelId) => {
		navigate(
			`/games/prisoners-dilemma/timeline/${newLeftModelId}/${rightModelId}`
		);
	};

	const handleRightModelChange = (newRightModelId) => {
		navigate(
			`/games/prisoners-dilemma/timeline/${leftModelId}/${newRightModelId}`
		);
	};

	// Get timeline events and organize by rounds
	const getRoundEvents = () => {
		if (!gameDetail?.timeline) return [];

		const rounds = [];
		let currentRound = null;
		let currentRoundIndex = -1;

		for (const event of gameDetail.timeline) {
			if (event.type === "round_start") {
				currentRound = {
					roundNumber: event.round,
					decisions: [],
					score: null,
				};
				rounds.push(currentRound);
				currentRoundIndex = rounds.length - 1;
			} else if (
				event.type === "player_decision" &&
				currentRoundIndex >= 0
			) {
				rounds[currentRoundIndex].decisions.push(event);
			} else if (
				event.type === "round_resolution" &&
				currentRoundIndex >= 0
			) {
				rounds[currentRoundIndex].score = event.scores;
			}
		}

		return rounds;
	};

	const roundEvents = getRoundEvents();

	// Get the list of unique models from gameSessions
	const getUniqueModels = () => {
		if (!gameSessions || !Array.isArray(gameSessions)) return [];

		const models = new Set();
		gameSessions.forEach((matchup) => {
			if (matchup?.player1_id) models.add(matchup.player1_id);
			if (matchup?.player2_id) models.add(matchup.player2_id);
		});

		return Array.from(models);
	};

	const modelOptions = getUniqueModels().map((modelId) => {
		const matchup = gameSessions?.find(
			(m) => m?.player1_id === modelId || m?.player2_id === modelId
		);

		let modelName = "Unknown Model";
		if (matchup?.player1_id === modelId) {
			modelName = matchup.player1;
		} else if (matchup?.player2_id === modelId) {
			modelName = matchup.player2;
		}

		return {
			id: modelId,
			name: modelName,
		};
	});

	// Create left and right model objects for the TimelineHeader
	const createModelObject = (modelId, modelName) => {
		return {
			id: modelId,
			name: modelName,
		};
	};

	const leftModel = createModelObject(
		leftModelId,
		modelOptions.find((m) => m.id === leftModelId)?.name || "Unknown"
	);

	const rightModel = createModelObject(
		rightModelId,
		modelOptions.find((m) => m.id === rightModelId)?.name || "Unknown"
	);

	return (
		<div className="w-full max-w-4xl mx-auto">
			<div className="mb-8 mt-4">
				<h2 className="text-xl font-bold text-center mb-1">
					Individual Matches
				</h2>
				<p className="text-sm text-center text-gray-600 mb-6">
					Detailed progression of individual sessions with
					decisions and reasoning
				</p>

				<div className="flex flex-col md:flex-row gap-2 md:gap-4 mb-4">
					<div className="w-full md:w-1/2">
						<select
							className="w-full border border-gray-300 rounded-md p-2"
							value={leftModelId || ""}
							onChange={(e) =>
								handleLeftModelChange(e.target.value)
							}
						>
							{modelOptions
								.filter((model) => model.id !== rightModelId)
								.map((model) => (
									<option key={model.id} value={model.id}>
										{shortenModelName(model.name)}
									</option>
								))}
						</select>
					</div>

					<div className="flex items-center justify-center">
						<span className="text-gray-500">vs</span>
					</div>

					<div className="w-full md:w-1/2">
						<select
							className="w-full border border-gray-300 rounded-md p-2"
							value={rightModelId || ""}
							onChange={(e) =>
								handleRightModelChange(e.target.value)
							}
						>
							{modelOptions
								.filter((model) => model.id !== leftModelId)
								.map((model) => (
									<option key={model.id} value={model.id}>
										{shortenModelName(model.name)}
									</option>
								))}
						</select>
					</div>
				</div>

				{error && <p className="text-center text-red-500">{error}</p>}

				{gameDetail && (
					<>
						<TimelineHeader
							gameDetail={gameDetail}
							leftModel={leftModel}
							rightModel={rightModel}
						/>
						{loading && (
							<div className="mt-20 mb-20">
								<p className="text-center">
									Loading game details...
								</p>
								<div className="h-200"></div>
							</div>
						)}
						<div className="mt-4">
							{roundEvents.map((round) => (
								<TimelineRound
									key={`round-${round.roundNumber}`}
									round={round}
									leftModelId={leftModelId}
									rightModelId={rightModelId}
									leftModelName={shortenModelName(
										leftModel.name
									)}
									rightModelName={shortenModelName(
										rightModel.name
									)}
								/>
							))}
						</div>
					</>
				)}
			</div>
		</div>
	);
};

export default TimelineTab;
