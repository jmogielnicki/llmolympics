import React from "react";
import { useGameData } from "../../../context/GameDataContext";
import ModelLeaderboard from "../../ModelLeaderboard";
import AverageVotesChart from "../../AverageVotesChart";
import PerformanceSummaryChart from "../../PerformanceSummaryChart";

/**
 * Leaderboard Tab content for Debate Slam
 */
const LeaderboardTab = () => {
	const { leaderboardData, gameConfig, metadata } = useGameData();
	const leaderboardColumns = gameConfig.leaderboardColumns;

	// Create a summary of voting data for visualization
	const votingData = leaderboardData
		.map((model) => ({
			name: model.model_name,
			avg_score: model.avg_score || 0,
			total_score: model.total_score || 0,
			games: model.games,
			wins: model.wins,
			losses: model.losses,
			ties: model.ties,
		}))
		.sort((a, b) => b.avg_score - a.avg_score);

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
			<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
				{/* Use the AverageVotesChart Component */}
				<AverageVotesChart
					data={votingData}
					title={"Average votes"}
					subtitle={
						"The average number of votes received by each model"
					}
				/>

				{/* Use the PerformanceSummaryChart Component */}
				<PerformanceSummaryChart
					data={votingData}
					title={"Performance Summary"}
					subtitle={"Wins, losses, and ties by model"}
				/>
			</div>
		</div>
	);
};

export default LeaderboardTab;
