import React from "react";
import {
	BarChart,
	Bar,
	XAxis,
	YAxis,
	CartesianGrid,
	Tooltip,
	Legend,
	ResponsiveContainer,
} from "recharts";
import AverageVotesChart from "../../AverageVotesChart";
import PerformanceSummaryChart from "../../PerformanceSummaryChart";

// Import custom hooks
import useWindowDimensions from "../../../hooks/useWindowDimensions";
import { useGameData } from "../../../context/GameDataContext";

// Import shared components
import ModelLeaderboard from "../../ModelLeaderboard";

/**
 * Leaderboard Tab content
 */
const LeaderboardTab = () => {
	const { leaderboardData, gameConfig, gameSummaryData, metadata } =
		useGameData();
	const leaderboardColumns = gameConfig.leaderboardColumns;

	return (
		<div className="space-y-6">
			{/* Use the ModelLeaderboard Component */}
			<ModelLeaderboard
				data={leaderboardData}
				columns={leaderboardColumns}
				title="Model Leaderboard"
				subtitle={`Performance rankings for Prisoner's Dilemma (${
					metadata?.processed_at?.split("T")[0] || "March 2025"
				})`}
			/>

			<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
				<AverageVotesChart
					data={leaderboardData}
					title={"Average score"}
					subtitle={
						"The average score from all games played"
					}
					dataKey={"model_name"}
				/>
				<PerformanceSummaryChart
					data={gameSummaryData}
					title={"Performance Summary"}
					subtitle={"Wins, losses, and ties by model"}
				/>
			</div>
		</div>
	);
};

export default LeaderboardTab;
