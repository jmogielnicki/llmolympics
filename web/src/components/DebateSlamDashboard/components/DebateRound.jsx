import React from "react";
import { Plus, Minus } from "lucide-react";
import { shortenModelName } from "../../../utils/commonUtils";

/**
 * Component for displaying a debate round with arguments and judge votes
 *
 * @param {Object} props
 * @param {Object} props.round - Round data
 * @param {string} props.roundId - Unique identifier for the round
 * @param {Array} props.debaters - Debater information
 * @param {Array} props.judges - Judge information
 * @param {boolean} props.isExpanded - Whether this round is expanded
 * @param {Function} props.onToggle - Function to call when toggling expansion
 * @param {boolean} props.isPostSwap - Whether this round is after the side swap
 */
const DebateRound = ({
	round,
	roundId,
	debaters,
	judges,
	isExpanded,
	onToggle,
	isPostSwap = false,
}) => {
	if (!round) return null;

	// Extract vote data
	const judgeVotes = round.judge_votes || [];
	const totalVotes = judgeVotes.length;

	// Count votes for each side
	const votesPerSide = {};
	judgeVotes.forEach((vote) => {
		if (!votesPerSide[vote.vote]) {
			votesPerSide[vote.vote] = 0;
		}
		votesPerSide[vote.vote]++;
	});

	// Get all sides from the debater arguments
	const sides = round.debater_arguments.map((arg) => arg.side_id);
	const side1 = sides[0];
	const side2 = sides[1];

	// Calculate percentage for progress bar
	const side1Votes = votesPerSide[side1] || 0;
	const side1Percentage = totalVotes ? (side1Votes / totalVotes) * 100 : 50;

	// Map player IDs to debater information
	const debaterMap = {};
	debaters?.forEach((debater) => {
		debaterMap[debater.player_id] = debater;
	});

	// Map player IDs to judge information
	const judgeMap = {};
	judges?.forEach((judge) => {
		judgeMap[judge.player_id] = judge;
	});

	// Previous round votes for comparison
	const previousVotes = round.previousRoundVotes || {};

	return (
		<div className="border border-gray-200 rounded-md overflow-hidden">
			{/* Round header with progress bar */}
			<div
				className="flex items-center cursor-pointer"
				onClick={onToggle}
			>
				<div className="flex-col w-full">
					<div className="flex items-center justify-center align-center">
						<div className="px-4 pt-4 pb-1 text-sm font-medium w-auto">
							Round {round.round_number}
						</div>
						<div className="bg-gray-50 mt-3 p-1 flex items-center">
							{isExpanded ? <Minus size={18} /> : <Plus size={18} />}
						</div>
					</div>
					<div className="flex-1 h-8 flex pb-2">
						{/* Left side progress (green) */}
						<div
							className="h-full bg-green-200"
							style={{ width: `${side1Percentage}%` }}
						></div>
						{/* Right side progress (orange) */}
						<div
							className="h-full bg-orange-200"
							style={{ width: `${100 - side1Percentage}%` }}
						></div>
					</div>
				</div>
			</div>

			{/* Expanded content */}
			{isExpanded && (
				<div className="px-4 py-3">
					{/* Debater arguments */}
					<div className="grid grid-cols-2 gap-4 mb-4">
						{round.debater_arguments.map((argument, index) => {
							const debater = debaters?.find(
								(d) => d.player_id === argument.player_id
							);
							const isLeftSide = index === 0;

							return (
								<div
									key={argument.player_id}
									className={`p-4 rounded-md ${
										isLeftSide
											? "bg-green-50"
											: "bg-orange-50"
									}`}
								>
									<div className="font-medium mb-2 flex justify-between">
										<span>
											{shortenModelName(
												debater?.model ||
													argument.player_id
											)}
										</span>
									</div>
									<p className="text-sm whitespace-pre-line">
										{argument.argument}
									</p>
								</div>
							);
						})}
					</div>

					{/* Judge votes */}
					<div className="mt-4">
						<h4 className="font-medium mb-2">Judge Votes</h4>
						<div className="grid grid-cols-2 gap-4">
							{sides.map((side_id, index) => {
								const isLeftSide = index === 0;
								const votes =
									judgeVotes.filter(
										(vote) => vote.vote === side_id
									) || [];

								return (
									<div
										key={side_id}
										className={`p-3 rounded-md ${
											isLeftSide
												? "bg-green-50"
												: "bg-orange-50"
										}`}
									>
										<p className="font-medium mb-2">
											{side_id.replace(/-/g, " ")} (
											{votes.length} votes)
										</p>
										<div className="flex flex-wrap gap-2">
											{votes.map((vote) => {
												const judge = judges?.find(
													(j) =>
														j.player_id ===
														vote.player_id
												);

												// A judge is swayed if their vote in this round differs from previous round
												const wasSwayed =
													previousVotes[
														vote.player_id
													] &&
													previousVotes[
														vote.player_id
													] !== vote.vote;

												return (
													<span
														key={vote.player_id}
														className={`inline-flex items-center px-2 py-1 rounded text-xs
															${wasSwayed ? "bg-yellow-100 border border-yellow-300" : "bg-gray-100"}`}
														title={
															wasSwayed
																? "Changed vote from previous round"
																: ""
														}
													>
														{shortenModelName(
															judge?.model ||
																vote.player_id
														)}
														{wasSwayed && " ★"}
													</span>
												);
											})}
										</div>
									</div>
								);
							})}
						</div>
					</div>
				</div>
			)}
		</div>
	);
};

export default DebateRound;
