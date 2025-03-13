import React, { useState, useEffect } from "react";
import { useGameData } from "../context/GameDataContext";
import { TimelineHeader } from "../components/TimelineHeader";
import { TimelineRound } from "../components/TimelineRound";
import { shortenModelName } from "../utils/dataTransformers";

const TimelineTab = () => {
	const { matchups, loadGameDetail } = useGameData();

	const [selectedLeftModel, setSelectedLeftModel] = useState("");
	const [selectedRightModel, setSelectedRightModel] = useState("");
	const [gameDetail, setGameDetail] = useState(null);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState(null);

	// Initialize selected models when matchups are loaded
	useEffect(() => {
		if (matchups && Array.isArray(matchups) && matchups.length > 0) {
			// Use the first matchup's model IDs
			const firstMatchup = matchups[0];
			setSelectedLeftModel(firstMatchup.player1_id);
			setSelectedRightModel(firstMatchup.player2_id);
		}
	}, [matchups]);

	// Find the current matchup based on selected models
	const currentMatchup = matchups?.find(
		(matchup) =>
			(matchup?.player1_id === selectedLeftModel &&
				matchup?.player2_id === selectedRightModel) ||
			(matchup?.player1_id === selectedRightModel &&
				matchup?.player2_id === selectedLeftModel)
	);

	// Load game detail when matchup changes
	useEffect(() => {
		const fetchGameDetail = async () => {
			if (!currentMatchup?.session_id) return;

			setLoading(true);
			setError(null);

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

		fetchGameDetail();
	}, [currentMatchup, loadGameDetail]);

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

	// Handle model selection change
	const handleLeftModelChange = (e) => {
		setSelectedLeftModel(e.target.value);
	};

	const handleRightModelChange = (e) => {
		setSelectedRightModel(e.target.value);
	};

	// Get the list of unique models from matchups
	const getUniqueModels = () => {
		if (!matchups || !Array.isArray(matchups)) return [];

		const models = new Set();
		matchups.forEach((matchup) => {
			if (matchup?.player1_id) models.add(matchup.player1_id);
			if (matchup?.player2_id) models.add(matchup.player2_id);
		});

		return Array.from(models);
	};

	const modelOptions = getUniqueModels().map((modelId) => {
		const matchup = matchups?.find(
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
		selectedLeftModel,
		modelOptions.find((m) => m.id === selectedLeftModel)?.name || "Unknown"
	);

	const rightModel = createModelObject(
		selectedRightModel,
		modelOptions.find((m) => m.id === selectedRightModel)?.name || "Unknown"
	);

	return (
		<div className="w-full max-w-4xl mx-auto">
			<div className="mb-8">
				<h2 className="text-2xl font-bold text-center mb-1">
					Game Timeline View
				</h2>
				<p className="text-center text-gray-600 mb-6">
					Detailed progression of individual matchups with decisions
					and reasoning
				</p>

				<div className="flex flex-col md:flex-row gap-2 md:gap-4 mb-4">
					<div className="w-full md:w-1/2">
						<select
							className="w-full border border-gray-300 rounded-md p-2"
							value={selectedLeftModel}
							onChange={handleLeftModelChange}
						>
							{modelOptions
								.filter(
									(model) => model.id !== selectedRightModel
								)
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
							value={selectedRightModel}
							onChange={handleRightModelChange}
						>
							{modelOptions
								.filter(
									(model) => model.id !== selectedLeftModel
								)
								.map((model) => (
									<option key={model.id} value={model.id}>
										{shortenModelName(model.name)}
									</option>
								))}
						</select>
					</div>
				</div>

				{error && <p className="text-center text-red-500">{error}</p>}

				{gameDetail && currentMatchup && (
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
									leftModelId={selectedLeftModel}
									rightModelId={selectedRightModel}
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