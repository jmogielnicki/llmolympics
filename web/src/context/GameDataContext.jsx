import React, { createContext, useContext, useState, useEffect } from "react";
import { ChevronUp, ChevronDown, Minus } from "lucide-react";

// Import data transformation utilities
import {
	transformLeaderboardData,
	transformMatchupMatrix,
	transformRoundProgressionData,
	createGameSummaryData,
	transformCooperationByModel,
	extractGameData,
} from "@/utils/dataTransformers";

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

// Create the context
const GameDataContext = createContext(null);

/**
 * Provider component for game data
 * @param {Object} props
 * @param {ReactNode} props.children - Child components
 */
export const GameDataProvider = ({ children }) => {
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
	const [metadata, setMetadata] = useState(metadataJson || {});

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
			formatter: (value) => `${(value * 100).toFixed(0)}%`,
		},
		{
			key: "first_to_defect_rate",
			label: "First Defector",
			align: "right",
			formatter: (value) => `${(value * 100).toFixed(0)}%`,
		},
		{
			key: "avg_score",
			label: "Avg. Score",
			align: "right",
			formatter: (value) => value.toFixed(1),
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
		if (rate >= 0.9) return "bg-blue-500";
		if (rate >= 0.8) return "bg-blue-400";
		if (rate >= 0.7) return "bg-blue-300";
		if (rate >= 0.6) return "bg-blue-200";
		if (rate >= 0.5) return "bg-blue-100";
		if (rate <= 0.1) return "bg-red-500";
		if (rate <= 0.2) return "bg-red-400";
		if (rate <= 0.3) return "bg-red-300";
		if (rate <= 0.4) return "bg-red-200";
		if (rate <= 0.5) return "bg-red-100";
		return "";
	};

	// Function to load game details based on session ID
	const loadGameDetail = async (sessionId) => {
		if (!sessionId) {
			return null;
		}

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
				return null;
			}

			// Load the file dynamically
			const module = await gameDetailFiles[fileKey]();
			return module.default || module;
		} catch (error) {
			console.error(
				`Failed to load game detail for ${sessionId}:`,
				error
			);
			return null;
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
				const gameData = extractGameData(modelProfilesJson);
				setMatchups(gameData);

				// Set metadata
				setMetadata(metadataJson || {});

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

	// Prepare the context value
	const contextValue = {
		// Data
		leaderboardData,
		roundProgressionData,
		matchupMatrix,
		gameSummaryData,
		cooperationByModelAndRound,
		matchups,
		metadata,

		// UI helpers
		leaderboardColumns,
		renderWinMatrixCell,
		getCellColor,

		// Functions
		loadGameDetail,

		// Status
		isLoading,
		error,
	};

	return (
		<GameDataContext.Provider value={contextValue}>
			{children}
		</GameDataContext.Provider>
	);
};

/**
 * Hook to use game data context
 * @returns {Object} Game data context
 */
export const useGameData = () => {
	const context = useContext(GameDataContext);
	if (!context) {
		throw new Error("useGameData must be used within a GameDataProvider");
	}
	return context;
};

export default GameDataContext;
