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

// Import custom hooks
import useWindowDimensions from "../../../hooks/useWindowDimensions";
import { useGameData } from "../../../context/GameDataContext";

// Import shared components
import ModelLeaderboard from "../../ModelLeaderboard";

/**
 * Leaderboard Tab content
 */
const LeaderboardTab = () => {
	const { leaderboardData, leaderboardColumns, gameSummaryData, metadata } =
		useGameData();
	const { width } = useWindowDimensions();

	// Responsive chart margins based on screen width
	const chartMargins = {
		top: 20,
		right: Math.max(5, Math.min(30, width / 40)), // Scale between 5-30px
		left: Math.max(5, Math.min(50, width / 20)), // Scale between 15-50px
		bottom: 5,
	};

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
				{/* Performance Summary Chart */}
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
							<ResponsiveContainer width="100%" height="100%">
								<BarChart
									layout="vertical"
									data={gameSummaryData}
									margin={chartMargins}
								>
									<CartesianGrid strokeDasharray="3 3" />
									<XAxis type="number" />
									<YAxis
										dataKey="name"
										type="category"
										width={40}
										tick={{ fontSize: 12 }}
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

				{/* Average Score Chart */}
				<div className="bg-white rounded-lg shadow-md overflow-hidden">
					<div className="px-6 py-4 border-b border-gray-200">
						<h2 className="text-xl font-semibold">Average Score</h2>
						<p className="text-gray-600 text-sm">
							Average points per game
						</p>
					</div>
					<div className="p-6">
						<div className="h-80">
							<ResponsiveContainer width="100%" height="100%">
								<BarChart
									layout="vertical"
									data={leaderboardData}
									margin={chartMargins}
								>
									<CartesianGrid strokeDasharray="3 3" />
									<XAxis type="number" domain={[0, 15]} />
									<YAxis
										dataKey="model_name"
										type="category"
										width={40}
										tick={{ fontSize: 12 }}
									/>
									<Tooltip
										formatter={(value) => value.toFixed(2)}
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
	);
};

export default LeaderboardTab;
