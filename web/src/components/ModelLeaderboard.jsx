import React from "react";

/**
 * Reusable model leaderboard component
 * @param {Object} props
 * @param {Array} props.data - Leaderboard data array
 * @param {Array} props.columns - Column configuration array
 * @param {string} props.title - Leaderboard title
 * @param {string} props.subtitle - Leaderboard subtitle
 */
const ModelLeaderboard = ({ data, columns, title, subtitle }) => {
	return (
		<div className="bg-white rounded-lg shadow-md overflow-hidden">
			<div className="px-6 py-4 border-b border-gray-200">
				<h2 className="text-xl font-semibold text-center">{title}</h2>
				{subtitle && (
					<p className="text-gray-600 text-sm text-center">
						{subtitle}
					</p>
				)}
			</div>
			<div className="p-6">
				<div className="overflow-x-auto -mx-6 px-6">
					<table className="min-w-full divide-y divide-gray-200">
						<thead className="bg-gray-50">
							<tr>
								{columns.map((column) => (
									<th
										key={column.key}
										scope="col"
										className={`px-2 sm:px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap ${
											column.align === "right"
												? "text-right"
												: "text-left"
										}`}
									>
										{column.label}
									</th>
								))}
							</tr>
						</thead>
						<tbody className="bg-white divide-y divide-gray-200">
							{data.map((row, index) => (
								<tr
									key={row.id || index}
									className="hover:bg-gray-50"
								>
									{columns.map((column) => (
										<td
											key={column.key}
											className={`px-2 sm:px-6 py-4 text-sm ${
												column.key === "model_name"
													? "whitespace-nowrap"
													: ""
											} ${
												column.key === "rank" ||
												column.key === "model_name"
													? "font-medium text-gray-900"
													: "text-gray-500"
											} ${
												column.align === "right"
													? "text-right"
													: "text-left"
											}`}
										>
											{column.formatter
												? column.formatter(
														row[column.key],
														row
												  )
												: row[column.key]}
										</td>
									))}
								</tr>
							))}
						</tbody>
					</table>
				</div>
			</div>
		</div>
	);
};

export default ModelLeaderboard;
