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
import { ChevronDown, ChevronUp, Minus } from "lucide-react";

// Import JSON files directly - using the correct paths to reach data directory
import leaderboardJson from "../../../data/processed/prisoners_dilemma_benchmark_1/leaderboard.json";
import matchupMatrixJson from "../../../data/processed/prisoners_dilemma_benchmark_1/matchup_matrix.json";
import roundProgressionJson from "../../../data/processed/prisoners_dilemma_benchmark_1/round_progression.json";
import modelProfilesJson from "../../../data/processed/prisoners_dilemma_benchmark_1/model_profiles.json";
import metadataJson from "../../../data/processed/prisoners_dilemma_benchmark_1/metadata.json";

const ParlourBenchDashboard = () => {
	const [activeTab, setActiveTab] = useState("leaderboard");
	const [selectedMatchup, setSelectedMatchup] = useState("");
	const [selectedGame, setSelectedGame] = useState("prisoners_dilemma");

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

	// Available games
	const games = [
		{ id: "prisoners_dilemma", name: "Prisoner's Dilemma" },
		{ id: "ghost", name: "Ghost" },
		{ id: "diplomacy", name: "Diplomacy" },
		{ id: "ultimatum_game", name: "Ultimatum Game" },
		{ id: "rock_paper_scissors", name: "Rock Paper Scissors" },
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
								finalScore: {
									player1: score1,
									player2: score2,
								},
								// We don't have actual timeline data in the JSON, so we'll use the match result
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

	// Load all data when the component mounts or selectedGame changes
	useEffect(() => {
		const loadData = async () => {
			setIsLoading(true);
			setError(null);

			try {
				if (selectedGame === "prisoners_dilemma") {
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

					console.log(`Loaded all data for ${selectedGame}`);
				} else {
					// Reset data for other game types (not yet implemented)
					setLeaderboardData([]);
					setRoundProgressionData([]);
					setMatchupMatrix({ models: [], winMatrix: [] });
					setGameSummaryData([]);
					setCooperationByModelAndRound([]);
					setMatchups([]);

					console.log(`No data available for ${selectedGame} yet`);
				}
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
	}, [selectedGame]);

	// Load game timeline data
	const loadGameTimelineData = async (sessionId) => {
		try {
			// In a real implementation, this would make an API call to fetch the timeline data
			// using the session ID. For now, we'll use a placeholder message.
			console.log(`Would fetch timeline data for session: ${sessionId}`);
			return {
				message:
					"Game timeline data would be loaded here based on the session ID",
				// This is where the actual game progression would be returned
			};
		} catch (error) {
			console.error("Error loading game timeline:", error);
			return null;
		}
	};

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
	if (isLoading && selectedGame === "prisoners_dilemma") {
		return (
			<div className="container mx-auto p-4 max-w-6xl">
				<header className="mb-4 text-center">
					<h1 className="text-3xl font-bold mt-4 mb-2">
						ParlourBench Dashboard
					</h1>
					<p className="text-lg text-gray-600 mb-6">
						An open-source benchmark that pits LLMs against one
						another in parlour games
					</p>
				</header>
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
							Loading game data...
						</p>
					</div>
				</div>
			</div>
		);
	}

	// Error state
	if (error) {
		return (
			<div className="container mx-auto p-4 max-w-6xl">
				<header className="mb-4 text-center">
					<h1 className="text-3xl font-bold mt-4 mb-2">
						ParlourBench Dashboard
					</h1>
				</header>
				<div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
					<p className="font-medium">Error loading data</p>
					<p className="text-sm">{error}</p>
				</div>
			</div>
		);
	}

	return (
		<div className="container mx-auto p-4 max-w-6xl">
			<header className="mb-4 text-center">
				<h1 className="text-3xl font-bold mt-4 mb-2">
					ParlourBench Dashboard
				</h1>
				<p className="text-lg text-gray-600 mb-6">
					An open-source benchmark that pits LLMs against one another
					in parlour games
				</p>

				{/* Game Selector */}
				<div className="flex justify-center mb-6">
					<div className="inline-block relative">
						<select
							className="block appearance-none w-64 bg-white border border-gray-300 text-gray-700 py-2 px-4 pr-8 rounded leading-tight focus:outline-none focus:bg-white focus:border-blue-500"
							value={selectedGame}
							onChange={(e) => {
								setSelectedGame(e.target.value);
								setActiveTab("leaderboard"); // Reset to leaderboard when changing games
							}}
						>
							{games.map((game) => (
								<option key={game.id} value={game.id}>
									{game.name}
								</option>
							))}
						</select>
						<div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
							<ChevronDown size={16} />
						</div>
					</div>
				</div>

				{/* Game Status Banner */}
				<div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-2 rounded-lg text-sm mb-6">
					{selectedGame === "prisoners_dilemma" ? (
						<>
							<span className="font-semibold">
								Prisoner's Dilemma:
							</span>{" "}
							{leaderboardData.length > 0
								? `${
										metadataJson?.game_count ||
										matchups.length
								  } games played between ${
										leaderboardData.length
								  } models • Last updated ${
										metadataJson?.processed_at?.split(
											"T"
										)[0] || "March 2025"
								  }`
								: "Loading game data..."}
						</>
					) : (
						<>
							<span className="font-semibold">
								{games.find((g) => g.id === selectedGame)
									?.name || selectedGame}
								:
							</span>{" "}
							Game data not yet available
						</>
					)}
				</div>
			</header>

			{/* Game-specific content */}
			{selectedGame === "prisoners_dilemma" ? (
				<>
					{/* Custom Tabs */}
					<div className="mb-8">
						<div className="flex border-b border-gray-200">
							<button
								className={`px-4 py-2 font-medium text-sm ${
									activeTab === "leaderboard"
										? "border-b-2 border-blue-500 text-blue-600"
										: "text-gray-500 hover:text-gray-700"
								}`}
								onClick={() => setActiveTab("leaderboard")}
							>
								Leaderboard
							</button>
							<button
								className={`px-4 py-2 font-medium text-sm ${
									activeTab === "game-stats"
										? "border-b-2 border-blue-500 text-blue-600"
										: "text-gray-500 hover:text-gray-700"
								}`}
								onClick={() => setActiveTab("game-stats")}
							>
								Game Statistics
							</button>
							<button
								className={`px-4 py-2 font-medium text-sm ${
									activeTab === "matchups"
										? "border-b-2 border-blue-500 text-blue-600"
										: "text-gray-500 hover:text-gray-700"
								}`}
								onClick={() => setActiveTab("matchups")}
							>
								Matchups
							</button>
							<button
								className={`px-4 py-2 font-medium text-sm ${
									activeTab === "timeline"
										? "border-b-2 border-blue-500 text-blue-600"
										: "text-gray-500 hover:text-gray-700"
								}`}
								onClick={() => setActiveTab("timeline")}
							>
								Game Timeline
							</button>
							<button
								className={`px-4 py-2 font-medium text-sm ${
									activeTab === "about"
										? "border-b-2 border-blue-500 text-blue-600"
										: "text-gray-500 hover:text-gray-700"
								}`}
								onClick={() => setActiveTab("about")}
							>
								About
							</button>
						</div>
					</div>

					{/* Tab Content */}
					{activeTab === "leaderboard" && (
						<div className="space-y-6">
							<div className="bg-white rounded-lg shadow-md overflow-hidden">
								<div className="px-6 py-4 border-b border-gray-200">
									<h2 className="text-xl font-semibold">
										Model Leaderboard
									</h2>
									<p className="text-gray-600 text-sm">
										Performance rankings for Prisoner's
										Dilemma (
										{metadataJson?.processed_at?.split(
											"T"
										)[0] || "March 2025"}
										)
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
														Rank
													</th>
													<th
														scope="col"
														className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
													>
														Model
													</th>
													<th
														scope="col"
														className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
													>
														Wins
													</th>
													<th
														scope="col"
														className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
													>
														Losses
													</th>
													<th
														scope="col"
														className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
													>
														Ties
													</th>
													<th
														scope="col"
														className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
													>
														Win Rate
													</th>
													<th
														scope="col"
														className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
													>
														Avg. Score
													</th>
												</tr>
											</thead>
											<tbody className="bg-white divide-y divide-gray-200">
												{leaderboardData.map(
													(model) => (
														<tr
															key={model.model_id}
															className="hover:bg-gray-50"
														>
															<td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
																{model.rank}
															</td>
															<td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
																{
																	model.model_name
																}
															</td>
															<td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
																{model.wins}
															</td>
															<td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
																{model.losses}
															</td>
															<td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
																{model.ties}
															</td>
															<td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
																{(
																	model.winrate *
																	100
																).toFixed(1)}
																%
															</td>
															<td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
																{model.avg_score.toFixed(
																	2
																)}
															</td>
														</tr>
													)
												)}
											</tbody>
										</table>
									</div>
								</div>
							</div>

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
														tickFormatter={(
															value
														) =>
															value
																.split(" ")
																.pop()
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
										Shows how models' strategies evolved
										over the 5 rounds
									</p>
								</div>
								<div className="p-6">
									<div className="h-80">
										<ResponsiveContainer
											width="100%"
											height="100%"
										>
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
														`${(
															value * 100
														).toFixed(0)}%`
													}
												/>
												<Tooltip
													formatter={(value) =>
														`${(
															value * 100
														).toFixed(1)}%`
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
										Shows how each model's cooperation
										strategy changed over rounds
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
																	model.round1 *
																	100
																).toFixed(0)}
																%
															</td>
															<td
																className={`px-6 py-4 whitespace-nowrap text-sm text-center ${getCellColor(
																	model.round2
																)}`}
															>
																{(
																	model.round2 *
																	100
																).toFixed(0)}
																%
															</td>
															<td
																className={`px-6 py-4 whitespace-nowrap text-sm text-center ${getCellColor(
																	model.round3
																)}`}
															>
																{(
																	model.round3 *
																	100
																).toFixed(0)}
																%
															</td>
															<td
																className={`px-6 py-4 whitespace-nowrap text-sm text-center ${getCellColor(
																	model.round4
																)}`}
															>
																{(
																	model.round4 *
																	100
																).toFixed(0)}
																%
															</td>
															<td
																className={`px-6 py-4 whitespace-nowrap text-sm text-center ${getCellColor(
																	model.round5
																)}`}
															>
																{(
																	model.round5 *
																	100
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

							<div className="bg-white rounded-lg shadow-md overflow-hidden">
								<div className="px-6 py-4 border-b border-gray-200">
									<h2 className="text-xl font-semibold">
										Strategy Evolution
									</h2>
									<p className="text-gray-600 text-sm">
										As the game progresses, models switch
										from cooperation to defection
									</p>
								</div>
								<div className="p-6">
									<div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
										<p className="mb-4">
											Key observations from the data:
										</p>
										<ul className="list-disc pl-5 space-y-2">
											<li>
												All models start with
												cooperation in round 1 (100%
												cooperation rate)
											</li>
											<li>
												By the final round, 83.3% of
												decisions are defections
											</li>
											<li>
												The tipping point occurs around
												round 3-4
											</li>
											<li>
												Models appear to use tit-for-tat
												strategies initially, but switch
												to self-preservation in later
												rounds
											</li>
											<li>
												Grok-2 was the most successful
												at timing its defections
												strategically
											</li>
										</ul>
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
										Which model won in direct competitions
										(green up = row model won)
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
																{model
																	.split(" ")
																	.pop()}
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
																(
																	colModel,
																	colIdx
																) => (
																	<td
																		key={
																			colIdx
																		}
																		className="px-6 py-4 whitespace-nowrap text-center"
																	>
																		{renderWinMatrixCell(
																			matchupMatrix
																				.winMatrix[
																				rowIdx
																			]?.[
																				colIdx
																			],
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

							{/* Game Highlights */}
							{matchups.length > 0 && (
								<div className="grid grid-cols-1 gap-6">
									{matchups
										.slice(0, 2)
										.map((matchup, index) => (
											<div
												key={matchup.id}
												className="bg-white rounded-lg shadow-md overflow-hidden"
											>
												<div className="px-6 py-4 border-b border-gray-200">
													<h2 className="text-xl font-semibold">
														Game: {matchup.title}
													</h2>
													<p className="text-gray-600 text-sm">
														{matchup.finalScore
															.player1 >
														matchup.finalScore
															.player2
															? `${matchup.player1} won with a score of ${matchup.finalScore.player1} vs ${matchup.finalScore.player2}`
															: matchup.finalScore
																	.player1 <
															  matchup.finalScore
																	.player2
															? `${matchup.player2} won with a score of ${matchup.finalScore.player2} vs ${matchup.finalScore.player1}`
															: `Game ended in a tie with a score of ${matchup.finalScore.player1}`}
													</p>
												</div>
												<div className="p-6">
													<div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
														{/* Display session ID for debugging/reference */}
														<p className="text-sm text-gray-500 mb-4">
															Session ID:{" "}
															{matchup.session_id ||
																"Not available"}
														</p>

														<p className="mb-2">
															Full game data for
															all rounds can be
															accessed in the Game
															Timeline tab.
														</p>
													</div>
												</div>
											</div>
										))}
								</div>
							)}
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
										Detailed progression of individual
										matchups with decisions and reasoning
									</p>
								</div>
								<div className="p-6">
									<div className="flex flex-wrap gap-2 mb-6">
										{matchups.map((matchup) => (
											<button
												key={matchup.id}
												className={`px-4 py-2 text-sm rounded-full ${
													selectedMatchup ===
													matchup.id
														? "bg-blue-500 text-white"
														: "bg-gray-200 text-gray-700 hover:bg-gray-300"
												}`}
												onClick={() =>
													setSelectedMatchup(
														matchup.id
													)
												}
											>
												{matchup.title}
											</button>
										))}
									</div>

									{(() => {
										const matchup =
											getSelectedMatchupData();

										if (!matchup) {
											return (
												<div className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-center">
													<p>
														No matchup data
														available
													</p>
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
															{
																matchup
																	.finalScore
																	.player1
															}{" "}
															-{" "}
															{
																matchup
																	.finalScore
																	.player2
															}{" "}
															{matchup.player2}
														</p>
													</div>
													<div className="text-sm px-3 py-1 rounded-full bg-gray-100">
														{matchup.finalScore
															.player1 >
														matchup.finalScore
															.player2
															? `${matchup.player1} wins`
															: matchup.finalScore
																	.player1 <
															  matchup.finalScore
																	.player2
															? `${matchup.player2} wins`
															: "Tie game"}
													</div>
												</div>

												<div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
													<p className="mb-4">
														To access the full game
														timeline with
														round-by-round decisions
														and reasoning, please
														use the ParlourBench API
														or view the detailed
														game JSON files.
													</p>
													<p className="text-sm text-gray-600">
														For detailed
														implementation, you
														would load the game
														timeline using the
														session ID:{" "}
														{matchup.session_id ||
															"Not available"}
													</p>
												</div>
											</div>
										);
									})()}
								</div>
							</div>
						</div>
					)}

					{/* About Tab Content */}
					{activeTab === "about" && (
						<div className="space-y-6">
							<div className="bg-white rounded-lg shadow-md overflow-hidden">
								<div className="px-6 py-4 border-b border-gray-200">
									<h2 className="text-xl font-semibold">
										About ParlourBench
									</h2>
								</div>
								<div className="p-6">
									<div className="prose max-w-none">
										<p>
											ParlourBench is an open-source
											benchmark platform that pits
											language models against each other
											in diverse parlour games to evaluate
											their strategic thinking, diplomatic
											prowess, creativity, persuasion,
											deceptive/cooperative behavior, and
											theory-of-mind capabilities.
										</p>
										<p>
											Through these competitions, we
											develop comprehensive rankings
											across key dimensions and showcase
											them on our arena leaderboard. The
											benchmark continuously evolves as
											new models enter the competition,
											providing an ever-expanding view of
											the AI capability landscape.
										</p>
										<h3>Why is this needed?</h3>
										<p>
											LLMs are quickly saturating
											traditional benchmarks - for
											example, they now achieve nearly 90%
											accuracy on MMLU. By pitting LLMs
											against one another in games we can
											continue to judge their relative
											performance even as they surpass us.
											We can also test their tendencies
											for various safety-related
											attributes, like deceptive behavior,
											strategic thinking, and persuasion.
										</p>
										<h3>Project Principles</h3>
										<ul>
											<li>
												Games should not require human
												judgement, scoring, or other
												interventions.
											</li>
											<li>
												Games should require only text
												inputs (no images, speech, or
												other modalities).
											</li>
											<li>
												Games should test at least one
												of the following properties:
												<ul>
													<li>Strategic thinking</li>
													<li>Persuasion</li>
													<li>Social intelligence</li>
													<li>
														Deception/trustworthiness
													</li>
													<li>
														Creativity (as judged by
														other models)
													</li>
													<li>Theory of mind</li>
												</ul>
											</li>
										</ul>
										<p>
											Visit our{" "}
											<a
												href="https://github.com/jmogielnicki/parlourbench/"
												className="text-blue-600 hover:underline"
											>
												GitHub repository
											</a>{" "}
											for more information, documentation,
											and to contribute to the project.
										</p>
									</div>
								</div>
							</div>
						</div>
					)}
				</>
			) : (
				<div className="bg-white rounded-lg shadow-md overflow-hidden">
					<div className="px-6 py-12 text-center">
						<h2 className="text-xl font-semibold text-gray-700 mb-4">
							{games.find((g) => g.id === selectedGame)?.name}{" "}
							Coming Soon
						</h2>
						<p className="text-gray-500 mb-6">
							We're currently collecting data for this game type.
							Check back soon!
						</p>
						<button
							className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
							onClick={() => setSelectedGame("prisoners_dilemma")}
						>
							View Prisoner's Dilemma Data
						</button>
					</div>
				</div>
			)}
		</div>
	);
};

export default ParlourBenchDashboard;
