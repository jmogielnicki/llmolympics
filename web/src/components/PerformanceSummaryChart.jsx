// components/charts/PerformanceSummaryChart.js
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
import useWindowDimensions from "../hooks/useWindowDimensions";

const PerformanceSummaryChart = ({ data, title, subtitle }) => {
	const { width } = useWindowDimensions();
	// Responsive chart margins based on screen width
	const chartMargins = {
		top: 20,
		right: Math.max(5, Math.min(30, width / 40)), // Scale between 5-30px
		left: Math.max(5, Math.min(50, width / 20)), // Scale between 15-50px
		bottom: 5,
	};

	return (
		<div className="bg-white rounded-lg shadow-md overflow-hidden">
			<div className="px-6 py-4 border-b border-gray-200">
				<h2 className="text-xl font-semibold">{title}</h2>
				<p className="text-gray-600 text-sm">{subtitle}</p>
			</div>
			<div className="p-6">
				<div className="h-100">
					<ResponsiveContainer width="100%" height="100%">
						<BarChart
							layout="vertical"
							data={data}
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
	);
};

export default PerformanceSummaryChart;
