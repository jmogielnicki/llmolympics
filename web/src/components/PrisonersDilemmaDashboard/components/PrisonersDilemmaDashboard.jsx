import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";

// Import context provider
import { GameDataProvider, useGameData } from "../../../context/GameDataContext";

// Import tab components
import LeaderboardTab from "../tabs/LeaderBoardTab";
import GameStatsTab from "../tabs/GameStatsTab";
import TimelineTab from "../tabs/TimelineTab";
import AboutTab from "../tabs/AboutTab";

// Import common components
import TabNavigation from "../../TabNavigation";

/**
 * Loading state component
 */
const LoadingState = () => (
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

/**
 * Error state component
 * @param {Object} props
 * @param {string} props.message - Error message
 */
const ErrorState = ({ message }) => (
	<div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
		<p className="font-medium">Error loading data</p>
		<p className="text-sm">{message}</p>
	</div>
);

/**
 * Main content component that handles routing between tabs
 */
const DashboardContent = () => {
	const { isLoading, error } = useGameData();

	// If still loading, show loading state
	if (isLoading) {
		return <LoadingState />;
	}

	// If there was an error, show error state
	if (error) {
		return <ErrorState message={error} />;
	}

	// Tab configuration
	const tabs = [
		{ id: "leaderboard", label: "Leaderboard" },
		{ id: "timeline", label: "Matches" },
		{ id: "game-stats", label: "Stats" },
		{ id: "about", label: "About" },
	];

	return (
		<div>
			{/* Use the Tab Navigation Component */}
			<TabNavigation tabs={tabs} basePath="/games/prisoners-dilemma" />

			{/* Route to the correct tab component */}
			<Routes>
				<Route
					path="/"
					element={
						<Navigate
							to="/games/prisoners-dilemma/leaderboard"
							replace
						/>
					}
				/>
				<Route path="/leaderboard" element={<LeaderboardTab />} />
				<Route path="/game-stats" element={<GameStatsTab />} />
				<Route path="/timeline" element={<TimelineTab />} />
				<Route
					path="/timeline/:leftModelId/:rightModelId"
					element={<TimelineTab />}
				/>

				<Route path="/about" element={<AboutTab />} />
				<Route
					path="*"
					element={
						<Navigate
							to="/games/prisoners-dilemma/leaderboard"
							replace
						/>
					}
				/>
			</Routes>
		</div>
	);
};

/**
 * Main Prisoner's Dilemma Dashboard component
 * This is the entry point that wraps everything with the data provider
 */
const PrisonersDilemmaDashboard = () => {
	return (
		<GameDataProvider gameType="prisoners_dilemma">
			<DashboardContent />
		</GameDataProvider>
	);
};

export default PrisonersDilemmaDashboard;
