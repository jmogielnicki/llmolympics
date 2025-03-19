import React from "react";
import { useGameData } from "../../../context/GameDataContext";
import ModelLeaderboard from "../../ModelLeaderboard";

/**
 * Leaderboard Tab content for Debate Slam
 */
const LeaderboardTab = () => {
	const { leaderboardData, gameConfig, metadata } = useGameData();
	const leaderboardColumns = gameConfig.leaderboardColumns;

	return (
		<div className="space-y-6">
			{/* Use the ModelLeaderboard Component */}
			<ModelLeaderboard
				data={leaderboardData}
				columns={leaderboardColumns}
				title="Model Leaderboard"
				subtitle={`Performance rankings for Debate Slam (${
					metadata?.processed_at?.split("T")[0] || "March 2025"
				})`}
			/>
		</div>
	);
};

export default LeaderboardTab;
