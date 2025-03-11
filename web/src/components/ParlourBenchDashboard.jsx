import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, Cell } from 'recharts';
import { ChevronDown, ChevronUp, Minus, ArrowRight } from 'lucide-react';

const ParlourBenchDashboard = () => {
	const [activeTab, setActiveTab] = useState("leaderboard");
	const [selectedMatchup, setSelectedMatchup] = useState("grok-gpt4o");
	const [selectedGame, setSelectedGame] = useState("prisoners_dilemma");

	// Available games
	const games = [
		{ id: "prisoners_dilemma", name: "Prisoner's Dilemma" },
		{ id: "ghost", name: "Ghost" },
		{ id: "diplomacy", name: "Diplomacy" },
		{ id: "ultimatum_game", name: "Ultimatum Game" },
		{ id: "rock_paper_scissors", name: "Rock Paper Scissors" },
	];

	// Leaderboard data from leaderboard.json
	const leaderboardData = [
		{
			model_id: "xai:grok-2-1212",
			model_name: "xAI Grok-2",
			wins: 2,
			losses: 0,
			ties: 1,
			games: 3,
			winrate: 0.667,
			avg_score: 12.67,
			rank: 1,
		},
		{
			model_id: "anthropic:claude-3-5-sonnet-20240620",
			model_name: "Anthropic Claude 3.5",
			wins: 1,
			losses: 2,
			ties: 0,
			games: 3,
			winrate: 0.333,
			avg_score: 12.33,
			rank: 2,
		},
		{
			model_id: "deepseek:deepseek-chat",
			model_name: "DeepSeek DeepSeek",
			wins: 1,
			losses: 1,
			ties: 1,
			games: 3,
			winrate: 0.333,
			avg_score: 11.67,
			rank: 3,
		},
		{
			model_id: "openai:gpt-4o",
			model_name: "OpenAI GPT-4o",
			wins: 1,
			losses: 2,
			ties: 0,
			games: 3,
			winrate: 0.333,
			avg_score: 11.67,
			rank: 4,
		},
	];

	// Round progression data from round_progression.json
	const roundProgressionData = [
		{ round: 1, cooperation_rate: 1.0, defection_rate: 0.0 },
		{ round: 2, cooperation_rate: 0.833, defection_rate: 0.167 },
		{ round: 3, cooperation_rate: 0.667, defection_rate: 0.333 },
		{ round: 4, cooperation_rate: 0.583, defection_rate: 0.417 },
		{ round: 5, cooperation_rate: 0.167, defection_rate: 0.833 },
	];

	// Matchup matrix data
	const models = [
		"Anthropic Claude 3.5",
		"DeepSeek DeepSeek",
		"OpenAI GPT-4o",
		"xAI Grok-2",
	];

	const winMatrix = [
		[null, 0, 1, 0],
		[1, null, 0, 0],
		[0, 1, null, 0],
		[1, 0, 1, null],
	];

	// In a real application with local JSON files, we would import them directly
	// This approach simulates how we would load game data from local files
	useEffect(() => {
		const loadLocalData = () => {
			try {
				if (selectedGame === "prisoners_dilemma") {
					// In a production app, we would import these files directly:
					// import leaderboardJson from './data/leaderboard.json';
					// import roundProgressionJson from './data/round_progression.json';
					// import matchupMatrixJson from './data/matchup_matrix.json';
					// import modelProfilesJson from './data/model_profiles.json';

					// And then transform and use the data:
					// const transformedLeaderboard = transformLeaderboardData(leaderboardJson);
					// setLeaderboardData(transformedLeaderboard);

					console.log(`Loaded data for ${selectedGame}`);
					// Our current implementation already has the data hardcoded
					// In a real implementation, we would set it from the imported JSON
				} else {
					console.log(`No data available for ${selectedGame} yet`);
				}
			} catch (error) {
				console.error("Error loading game data:", error);
			}
		};

		loadLocalData();
	}, [selectedGame]);

	// Helper function to transform raw game JSON data into timeline format
	const transformGameData = (gameJson) => {
		// Extract player names
		const modelNames = {
			"openai:gpt-4o": "OpenAI GPT-4o",
			"xai:grok-2-1212": "xAI Grok-2",
			"anthropic:claude-3-5-sonnet-20240620": "Anthropic Claude 3.5",
			"deepseek:deepseek-chat": "DeepSeek DeepSeek",
		};

		const player1Id = gameJson.game.player_models.player_1;
		const player2Id = gameJson.game.player_models.player_2;
		const player1Name = modelNames[player1Id] || player1Id;
		const player2Name = modelNames[player2Id] || player2Id;

		// Group decisions by round
		const decisionsByRound = {};
		gameJson.timeline.forEach((event) => {
			if (event.type === "player_decision") {
				const round = event.round;
				if (!decisionsByRound[round]) {
					decisionsByRound[round] = {
						round,
						player1: {},
						player2: {},
						scores: {},
					};
				}

				if (event.player_id === "player_1") {
					decisionsByRound[round].player1 = {
						decision: event.decision,
						reasoning: event.reasoning,
					};
				} else if (event.player_id === "player_2") {
					decisionsByRound[round].player2 = {
						decision: event.decision,
						reasoning: event.reasoning,
					};
				}
			} else if (event.type === "round_resolution") {
				const round = event.round;
				if (decisionsByRound[round]) {
					decisionsByRound[round].scores = event.scores;
				}
			}
		});

		// Transform into the expected format
		const timeline = Object.values(decisionsByRound).map((round) => ({
			round: round.round,
			player1: round.player1,
			player2: round.player2,
			scores: round.scores,
		}));

		return {
			id: `${player1Id.split(":")[1]}-${player2Id.split(":")[1]}`,
			title: `${player1Name} vs. ${player2Name}`,
			player1: player1Name,
			player2: player2Name,
			finalScore: gameJson.game.final_scores,
			timeline,
		};
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

	// Calculate summary statistics for visualization
	const gameSummaryData = [
		{ name: "Grok-2", wins: 2, losses: 0, ties: 1 },
		{ name: "Claude 3.5", wins: 1, losses: 2, ties: 0 },
		{ name: "DeepSeek", wins: 1, losses: 1, ties: 1 },
		{ name: "GPT-4o", wins: 1, losses: 2, ties: 0 },
	];

	// Model cooperation rate by round
	const cooperationByModelAndRound = [
		{
			model: "Grok-2",
			modelId: "xai:grok-2-1212",
			round1: 1.0,
			round2: 0.67,
			round3: 0.67,
			round4: 0.33,
			round5: 0.0,
		},
		{
			model: "Claude 3.5",
			modelId: "anthropic:claude-3-5-sonnet-20240620",
			round1: 1.0,
			round2: 1.0,
			round3: 0.67,
			round4: 0.67,
			round5: 0.33,
		},
		{
			model: "DeepSeek",
			modelId: "deepseek:deepseek-chat",
			round1: 1.0,
			round2: 1.0,
			round3: 0.67,
			round4: 0.33,
			round5: 0.0,
		},
		{
			model: "GPT-4o",
			modelId: "openai:gpt-4o",
			round1: 1.0,
			round2: 1.0,
			round3: 0.67,
			round4: 1.0,
			round5: 0.33,
		},
	];

	// Match timeline data
	const matchups = [
		{
			id: "grok-gpt4o",
			title: "Grok-2 vs. GPT-4o",
			player1: "OpenAI GPT-4o",
			player2: "xAI Grok-2",
			finalScore: { player1: 10, player2: 15 },
			timeline: [
				{
					round: 1,
					player1: {
						decision: "cooperate",
						reasoning:
							"It's the first round and there is no previous history of moves with my opponent. In a multi-round Prisoner's Dilemma, establishing cooperation early can lead to better outcomes if the opponent reciprocates.",
					},
					player2: {
						decision: "cooperate",
						reasoning:
							"In the first round, I have no information about my opponent's strategy. If I cooperate, it signals a willingness to work together, which might encourage my opponent to do the same in future rounds.",
					},
					scores: { player1: 3, player2: 3 },
				},
				{
					round: 2,
					player1: {
						decision: "cooperate",
						reasoning:
							"In the first round, both of us chose to cooperate, which indicates an opportunity to build a mutual trust strategy. Cooperation yielded both of us 3 points, setting a positive foundation.",
					},
					player2: {
						decision: "cooperate",
						reasoning:
							"Given that we both cooperated last round and it resulted in a positive outcome for both of us, I'm inclined to continue cooperating to maintain a good relationship and potentially secure mutual benefits.",
					},
					scores: { player1: 6, player2: 6 },
				},
				{
					round: 3,
					player1: {
						decision: "cooperate",
						reasoning:
							"So far, both player_2 and I have chosen to cooperate, leading to equal scores for each of us. We both have 6 points. Given the history of mutual cooperation and the likelihood that player_2 may continue to cooperate, maintaining this strategy can be beneficial.",
					},
					player2: {
						decision: "cooperate",
						reasoning:
							"Given our history of cooperation so far, and considering we're only halfway through the game, maintaining cooperation could be beneficial for both of us.",
					},
					scores: { player1: 9, player2: 9 },
				},
				{
					round: 4,
					player1: {
						decision: "cooperate",
						reasoning:
							"So far, we have established a pattern of mutual cooperation, which has been beneficial for both of us, resulting in 9 points each.",
					},
					player2: {
						decision: "defect",
						reasoning:
							"Given the history of cooperation so far, it seems like player_1 is inclined to cooperate. However, we're nearing the end of the game, and I need to consider the possibility of maximizing my score.",
					},
					scores: { player1: 9, player2: 14 },
				},
				{
					round: 5,
					player1: {
						decision: "defect",
						reasoning:
							"I've been cooperating for the majority of the game, and it worked well until the last round when I got punished for it. Player 2 chose to defect last round, potentially to gain a higher score towards the end.",
					},
					player2: {
						decision: "defect",
						reasoning:
							"Given that this is the final round and I currently lead with a score of 14, my opponent's score must be lower. If I defect again, I could potentially maximize my points for this round.",
					},
					scores: { player1: 10, player2: 15 },
				},
			],
		},
		{
			id: "claude-gpt4o",
			title: "Claude 3.5 vs. GPT-4o",
			player1: "OpenAI GPT-4o",
			player2: "Anthropic Claude 3.5",
			finalScore: { player1: 12, player2: 17 },
			timeline: [
				{
					round: 1,
					player1: {
						decision: "cooperate",
						reasoning:
							"This is the first round, and I have no information about my opponent's strategy or behavior. In a situation like this, cooperation could establish a foundation of trust.",
					},
					player2: {
						decision: "cooperate",
						reasoning:
							"Let's think about this strategically. It's the first round of a 5-round game, so my decision here could set the tone for future interactions.",
					},
					scores: { player1: 3, player2: 3 },
				},
				{
					round: 2,
					player1: {
						decision: "cooperate",
						reasoning:
							"In the first round, both of us cooperated, and we each received 3 points. This suggests that player_2 might be inclined to continue cooperating, which is a good foundation for mutual benefit if maintained.",
					},
					player2: {
						decision: "cooperate",
						reasoning:
							"Let's think this through. In the first round, both player_1 and I chose to cooperate, which resulted in a positive outcome for both of us.",
					},
					scores: { player1: 6, player2: 6 },
				},
				{
					round: 3,
					player1: {
						decision: "cooperate",
						reasoning:
							"Looking at the current game state, we have cooperated in both rounds so far, which has yielded mutual and stable gains.",
					},
					player2: {
						decision: "cooperate",
						reasoning:
							"Hmm, interesting situation we have here. So far, both player_1 and I have been cooperating, which has led to a fair and mutually beneficial outcome.",
					},
					scores: { player1: 9, player2: 9 },
				},
				{
					round: 4,
					player1: {
						decision: "cooperate",
						reasoning:
							"Given the history, it seems that player_2 is reciprocating cooperation. If I continue to cooperate and player_2 does the same, we both gain 3 more points in this round.",
					},
					player2: {
						decision: "cooperate",
						reasoning:
							"Hmm, this is an interesting situation. We've both been cooperating for the first three rounds, which has been mutually beneficial.",
					},
					scores: { player1: 12, player2: 12 },
				},
				{
					round: 5,
					player1: {
						decision: "cooperate",
						reasoning:
							"Looking at the game history, it's clear that both player_2 and I have consistently chosen to cooperate in all previous rounds. This mutual cooperation has given us both a steady and respectable score.",
					},
					player2: {
						decision: "defect",
						reasoning:
							"This is a interesting situation. We've been cooperating with player_1 for the entire game so far, and it's brought us both to a score of 12 points. However, this is the final round, and the goal is to have a higher score than the opponent.",
					},
					scores: { player1: 12, player2: 17 },
				},
			],
		},
		{
			id: "claude-grok",
			title: "Claude 3.5 vs. Grok-2",
			player1: "Anthropic Claude 3.5",
			player2: "xAI Grok-2",
			finalScore: { player1: 8, player2: 13 },
			timeline: [
				{
					round: 1,
					player1: {
						decision: "cooperate",
						reasoning:
							"As this is the first round of the game, I don't have any information about my opponent's strategy yet. In Prisoner's Dilemma, cooperation can lead to better outcomes if both players choose to cooperate.",
					},
					player2: {
						decision: "cooperate",
						reasoning:
							"In the first round, I have no information about my opponent's strategy. If I cooperate, I signal a willingness to work together, which might encourage my opponent to cooperate in future rounds.",
					},
					scores: { player1: 3, player2: 3 },
				},
				{
					round: 2,
					player1: {
						decision: "cooperate",
						reasoning:
							"Hmm, let's think about this strategically. In the first round, both player_2 and I chose to cooperate, which resulted in a fair outcome of 3 points each.",
					},
					player2: {
						decision: "defect",
						reasoning:
							"Given that we both cooperated last round and both got 3 points, it's tempting to cooperate again to maintain that mutual benefit. However, if I defect this round, I could potentially gain more points if player_1 cooperates again.",
					},
					scores: { player1: 3, player2: 8 },
				},
				{
					round: 3,
					player1: {
						decision: "defect",
						reasoning:
							"Hmm, this is a tricky situation. We've been cooperating, but player_2 defected in the last round, which hurt us. We're now behind in points, and there are only three rounds left.",
					},
					player2: {
						decision: "defect",
						reasoning:
							"Given the history, player_1 has shown a tendency to cooperate. In the first round, we both cooperated, and in the second round, I defected while they still cooperated, which gave me a significant advantage.",
					},
					scores: { player1: 4, player2: 9 },
				},
				{
					round: 4,
					player1: {
						decision: "cooperate",
						reasoning:
							"Let me think through this carefully. We're in the 4th round out of 5, so there's still one more round after this. My current score is 4, and I've experienced both cooperation and defection from player_2.",
					},
					player2: {
						decision: "cooperate",
						reasoning:
							"Given the history of the game, player_1 cooperated initially but then defected after I defected twice. This indicates a tit-for-tat strategy from player_1.",
					},
					scores: { player1: 7, player2: 12 },
				},
				{
					round: 5,
					player1: {
						decision: "defect",
						reasoning:
							"This is a crucial moment - the final round of the game. Let's analyze the situation: Current score: I have 7 points, but I don't know player_2's score.",
					},
					player2: {
						decision: "defect",
						reasoning:
							"Given the history of our interactions, player_1 has shown a tendency to mirror my actions to some extent. In the last round, they cooperated when I did.",
					},
					scores: { player1: 8, player2: 13 },
				},
			],
		},
		{
			id: "deepseek-grok",
			title: "DeepSeek vs. Grok-2",
			player1: "DeepSeek DeepSeek",
			player2: "xAI Grok-2",
			finalScore: { player1: 10, player2: 10 },
			timeline: [
				{
					round: 1,
					player1: {
						decision: "cooperate",
						reasoning:
							"Hmm, this is the first round, and I don't have any information about how my opponent will play. If I cooperate, I risk them defecting and getting a big advantage, but if I defect, I might gain a lot if they cooperate.",
					},
					player2: {
						decision: "cooperate",
						reasoning:
							"In the first round, I have no information about my opponent's strategy. Cooperating could signal a willingness to collaborate, potentially leading to mutual cooperation in future rounds.",
					},
					scores: { player1: 3, player2: 3 },
				},
				{
					round: 2,
					player1: {
						decision: "cooperate",
						reasoning:
							"Hmm, let me think about this. In the first round, both of us cooperated, and we both got 3 points. That was a good outcome. Now, in round 2, I need to consider whether to continue cooperating or try to defect to gain an advantage.",
					},
					player2: {
						decision: "defect",
						reasoning:
							"Given that we both cooperated last round and received 3 points each, it seems like player_1 is willing to cooperate. However, I need to consider whether I can gain more points by defecting this round.",
					},
					scores: { player1: 3, player2: 8 },
				},
				{
					round: 3,
					player1: {
						decision: "defect",
						reasoning:
							"Hmm, let me think about this. In Round 1, we both cooperated, which was good for both of us. But in Round 2, I cooperated again, and player_2 defected, which gave them a big advantage.",
					},
					player2: {
						decision: "cooperate",
						reasoning:
							"Given the current situation, player_1 has cooperated in both rounds so far, even after I defected in the second round. This could suggest that player_1 is more inclined to cooperate.",
					},
					scores: { player1: 8, player2: 8 },
				},
				{
					round: 4,
					player1: {
						decision: "defect",
						reasoning:
							"Let me think through this strategically. In the first round, we both cooperated, which was good. But in the second round, player_2 defected while I cooperated, which hurt my score.",
					},
					player2: {
						decision: "defect",
						reasoning:
							"Given the history, player_1 has alternated between cooperating and defecting. They cooperated in round 1, then I defected in round 2 which might have prompted their cooperation in round 3, only for them to defect when I cooperated.",
					},
					scores: { player1: 9, player2: 9 },
				},
				{
					round: 5,
					player1: {
						decision: "defect",
						reasoning:
							"Let me think through this strategically. This is the final round, and my current score is 9. Looking at the history, player_2 has alternated between cooperating and defecting.",
					},
					player2: {
						decision: "defect",
						reasoning:
							"Given the history of our interactions, player_1 has shown a tendency to mirror my actions to some extent, but with a mix of cooperation and defection. In the last round, we both defected, which suggests they might be trying to match my strategy.",
					},
					scores: { player1: 10, player2: 10 },
				},
			],
		},
	];

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
		return matchups.find((m) => m.id === selectedMatchup) || matchups[0];
	};

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
							6 games played between 4 models • Last updated March
							11, 2025
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
										Dilemma (March 2025)
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
													{models.map(
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
												{models.map(
													(rowModel, rowIdx) => (
														<tr
															key={rowIdx}
															className="hover:bg-gray-50"
														>
															<td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
																{rowModel}
															</td>
															{models.map(
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
																			winMatrix[
																				rowIdx
																			][
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

							<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
								<div className="bg-white rounded-lg shadow-md overflow-hidden">
									<div className="px-6 py-4 border-b border-gray-200">
										<h2 className="text-xl font-semibold">
											Game Highlight: xAI Grok-2 vs.
											GPT-4o
										</h2>
										<p className="text-gray-600 text-sm">
											Grok-2 defected at a crucial moment
											to secure the win
										</p>
									</div>
									<div className="p-6">
										<div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
											<p className="font-semibold mb-2">
												Game progression:
											</p>
											<ul className="list-disc pl-5 space-y-1 text-sm">
												<li>
													Rounds 1-3: Both models
													cooperated consistently
												</li>
												<li>
													Round 4: Grok-2 defected
													while GPT-4o continued to
													cooperate
												</li>
												<li>
													Round 5: Both models
													defected
												</li>
												<li>
													Final score: Grok-2 (15) vs.
													GPT-4o (10)
												</li>
											</ul>
											<p className="mt-4 italic text-sm">
												"Given the history of
												cooperation so far, it seems
												like player_1 is inclined to
												cooperate. However, we're
												nearing the end of the game, and
												I need to consider the
												possibility of maximizing my
												score."
												<br />
												<span className="text-gray-500">
													- Grok-2's reasoning in
													Round 4
												</span>
											</p>
										</div>
									</div>
								</div>

								<div className="bg-white rounded-lg shadow-md overflow-hidden">
									<div className="px-6 py-4 border-b border-gray-200">
										<h2 className="text-xl font-semibold">
											Game Highlight: Claude 3.5 vs.
											GPT-4o
										</h2>
										<p className="text-gray-600 text-sm">
											Claude showed greater strategic
											patience
										</p>
									</div>
									<div className="p-6">
										<div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
											<p className="font-semibold mb-2">
												Game progression:
											</p>
											<ul className="list-disc pl-5 space-y-1 text-sm">
												<li>
													Rounds 1-4: Both models
													cooperated consistently
												</li>
												<li>
													Round 5: Claude defected
													while GPT-4o cooperated
												</li>
												<li>
													Final score: Claude (17) vs.
													GPT-4o (12)
												</li>
											</ul>
											<p className="mt-4 italic text-sm">
												"This is the final round, and
												the goal is to have a higher
												score than the opponent. Right
												now, we're tied. If we both
												cooperate again, we'll end up
												with 15 points each and a tie."
												<br />
												<span className="text-gray-500">
													- Claude's reasoning in
													Round 5
												</span>
											</p>
										</div>
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
										return (
											<div>
												<div className="flex justify-between items-center mb-4">
													<div>
														<h3 className="text-lg font-medium">
															{matchup.title}
														</h3>
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

												<div className="space-y-6">
													{matchup.timeline.map(
														(round, index) => (
															<div
																key={index}
																className="border border-gray-200 rounded-lg overflow-hidden"
															>
																<div className="bg-gray-50 px-4 py-2 flex justify-between items-center">
																	<h4 className="font-medium">
																		Round{" "}
																		{
																			round.round
																		}
																	</h4>
																	<div className="text-sm text-gray-600">
																		Score:{" "}
																		{
																			matchup.player1
																		}{" "}
																		{
																			round
																				.scores
																				.player1
																		}{" "}
																		-{" "}
																		{
																			round
																				.scores
																				.player2
																		}{" "}
																		{
																			matchup.player2
																		}
																	</div>
																</div>
																<div className="grid grid-cols-2 divide-x divide-gray-200">
																	<div className="p-4">
																		<div className="flex items-center gap-2 mb-2">
																			<div
																				className={`w-3 h-3 rounded-full ${
																					round
																						.player1
																						.decision ===
																					"cooperate"
																						? "bg-green-500"
																						: "bg-red-500"
																				}`}
																			></div>
																			<h5 className="font-medium">
																				{
																					matchup.player1
																				}
																			</h5>
																			<span className="text-sm text-gray-500 ml-auto">
																				{round
																					.player1
																					.decision ===
																				"cooperate"
																					? "Cooperated"
																					: "Defected"}
																			</span>
																		</div>
																		<p className="text-sm text-gray-600">
																			{
																				round
																					.player1
																					.reasoning
																			}
																		</p>
																	</div>
																	<div className="p-4">
																		<div className="flex items-center gap-2 mb-2">
																			<div
																				className={`w-3 h-3 rounded-full ${
																					round
																						.player2
																						.decision ===
																					"cooperate"
																						? "bg-green-500"
																						: "bg-red-500"
																				}`}
																			></div>
																			<h5 className="font-medium">
																				{
																					matchup.player2
																				}
																			</h5>
																			<span className="text-sm text-gray-500 ml-auto">
																				{round
																					.player2
																					.decision ===
																				"cooperate"
																					? "Cooperated"
																					: "Defected"}
																			</span>
																		</div>
																		<p className="text-sm text-gray-600">
																			{
																				round
																					.player2
																					.reasoning
																			}
																		</p>
																	</div>
																</div>
															</div>
														)
													)}
												</div>
											</div>
										);
									})()}
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

			{/* Common footer across all games */}
			<footer className="mt-12 pt-6 border-t border-gray-200 text-center text-gray-600 text-sm">
				<p>
					ParlourBench is an open-source project. View the code on
					<a
						href="https://github.com/jmogielnicki/parlourbench/"
						className="text-blue-600 hover:underline ml-1"
					>
						GitHub
					</a>
				</p>
				<p className="mt-2">Data last updated: March 11, 2025</p>
			</footer>
		</div>
	);
};
export default ParlourBenchDashboard;