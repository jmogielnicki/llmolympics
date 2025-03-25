import React from "react";
import { useGameData } from "../context/GameDataContext";
import { ChevronUp, ChevronDown, Minus } from "lucide-react";


/**
 * Matchups Tab content showing head-to-head competition results
 */
const MatchupsChart = () => {
	const { matchupMatrix } = useGameData();

	const renderWinMatrixCell = (value, rowIndex, colIndex) => {
		if (rowIndex === colIndex) return "-";
		if (value === null) return "-";

		if (value === 1)
			return <ChevronUp className="text-green-500 mx-auto" />;
		if (value === 0)
			return <ChevronDown className="text-red-500 mx-auto" />;
		return <Minus className="text-gray-500 mx-auto" />;
	};
	return (
		<div className="space-y-6">
			<div className="bg-white rounded-lg shadow-md overflow-hidden">
				<div className="px-6 py-4 border-b border-gray-200">
					<h2 className="text-xl font-semibold">
						Head-to-Head Matchups
					</h2>
					<p className="text-gray-600 text-sm">
						Which model won in direct competitions (green up = row
						model won)
					</p>
				</div>
				<div className="p-6">
					<div className="overflow-x-auto -mx-6 px-6">
						<table className="min-w-full divide-y divide-gray-200">
							<thead className="bg-gray-50">
								<tr>
									<th
										scope="col"
										className="px-2 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 tracking-tight whitespace-wrap"
									>
										Model
									</th>
									{matchupMatrix.models.map((model, idx) => (
										<th
											key={idx}
											scope="col"
											className="px-2 sm:px-4 py-3 text-center text-xs font-medium text-gray-500 tracking-tight whitespace-wrap"
										>
											{model}
										</th>
									))}
								</tr>
							</thead>
							<tbody className="bg-white divide-y divide-gray-200">
								{matchupMatrix.models.map(
									(rowModel, rowIdx) => (
										<tr
											key={rowIdx}
											className="hover:bg-gray-50"
										>
											<td className="px-2 sm:px-6 py-4 text-sm font-medium text-gray-900 whitespace-nowrap">
												{rowModel}
											</td>
											{matchupMatrix.models.map(
												(colModel, colIdx) => (
													<td
														key={colIdx}
														className="px-2 sm:px-4 py-4 text-center"
													>
														{renderWinMatrixCell(
															matchupMatrix
																.winMatrix[
																rowIdx
															]?.[colIdx],
															rowIdx,
															colIdx
														)}
													</td>
												)
											)}
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

export default MatchupsChart;
