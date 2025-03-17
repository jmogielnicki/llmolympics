import React, { useMemo } from "react";
import { useGameData } from "../../../context/GameDataContext";

/**
 * Voting Patterns Tab to visualize which models vote for which other models
 */
const VotingPatternsTab = () => {
	const { votingPatterns } = useGameData();

	// If voting patterns aren't available yet
	if (
		!votingPatterns ||
		!votingPatterns.models ||
		votingPatterns.models.length === 0
	) {
		return (
			<div className="bg-white rounded-lg shadow-md p-6 text-center">
				<p className="text-gray-500">
					No voting pattern data available yet.
				</p>
			</div>
		);
	}

	// Calculate vote counts for better visualization
	const modelsWithVotes = useMemo(() => {
		const result = [];

		// For each voter model
		for (const voterModel of votingPatterns.models) {
			const votesGiven = {};
			let totalVotesGiven = 0;

			// Count votes given to each candidate
			for (const candidateModel of votingPatterns.models) {
				if (voterModel.id !== candidateModel.id) {
					// Models don't vote for themselves
					const voteCount =
						votingPatterns.matrix[voterModel.id][
							candidateModel.id
						] || 0;
					votesGiven[candidateModel.id] = voteCount;
					totalVotesGiven += voteCount;
				}
			}

			// Calculate votes received
			let votesReceived = 0;
			for (const otherVoter of votingPatterns.models) {
				if (otherVoter.id !== voterModel.id) {
					votesReceived +=
						votingPatterns.matrix[otherVoter.id][voterModel.id] ||
						0;
				}
			}

			result.push({
				id: voterModel.id,
				name: voterModel.name,
				votesGiven,
				totalVotesGiven,
				votesReceived,
			});
		}

		return result;
	}, [votingPatterns]);

	// Sort models by votes received (most to least)
	const sortedModels = useMemo(() => {
		return [...modelsWithVotes].sort(
			(a, b) => b.votesReceived - a.votesReceived
		);
	}, [modelsWithVotes]);

	// Get color intensity based on vote count
	const getColorIntensity = (count, max) => {
		if (count === 0) return "bg-gray-100";

		const intensity = Math.min(Math.floor((count / max) * 5) + 1, 5);
		return `bg-indigo-${intensity}00`;
	};

	// Find maximum vote count for color scaling
	const maxVoteCount = useMemo(() => {
		let max = 0;
		for (const voter of modelsWithVotes) {
			for (const candidateId in voter.votesGiven) {
				max = Math.max(max, voter.votesGiven[candidateId]);
			}
		}
		return max || 1; // Avoid division by zero
	}, [modelsWithVotes]);

	return (
		<div className="space-y-6">
			{/* Voting Heatmap */}
			<div className="bg-white rounded-lg shadow-md overflow-hidden">
				<div className="px-6 py-4 border-b border-gray-200">
					<h2 className="text-xl font-semibold text-center">
						Voting Relationships
					</h2>
					<p className="text-gray-600 text-sm text-center">
						Which models vote for which other models
					</p>
				</div>
				<div className="p-6">
					<div className="overflow-x-auto -mx-6 px-6">
						<table className="min-w-full divide-y divide-gray-200">
							<thead className="bg-gray-50">
								<tr>
									<th className="px-4 py-3 text-left text-xs font-medium text-gray-500 tracking-wider">
										Voter \ Candidate
									</th>
									{/* Use sortedModels for column headers */}
									{sortedModels.map((model) => (
										<th
											key={model.id}
											className="px-2 py-2 text-center text-xs font-medium text-gray-500 tracking-wider w-16"
											style={{
												minWidth: "4rem",
												maxWidth: "6rem",
											}}
										>
											<div className="line-clamp-2 h-12 flex items-center justify-center">
												{model.name}
											</div>
										</th>
									))}
									<th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
										<div className="line-clamp-2">
											Total Votes Given
										</div>
									</th>
								</tr>
							</thead>
							<tbody className="bg-white divide-y divide-gray-200">
								{/* Use sortedModels for rows as well */}
								{sortedModels.map((voter) => (
									<tr
										key={voter.id}
										className="hover:bg-gray-50"
									>
										<td className="px-2 py-4 text-sm font-medium text-gray-900 w-24">
											<div className="truncate">
												{voter.name}
											</div>
										</td>
										{/* Use same sortedModels for columns in each row */}
										{sortedModels.map((candidate) => (
											<td
												key={candidate.id}
												className={`px-2 py-4 text-center w-16 ${
													voter.id === candidate.id
														? "bg-gray-200 text-gray-400"
														: getColorIntensity(
																voter
																	.votesGiven[
																	candidate.id
																] || 0,
																maxVoteCount
														  )
												} ${
													(voter.votesGiven[
														candidate.id
													] || 0) > 0
														? "text-indigo-900 font-medium"
														: "text-gray-500"
												}`}
											>
												{voter.id === candidate.id
													? "—"
													: voter.votesGiven[
															candidate.id
													  ] || 0}
											</td>
										))}
										<td className="px-4 py-4 text-center font-medium text-gray-900">
											{voter.totalVotesGiven}
										</td>
									</tr>
								))}
								<tr className="bg-gray-50">
									<td className="px-2 py-4 text-sm font-medium text-gray-900">
										<div className="line-clamp-2">
											Total Votes Received
										</div>
									</td>
									{/* Use sortedModels for total votes row as well */}
									{sortedModels.map((model) => (
										<td
											key={model.id}
											className="px-2 py-4 text-center font-medium text-gray-900 w-16"
										>
											{model.votesReceived}
										</td>
									))}
									<td className="px-4 py-4"></td>
								</tr>
							</tbody>
						</table>
					</div>
				</div>
			</div>

			{/* Model Voting Preferences */}
			<div className="bg-white rounded-lg shadow-md overflow-hidden">
				<div className="px-6 py-4 border-b border-gray-200">
					<h2 className="text-xl font-semibold text-center">
						Model Voting Preferences
					</h2>
					<p className="text-gray-600 text-sm text-center">
						Summary of which models' poetry is preferred by others
					</p>
				</div>
				<div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
					{/* Most Votes Received */}
					<div className="border rounded-lg p-4">
						<h3 className="text-lg font-medium mb-3">
							Most Votes Received
						</h3>
						<ul className="space-y-2">
							{sortedModels.map((model) => (
								<li
									key={model.id}
									className="flex justify-between items-center"
								>
									<span className="text-gray-800">
										{model.name}
									</span>
									<div className="flex items-center">
										<div
											className="bg-indigo-500 h-4 rounded"
											style={{
												width: `${Math.min(
													100,
													model.votesReceived * 20
												)}px`,
											}}
										></div>
										<span className="ml-2 text-gray-700">
											{model.votesReceived}
										</span>
									</div>
								</li>
							))}
						</ul>
					</div>

					{/* Most Active Voters */}
					<div className="border rounded-lg p-4">
						<h3 className="text-lg font-medium mb-3">
							Most Active Voters
						</h3>
						<ul className="space-y-2">
							{[...modelsWithVotes]
								.sort(
									(a, b) =>
										b.totalVotesGiven - a.totalVotesGiven
								)
								.map((model) => (
									<li
										key={model.id}
										className="flex justify-between items-center"
									>
										<span className="text-gray-800">
											{model.name}
										</span>
										<div className="flex items-center">
											<div
												className="bg-green-500 h-4 rounded"
												style={{
													width: `${Math.min(
														100,
														model.totalVotesGiven *
															20
													)}px`,
												}}
											></div>
											<span className="ml-2 text-gray-700">
												{model.totalVotesGiven}
											</span>
										</div>
									</li>
								))}
						</ul>
					</div>
				</div>
			</div>
		</div>
	);
};

export default VotingPatternsTab;
