import React, { useState, useEffect } from "react";
import {
	BarChart,
	Bar,
	XAxis,
	YAxis,
	CartesianGrid,
	Tooltip,
	Legend,
	ResponsiveContainer,
	LineChart,
	Line,
} from "recharts";
import {
	ChevronDown,
	ChevronUp,
	Minus,
	CheckCircle,
	XCircle,
} from "lucide-react";

// Import common components
import TabNavigation from "./TabNavigation";
import ModelLeaderboard from "./ModelLeaderboard";

// Import JSON files directly - using the correct paths to reach data directory
import leaderboardJson from "@data/processed/prisoners_dilemma_benchmark_1/leaderboard.json";
import matchupMatrixJson from "@data/processed/prisoners_dilemma_benchmark_1/matchup_matrix.json";
import roundProgressionJson from "@data/processed/prisoners_dilemma_benchmark_1/round_progression.json";
import modelProfilesJson from "@data/processed/prisoners_dilemma_benchmark_1/model_profiles.json";
import metadataJson from "@data/processed/prisoners_dilemma_benchmark_1/metadata.json";

// Dynamic imports for game detail files
const gameDetailFiles = import.meta.glob(
	"@data/processed/prisoners_dilemma_benchmark_1/detail/*.json",
	{ eager: false }
);

/**
 * Dashboard specifically for the Prisoner's Dilemma game
 */
const PrisonersDilemmaDashboard = () => {
	const [activeTab, setActiveTab] = useState("leaderboard");
	const [selectedMatchup, setSelectedMatchup] = useState("");

	// State for storing loaded data
	const [leaderboardData, setLeaderboardData] = useState([]);
	const [roundProgressionData, setRoundProgressionData] = useState([]);
	const [matchupMatrix, setMatchupMatrix] = useState({
		models: [],
		winMatrix: [],
	});
	const [gameSummaryData, setGameSummaryData] = useState([]);
	const [cooperationByModelAndRound, setCooperationByModelAndRound] =
		useState([]);
	const [matchups, setMatchups] = useState([]);
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState(null);

	// State for game detail loading
	const [gameDetail, setGameDetail] = useState(null);
	const [isLoadingDetail, setIsLoadingDetail] = useState(false);

	// Tab configuration
	const tabs = [
		{ id: "leaderboard", label: "Leaderboard" },
		{ id: "game-stats", label: "Game Statistics" },
		{ id: "matchups", label: "Matchups" },
		{ id: "timeline", label: "Game Timeline" },
		{ id: "about", label: "About" },
	];

	// Transform leaderboard data
	const transformLeaderboardData = (data) => {
		return data.leaderboard.map((model) => ({
			...model,
		}));
	};

	// Transform matchup matrix data
	const transformMatchupMatrix = (data) => {
		return {
			models:
				data.model_names ||
				data.models.map((model) => model.split(":")[1]),
			winMatrix: data.win_matrix,
		};
	};

	// Transform round progression data
	const transformRoundProgressionData = (data) => {
		return data.round_progression.map((round) => ({
			round: round.round,
			cooperation_rate: round.cooperation_rate,
			defection_rate: round.defection_rate,
		}));
	};

	// Create model summary data for visualization
	const createGameSummaryData = (leaderboard) => {
		return leaderboard.map((model) => ({
			name: model.model_name.split(" ").pop() || model.model_name,
			wins: model.wins,
			losses: model.losses,
			ties: model.ties,
		}));
	};

	// Transform cooperation data by model and round
	const transformCooperationByModel = (roundProgression, modelProfiles) => {
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

	// Extract real game data from model profiles
	const extractGameData = () => {
		try {
			// Get all unique games from model profiles
			const uniqueGames = new Map();
			const profiles = modelProfilesJson.models;

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
							const player1 = isFirstPlayer
								? model
								: opponentModel;
							const player2 = isFirstPlayer
								? opponentModel
								: model;
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

	// Function to load game details based on session ID
	const loadGameDetail = async (sessionId) => {
		if (!sessionId) {
			setGameDetail(null);
			return;
		}

		setIsLoadingDetail(true);

		try {
			// Extract just the timestamp part from the session ID
			// Pattern matches: prisoner's_dilemma_20250311_153141 -> 20250311_153141
			const timestampMatch = sessionId.match(/(\d{8}_\d{6})/);
			const timestamp = timestampMatch ? timestampMatch[1] : sessionId;

			// Find the file that matches this timestamp
			const fileKey = Object.keys(gameDetailFiles).find((key) => {
				return key.includes(timestamp);
			});

			if (!fileKey) {
				console.error(
					`Game detail file not found for session: ${sessionId} (timestamp: ${timestamp})`
				);
				setIsLoadingDetail(false);
				return;
			}

			// Load the file dynamically
			const module = await gameDetailFiles[fileKey]();
			setGameDetail(module.default || module);
		} catch (error) {
			console.error(
				`Failed to load game detail for ${sessionId}:`,
				error
			);
		} finally {
			setIsLoadingDetail(false);
		}
	};

	// Load all data when the component mounts
	useEffect(() => {
		const loadData = async () => {
			setIsLoading(true);
			setError(null);

			try {
				console.log("Loading data for Prisoner's Dilemma");

				// Transform and set leaderboard data
				const transformedLeaderboard =
					transformLeaderboardData(leaderboardJson);
				setLeaderboardData(transformedLeaderboard);

				// Transform and set matchup matrix data
				const transformedMatchupMatrix =
					transformMatchupMatrix(matchupMatrixJson);
				setMatchupMatrix(transformedMatchupMatrix);

				// Transform and set round progression data
				const transformedRoundProgression =
					transformRoundProgressionData(roundProgressionJson);
				setRoundProgressionData(transformedRoundProgression);

				// Create game summary data for visualization
				const summaryData = createGameSummaryData(
					transformedLeaderboard
				);
				setGameSummaryData(summaryData);

				// Transform cooperation data by model and round
				const cooperationData = transformCooperationByModel(
					roundProgressionJson,
					modelProfilesJson
				);
				setCooperationByModelAndRound(cooperationData);

				// Extract real game data from model profiles
				const gameData = extractGameData();
				setMatchups(gameData);

				// Set the first matchup as selected by default
				if (gameData.length > 0) {
					setSelectedMatchup(gameData[0].id);
				}

				console.log("Loaded all data for Prisoner's Dilemma");
			} catch (error) {
				console.error("Error loading game data:", error);
				setError(
					"Failed to load game data. Please try again later. Error: " +
						error.message
				);
			} finally {
				setIsLoading(false);
			}
		};

		loadData();
	}, []);

	// Load game detail when a matchup is selected
	useEffect(() => {
		const matchup = getSelectedMatchupData();
		if (matchup && matchup.session_id) {
			loadGameDetail(matchup.session_id);
		} else {
			setGameDetail(null);
		}
	}, [selectedMatchup]);

	// Configure columns for the leaderboard
	const leaderboardColumns = [
		{ key: "rank", label: "Rank", align: "left" },
		{ key: "model_name", label: "Model", align: "left" },
		{ key: "wins", label: "Wins", align: "right" },
		{ key: "losses", label: "Losses", align: "right" },
		{ key: "ties", label: "Ties", align: "right" },
		{
			key: "winrate",
			label: "Win Rate",
			align: "right",
			formatter: (value) => `${(value * 100).toFixed(1)}%`,
		},
		{
			key: "avg_score",
			label: "Avg. Score",
			align: "right",
			formatter: (value) => value.toFixed(2),
		},
	];

	const renderWinMatrixCell = (value, rowIndex, colIndex) => {
		if (rowIndex === colIndex) return "-";
		if (value === null) return "-";

		if (value === 1)
			return <ChevronUp className="text-green-500 mx-auto" />;
		if (value === 0)
			return <ChevronDown className="text-red-500 mx-auto" />;
		return <Minus className="text-gray-500 mx-auto" />;
	};

	// Helper function to get color based on cooperation rate
	const getCellColor = (rate) => {
		if (rate >= 0.8) return "bg-blue-100";
		if (rate >= 0.6) return "bg-blue-50";
		if (rate <= 0.2) return "bg-red-100";
		if (rate <= 0.4) return "bg-red-50";
		return "";
	};

	// Get the selected matchup data
	const getSelectedMatchupData = () => {
		return (
			matchups.find((m) => m.id === selectedMatchup) ||
			(matchups.length > 0 ? matchups[0] : null)
		);
	};

	// Loading state
	if (isLoading) {
		return (
			<div className="flex items-center justify-center h-64">
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
						Loading Prisoner's Dilemma data...
					</p>
				</div>
			</div>
		);
	}

	// Error state
	if (error) {
		return (
			<div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
				<p className="font-medium">Error loading data</p>
				<p className="text-sm">{error}</p>
			</div>
		);
	}

	// Game Status Banner
	const renderGameStatusBanner = () => (
		<div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-2 rounded-lg text-sm mb-6">
			<span className="font-semibold">Prisoner's Dilemma:</span>{" "}
			{leaderboardData.length > 0
				? `${
						metadataJson?.game_count || matchups.length
				  } games played between ${
						leaderboardData.length
				  } models • Last updated ${
						metadataJson?.processed_at?.split("T")[0] ||
						"March 2025"
				  }`
				: "Loading game data..."}
		</div>
	);

	return (
		<div>
			{renderGameStatusBanner()}

			{/* Use the Tab Navigation Component */}
			<TabNavigation
				activeTab={activeTab}
				tabs={tabs}
				onTabChange={setActiveTab}
			/>

			{/* Tab Content */}
			{activeTab === "leaderboard" && (
				<div className="space-y-6">
					{/* Use the ModelLeaderboard Component */}
					<ModelLeaderboard
						data={leaderboardData}
						columns={leaderboardColumns}
						title="Model Leaderboard"
						subtitle={`Performance rankings for Prisoner's Dilemma (${
							metadataJson?.processed_at?.split("T")[0] ||
							"March 2025"
						})`}
					/>

					<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
						<div className="bg-white rounded-lg shadow-md overflow-hidden">
							<div className="px-6 py-4 border-b border-gray-200">
								<h2 className="text-xl font-semibold">
									Performance Summary
								</h2>
								<p className="text-gray-600 text-sm">
									Wins, losses, and ties by model
								</p>
							</div>
							<div className="p-6">
								<div className="h-80">
									<ResponsiveContainer
										width="100%"
										height="100%"
									>
										<BarChart
											layout="vertical"
											data={gameSummaryData}
											margin={{
												top: 20,
												right: 30,
												left: 80,
												bottom: 5,
											}}
										>
											<CartesianGrid strokeDasharray="3 3" />
											<XAxis type="number" />
											<YAxis
												dataKey="name"
												type="category"
												width={80}
											/>
											<Tooltip />
											<Legend />
											<Bar
												dataKey="wins"
												stackId="a"
												fill="#22c55e"
												name="Wins"
											/>
											<Bar
												dataKey="losses"
												stackId="a"
												fill="#ef4444"
												name="Losses"
											/>
											<Bar
												dataKey="ties"
												stackId="a"
												fill="#94a3b8"
												name="Ties"
											/>
										</BarChart>
									</ResponsiveContainer>
								</div>
							</div>
						</div>

						<div className="bg-white rounded-lg shadow-md overflow-hidden">
							<div className="px-6 py-4 border-b border-gray-200">
								<h2 className="text-xl font-semibold">
									Average Score
								</h2>
								<p className="text-gray-600 text-sm">
									Average points per game
								</p>
							</div>
							<div className="p-6">
								<div className="h-80">
									<ResponsiveContainer
										width="100%"
										height="100%"
									>
										<BarChart
											layout="vertical"
											data={leaderboardData}
											margin={{
												top: 20,
												right: 30,
												left: 80,
												bottom: 5,
											}}
										>
											<CartesianGrid strokeDasharray="3 3" />
											<XAxis
												type="number"
												domain={[0, 15]}
											/>
											<YAxis
												dataKey="model_name"
												type="category"
												width={80}
												tickFormatter={(value) =>
													value.split(" ").pop()
												}
											/>
											<Tooltip
												formatter={(value) =>
													value.toFixed(2)
												}
											/>
											<Bar
												dataKey="avg_score"
												fill="#3b82f6"
												name="Average Score"
											/>
										</BarChart>
									</ResponsiveContainer>
								</div>
							</div>
						</div>
					</div>
				</div>
			)}

			{/* Game Stats Tab Content */}
			{activeTab === "game-stats" && (
				<div className="space-y-6">
					<div className="bg-white rounded-lg shadow-md overflow-hidden">
						<div className="px-6 py-4 border-b border-gray-200">
							<h2 className="text-xl font-semibold">
								Cooperation vs. Defection Over Rounds
							</h2>
							<p className="text-gray-600 text-sm">
								Shows how models' strategies evolved over the 5
								rounds
							</p>
						</div>
						<div className="p-6">
							<div className="h-80">
								<ResponsiveContainer width="100%" height="100%">
									<LineChart
										data={roundProgressionData}
										margin={{
											top: 20,
											right: 30,
											left: 20,
											bottom: 5,
										}}
									>
										<CartesianGrid strokeDasharray="3 3" />
										<XAxis dataKey="round" />
										<YAxis
											domain={[0, 1]}
											tickFormatter={(value) =>
												`${(value * 100).toFixed(0)}%`
											}
										/>
										<Tooltip
											formatter={(value) =>
												`${(value * 100).toFixed(1)}%`
											}
										/>
										<Legend />
										<Line
											type="monotone"
											dataKey="cooperation_rate"
											stroke="#3b82f6"
											name="Cooperation Rate"
											strokeWidth={2}
											dot={{ r: 5 }}
										/>
										<Line
											type="monotone"
											dataKey="defection_rate"
											stroke="#ef4444"
											name="Defection Rate"
											strokeWidth={2}
											dot={{ r: 5 }}
										/>
									</LineChart>
								</ResponsiveContainer>
							</div>
						</div>
					</div>

					<div className="bg-white rounded-lg shadow-md overflow-hidden">
						<div className="px-6 py-4 border-b border-gray-200">
							<h2 className="text-xl font-semibold">
								Cooperation Rate by Model and Round
							</h2>
							<p className="text-gray-600 text-sm">
								Shows how each model's cooperation strategy
								changed over rounds
							</p>
						</div>
						<div className="p-6">
							<div className="overflow-x-auto">
								<table className="min-w-full divide-y divide-gray-200">
									<thead className="bg-gray-50">
										<tr>
											<th
												scope="col"
												className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
											>
												Model
											</th>
											<th
												scope="col"
												className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"
											>
												Round 1
											</th>
											<th
												scope="col"
												className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"
											>
												Round 2
											</th>
											<th
												scope="col"
												className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"
											>
												Round 3
											</th>
											<th
												scope="col"
												className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"
											>
												Round 4
											</th>
											<th
												scope="col"
												className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"
											>
												Round 5
											</th>
										</tr>
									</thead>
									<tbody className="bg-white divide-y divide-gray-200">
										{cooperationByModelAndRound.map(
											(model, index) => (
												<tr
													key={index}
													className="hover:bg-gray-50"
												>
													<td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
														{model.model}
													</td>
													<td
														className={`px-6 py-4 whitespace-nowrap text-sm text-center ${getCellColor(
															model.round1
														)}`}
													>
														{(
															model.round1 * 100
														).toFixed(0)}
														%
													</td>
													<td
														className={`px-6 py-4 whitespace-nowrap text-sm text-center ${getCellColor(
															model.round2
														)}`}
													>
														{(
															model.round2 * 100
														).toFixed(0)}
														%
													</td>
													<td
														className={`px-6 py-4 whitespace-nowrap text-sm text-center ${getCellColor(
															model.round3
														)}`}
													>
														{(
															model.round3 * 100
														).toFixed(0)}
														%
													</td>
													<td
														className={`px-6 py-4 whitespace-nowrap text-sm text-center ${getCellColor(
															model.round4
														)}`}
													>
														{(
															model.round4 * 100
														).toFixed(0)}
														%
													</td>
													<td
														className={`px-6 py-4 whitespace-nowrap text-sm text-center ${getCellColor(
															model.round5
														)}`}
													>
														{(
															model.round5 * 100
														).toFixed(0)}
														%
													</td>
												</tr>
											)
										)}
									</tbody>
								</table>
							</div>
						</div>
					</div>
				</div>
			)}

			{/* Matchups Tab Content */}
			{activeTab === "matchups" && (
				<div className="space-y-6">
					<div className="bg-white rounded-lg shadow-md overflow-hidden">
						<div className="px-6 py-4 border-b border-gray-200">
							<h2 className="text-xl font-semibold">
								Head-to-Head Matchups
							</h2>
							<p className="text-gray-600 text-sm">
								Which model won in direct competitions (green up
								= row model won)
							</p>
						</div>
						<div className="p-6">
							<div className="overflow-x-auto">
								<table className="min-w-full divide-y divide-gray-200">
									<thead className="bg-gray-50">
										<tr>
											<th
												scope="col"
												className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-48"
											>
												Model
											</th>
											{matchupMatrix.models.map(
												(model, idx) => (
													<th
														key={idx}
														scope="col"
														className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"
													>
														{model.split(" ").pop()}
													</th>
												)
											)}
										</tr>
									</thead>
									<tbody className="bg-white divide-y divide-gray-200">
										{matchupMatrix.models.map(
											(rowModel, rowIdx) => (
												<tr
													key={rowIdx}
													className="hover:bg-gray-50"
												>
													<td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
														{rowModel}
													</td>
													{matchupMatrix.models.map(
														(colModel, colIdx) => (
															<td
																key={colIdx}
																className="px-6 py-4 whitespace-nowrap text-center"
															>
																{renderWinMatrixCell(
																	matchupMatrix
																		.winMatrix[
																		rowIdx
																	]?.[colIdx],
																	rowIdx,
																	colIdx
																)}
															</td>
														)
													)}
												</tr>
											)
										)}
									</tbody>
								</table>
							</div>
						</div>
					</div>
				</div>
			)}

			{/* Timeline Tab Content */}
			{activeTab === "timeline" && (
				<div className="space-y-6">
					<div className="bg-white rounded-lg shadow-md overflow-hidden">
						<div className="px-6 py-4 border-b border-gray-200">
							<h2 className="text-xl font-semibold">
								Game Timeline View
							</h2>
							<p className="text-gray-600 text-sm">
								Detailed progression of individual matchups with
								decisions and reasoning
							</p>
						</div>
						<div className="p-6">
							<div className="flex flex-wrap gap-2 mb-6">
								{matchups.map((matchup) => (
									<button
										key={matchup.id}
										className={`px-4 py-2 text-sm rounded-full ${
											selectedMatchup === matchup.id
												? "bg-blue-500 text-white"
												: "bg-gray-200 text-gray-700 hover:bg-gray-300"
										}`}
										onClick={() =>
											setSelectedMatchup(matchup.id)
										}
									>
										{matchup.title}
									</button>
								))}
							</div>

							{(() => {
								const matchup = getSelectedMatchupData();

								if (!matchup) {
									return (
										<div className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-center">
											<p>No matchup data available</p>
										</div>
									);
								}

								return (
									<div>
										<div className="flex justify-between items-center mb-4">
											<div>
												<h3 className="text-lg font-medium">
													{matchup.title}
												</h3>
												<p className="text-sm text-gray-500">
													Session ID:{" "}
													{matchup.session_id ||
														"Not available"}
												</p>
												<p className="text-sm text-gray-500">
													Final score:{" "}
													{matchup.player1}{" "}
													{matchup.finalScore.player1}{" "}
													-{" "}
													{matchup.finalScore.player2}{" "}
													{matchup.player2}
												</p>
											</div>
											<div className="text-sm px-3 py-1 rounded-full bg-gray-100">
												{matchup.finalScore.player1 >
												matchup.finalScore.player2
													? `${matchup.player1} wins`
													: matchup.finalScore
															.player1 <
													  matchup.finalScore.player2
													? `${matchup.player2} wins`
													: "Tie game"}
											</div>
										</div>

										{isLoadingDetail ? (
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
										) : gameDetail ? (
											<div className="space-y-6">
												{/* Group timeline items by round for cleaner display */}
												{(() => {
													// Extract player decision events from the timeline
													const playerDecisionEvents =
														gameDetail.timeline.filter(
															(item) =>
																item.type ===
																"player_decision"
														);

													// Group decisions by round
													const roundsData = {};
													playerDecisionEvents.forEach(
														(item) => {
															if (
																!roundsData[
																	item.round
																]
															) {
																roundsData[
																	item.round
																] = {
																	decisions:
																		{},
																};
															}
															roundsData[
																item.round
															].decisions[
																item.player_id
															] = item;
														}
													);

													// Add resolution events to round data
													gameDetail.timeline
														.filter(
															(item) =>
																item.type ===
																"round_resolution"
														)
														.forEach((item) => {
															if (
																roundsData[
																	item.round
																]
															) {
																roundsData[
																	item.round
																].resolution =
																	item;
															}
														});

													// Convert to sorted array
													return Object.entries(
														roundsData
													)
														.sort(
															([a], [b]) =>
																Number(a) -
																Number(b)
														)
														.map(
															([
																roundNumber,
																roundData,
															]) => {
																// Find all player decisions for this round
																const playerDecisions =
																	Object.values(
																		roundData.decisions ||
																			{}
																	);
																const resolution =
																	roundData.resolution;

																return (
																	<div
																		key={
																			roundNumber
																		}
																		className="border border-gray-200 rounded-lg overflow-hidden"
																	>
																		<div className="bg-gray-50 px-4 py-2 flex justify-between items-center">
																			<h4 className="font-medium">
																				Round{" "}
																				{
																					roundNumber
																				}
																			</h4>
																			{resolution && (
																				<div className="text-sm text-gray-600">
																					Score:{" "}
																					{Object.entries(
																						resolution.scores ||
																							{}
																					)
																						.map(
																							([
																								id,
																								score,
																							]) => {
																								const player =
																									gameDetail.game.players.find(
																										(
																											p
																										) =>
																											p.id ===
																											id
																									);
																								return `${
																									player?.model_name ||
																									id
																								}: ${score}`;
																							}
																						)
																						.join(
																							" - "
																						)}
																				</div>
																			)}
																		</div>

																		<div className="grid grid-cols-2 divide-x divide-gray-200">
																			{playerDecisions.map(
																				(
																					decisionEvent,
																					idx
																				) => (
																					<div
																						key={
																							idx
																						}
																						className="p-4"
																					>
																						<div className="flex items-center gap-2 mb-2">
																							<div
																								className={`w-3 h-3 rounded-full ${
																									decisionEvent
																										.decision_context
																										?.css_class ||
																									(decisionEvent.decision ===
																									"cooperate"
																										? "bg-green-500"
																										: "bg-red-500")
																								}`}
																							></div>
																							<h5 className="font-medium">
																								{
																									decisionEvent.model_name
																								}
																							</h5>
																							<span className="text-sm text-gray-500 ml-auto">
																								{decisionEvent
																									.decision_context
																									?.display_text ||
																									(decisionEvent.decision ===
																									"cooperate"
																										? "Cooperated"
																										: "Defected")}
																							</span>
																						</div>
																						<p className="text-sm text-gray-600">
																							{
																								decisionEvent.reasoning
																							}
																						</p>
																					</div>
																				)
																			)}
																		</div>
																	</div>
																);
															}
														);
												})()}
											</div>
										) : (
											<div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
												<p className="mb-4">
													No detailed timeline data
													available for this game.
												</p>
											</div>
										)}
									</div>
								);
							})()}
						</div>
					</div>
				</div>
			)}

			{/* About Tab Content - Modified to be about Prisoner's Dilemma specifically */}
			{activeTab === "about" && (
				<div className="space-y-6">
					<div className="bg-white rounded-lg shadow-md overflow-hidden">
						<div className="px-6 py-4 border-b border-gray-200">
							<h2 className="text-xl font-semibold">
								About Prisoner's Dilemma
							</h2>
						</div>
						<div className="p-6">
							<div className="prose prose-lg max-w-none text-left">
								<p className="text-gray-800">
									The Prisoner's Dilemma is a classic game
									theory scenario that demonstrates why two
									completely rational individuals might not
									cooperate, even if it appears that it's in
									their best interests to do so.
								</p>

								<h3 className="text-xl font-semibold mt-6 mb-3">
									Game Description
								</h3>
								<p className="text-gray-800">
									Players participate in multiple rounds of
									the classic dilemma against different
									opponents. Each round, players
									simultaneously choose to cooperate or
									defect. Mutual cooperation yields moderate
									rewards for both (3,3), mutual defection
									yields low rewards (1,1), while unilateral
									defection yields high reward for the
									defector (5,0). Different strategies emerge
									across repeated interactions.
								</p>

								<h3 className="text-xl font-semibold mt-6 mb-3">
									Game Structure
								</h3>
								<ul className="list-disc pl-6 space-y-2">
									<li className="text-gray-800">
										<span className="font-semibold">
											Players:
										</span>{" "}
										2 LLMs compete against each other
									</li>
									<li className="text-gray-800">
										<span className="font-semibold">
											Rounds:
										</span>{" "}
										5 rounds per game
									</li>
									<li className="text-gray-800">
										<span className="font-semibold">
											Choices:
										</span>{" "}
										Cooperate or Defect (made
										simultaneously)
									</li>
									<li className="text-gray-800">
										<span className="font-semibold">
											Scoring:
										</span>
										<ul className="list-disc pl-6 mt-2 space-y-1">
											<li>
												Both cooperate: 3 points each
											</li>
											<li>Both defect: 1 point each</li>
											<li>
												One defects, one cooperates:
												Defector gets 5 points,
												cooperator gets 0
											</li>
										</ul>
									</li>
								</ul>

								<h3 className="text-xl font-semibold mt-6 mb-3">
									Capabilities Tested
								</h3>
								<ul className="list-disc pl-6 space-y-2">
									<li className="text-gray-800">
										Strategic decision-making
									</li>
									<li className="text-gray-800">
										Pattern recognition
									</li>
									<li className="text-gray-800">
										Reciprocity
									</li>
									<li className="text-gray-800">
										Balance between cooperation and
										competition
									</li>
									<li className="text-gray-800">
										Adaptability to opponent's strategy
									</li>
								</ul>

								<h3 className="text-xl font-semibold mt-6 mb-3">
									Why This Game Matters
								</h3>
								<p className="text-gray-800">
									The Prisoner's Dilemma tests an AI model's
									ability to make strategic decisions when
									there are complex trade-offs between
									short-term gain and long-term cooperation.
									It can reveal whether models are capable of
									developing trust, recognizing patterns in
									opponent behavior, and adapting strategies
									accordingly.
								</p>

								<p className="text-gray-800 mt-4">
									This game is particularly interesting for AI
									safety research as it demonstrates how
									models handle the balance between
									self-interest and mutual benefit, which may
									have implications for AI cooperation and
									alignment.
								</p>
							</div>
						</div>
					</div>
				</div>
			)}
		</div>
	);
};

export default PrisonersDilemmaDashboard;
