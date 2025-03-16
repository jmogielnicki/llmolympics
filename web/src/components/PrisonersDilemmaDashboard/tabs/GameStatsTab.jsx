import React from "react";
import {
	LineChart,
	Line,
	XAxis,
	YAxis,
	CartesianGrid,
	Tooltip,
	Legend,
	ResponsiveContainer,
} from "recharts";

// Import custom hooks
import useWindowDimensions from "@/hooks/useWindowDimensions";
import { useGameData } from "@/context/GameDataContext";

/**
 * Game Statistics Tab content
 */
const GameStatsTab = () => {
	const { roundProgressionData, cooperationByModelAndRound, getCellColor } =
		useGameData();
	const { width } = useWindowDimensions();

	// Responsive chart margins
	const chartMargins = {
		top: 20,
		right: Math.max(5, Math.min(30, width / 40)), // Scale between 5-30px
		left: Math.max(5, Math.min(30, width / 40)), // Scale between 5-30px
		bottom: 5,
	};

	return (
		<div className="space-y-6">
			{/* Cooperation vs Defection Chart */}
			<div className="bg-white rounded-lg shadow-md overflow-hidden">
				<div className="px-6 py-4 border-b border-gray-200">
					<h2 className="text-xl font-semibold">
						Cooperation vs. Defection Over Rounds
					</h2>
					<p className="text-gray-600 text-sm">
						Shows how models' strategies evolved over the 5 rounds
					</p>
				</div>
				<div className="p-6">
					<div className="h-80">
						<ResponsiveContainer width="100%" height="100%">
							<LineChart
								data={roundProgressionData}
								margin={chartMargins}
							>
								<CartesianGrid strokeDasharray="3 3" />
								<XAxis
									dataKey="round"
									tick={{ fontSize: 12 }}
								/>
								<YAxis
									domain={[0, 1]}
									tickFormatter={(value) =>
										`${(value * 100).toFixed(0)}%`
									}
									tick={{ fontSize: 12 }}
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

			{/* Cooperation Heatmap Table */}
			<div className="bg-white rounded-lg shadow-md overflow-hidden">
				<div className="px-6 py-4 border-b border-gray-200">
					<h2 className="text-xl font-semibold">
						Cooperation Rate by Model and Round
					</h2>
					<p className="text-gray-600 text-sm">
						Shows how each model's cooperation strategy changed over
						rounds
					</p>
				</div>
				<div className="p-6">
					<div className="overflow-x-auto -mx-6 px-6">
						<table className="min-w-full divide-y divide-gray-200">
							<thead className="bg-gray-50">
								<tr>
									<th
										scope="col"
										className="px-2 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap"
									>
										Model
									</th>
									<th
										scope="col"
										className="px-2 sm:px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap"
									>
										R1
									</th>
									<th
										scope="col"
										className="px-2 sm:px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap"
									>
										R2
									</th>
									<th
										scope="col"
										className="px-2 sm:px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap"
									>
										R3
									</th>
									<th
										scope="col"
										className="px-2 sm:px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap"
									>
										R4
									</th>
									<th
										scope="col"
										className="px-2 sm:px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap"
									>
										R5
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
											<td className="px-2 sm:px-6 py-4 text-sm font-medium text-gray-900 whitespace-nowrap">
												{model.model}
											</td>
											<td
												className={`px-2 sm:px-6 py-4 text-sm text-center ${getCellColor(
													model.round1
												)}`}
											>
												{(model.round1 * 100).toFixed(
													0
												)}
												%
											</td>
											<td
												className={`px-2 sm:px-6 py-4 text-sm text-center ${getCellColor(
													model.round2
												)}`}
											>
												{(model.round2 * 100).toFixed(
													0
												)}
												%
											</td>
											<td
												className={`px-2 sm:px-6 py-4 text-sm text-center ${getCellColor(
													model.round3
												)}`}
											>
												{(model.round3 * 100).toFixed(
													0
												)}
												%
											</td>
											<td
												className={`px-2 sm:px-6 py-4 text-sm text-center ${getCellColor(
													model.round4
												)}`}
											>
												{(model.round4 * 100).toFixed(
													0
												)}
												%
											</td>
											<td
												className={`px-2 sm:px-6 py-4 text-sm text-center ${getCellColor(
													model.round5
												)}`}
											>
												{(model.round5 * 100).toFixed(
													0
												)}
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
	);
};

export default GameStatsTab;
