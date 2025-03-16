import React, { createContext, useContext, useState, useEffect } from "react";
import { getGameDefinition } from "../utils/gameDefinitions";

// Create context
const GameDataContext = createContext(null);

/**
 * Provider component for game data
 */
export const GameDataProvider = ({ gameType, children }) => {
	const [data, setData] = useState({
		leaderboard: [],
		gameSessions: [],
		metadata: null,
		gameSpecific: {},
	});
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState(null);

	// Get game definition which contains configuration and transformers
	const gameDefinition = getGameDefinition(gameType);

	// Load all data when the component mounts
	useEffect(() => {
		if (!gameType || !gameDefinition) {
			setError("Invalid game type");
			setIsLoading(false);
			return;
		}

		const loadData = async () => {
			setIsLoading(true);
			setError(null);

			try {
				const benchmark = `${gameType}_benchmark_1`;

				// Load required data files in parallel
				const [leaderboardData, modelProfilesData, metadataData] =
					await Promise.all([
						import(`@data/processed/${benchmark}/leaderboard.json`),
						import(
							`@data/processed/${benchmark}/model_profiles.json`
						),
						import(`@data/processed/${benchmark}/metadata.json`),
					]);

				// Load optional game-specific data files
				const gameSpecificData = {};
				await Promise.all(
					(gameDefinition.config.dataTypes || []).map(async (dataType) => {

						try {
							const data = await import(
								`@data/processed/${benchmark}/${dataType}.json`
							);
							gameSpecificData[dataType] = data.default || data;
						} catch (e) {
							console.log(
								`Optional data ${dataType} not available for ${gameType}`
							);
						}
					})
				);

				// Transform the data using the game definition
				const transformedData = gameDefinition.transformData({
					leaderboard: leaderboardData.default || leaderboardData,
					modelProfiles:
						modelProfilesData.default || modelProfilesData,
					metadata: metadataData.default || metadataData,
					gameSpecific: gameSpecificData,
				});

				setData(transformedData);
			} catch (error) {
				console.error(`Error loading ${gameType} data:`, error);
				setError(`Failed to load game data: ${error.message}`);
			} finally {
				setIsLoading(false);
			}
		};

		loadData();
	}, [gameType, gameDefinition]);

	// Function to load game details - simplified to use a consistent pattern
	const loadGameDetail = async (sessionId) => {
		if (!sessionId || !gameType) return null;

		try {
			// Extract timestamp from session ID
			const timestampMatch = sessionId.match(/(\d{8}_\d{6})/);
			const timestamp = timestampMatch ? timestampMatch[1] : sessionId;

			// Load the detail file directly
			const detailModule = await import(
				`@data/processed/${gameType}_benchmark_1/detail/${timestamp}.json`
			);
			return gameDefinition.transformGameDetail(
				detailModule.default || detailModule
			);
		} catch (error) {
			console.error(
				`Failed to load game detail for ${sessionId}:`,
				error
			);
			return null;
		}
	};

	// Check if gameType is defined
	if (!gameType) {
		return (
			<div className="p-4 bg-red-50 border border-red-300 rounded text-red-700">
				Error: No game type specified
			</div>
		);
	}

	// Prepare the context value
	const contextValue = {
		// Game metadata
		gameType,
		gameConfig: gameDefinition.config,
		metadata: data.metadata,

		// Game data
		leaderboardData: data.leaderboard,
		gameSessions: data.gameSessions,
		...data.gameSpecific,

		// Helper functions
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
 */
export const useGameData = () => {
	const context = useContext(GameDataContext);
	if (!context) {
		throw new Error("useGameData must be used within a GameDataProvider");
	}
	return context;
};

export default GameDataContext;
