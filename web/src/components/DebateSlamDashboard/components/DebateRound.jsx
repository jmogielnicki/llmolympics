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
						<div className="px-4 pt-4 pb-1 text-sm font-medium w-auto text-stone-600">
							Round {round.round_number}
						</div>
						<div className="bg-gray-50 mt-3 p-1 flex items-center text-stone-600">
							{isExpanded ? (
								<Minus size={18} />
							) : (
								<Plus size={18} />
							)}
						</div>
					</div>
					<div className="flex-1 h-8 flex pb-2">
						{/* Left side progress (green) */}
						<div
							className="h-full bg-green-300"
							style={{ width: `${side1Percentage}%` }}
						></div>
						{/* Right side progress (orange) */}
						<div
							className="h-full bg-orange-300"
							style={{ width: `${100 - side1Percentage}%` }}
						></div>
					</div>
				</div>
			</div>

			{/* Expanded content */}
			{isExpanded && (
				<div className="px-4 py-3">
					{/* Debater arguments */}
					<div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
						{round.debater_arguments.map((argument, index) => {
							const debater = debaters?.find(
								(d) => d.player_id === argument.player_id
							);
							const isLeftSide = index === 0;
							const sideText = argument.side_id.replace(
								/-/g,
								" "
							);

							return (
								<div
									key={argument.player_id}
									className={`p-4 rounded-md shadow-sm border border-gray-200 relative overflow-hidden`}
								>
									{/* Accent line on the left */}
									<div
										className={`absolute left-0 top-0 bottom-0 w-1 ${
											isLeftSide
												? "bg-green-500"
												: "bg-orange-500"
										}`}
									></div>

									{/* Content with increased left padding due to accent line */}
									<div className="pl-3">
										{/* Header with model name and stance */}
										<div className="font-medium mb-3 flex flex-col">
											<span className="text-gray-900 font-bold">
												{shortenModelName(
													debater?.model ||
														argument.player_id
												)}
											</span>
											<span
												className={`text-sm ${
													isLeftSide
														? "text-green-600"
														: "text-orange-600"
												}`}
											>
												{sideText}
											</span>
										</div>

										{/* Argument text */}
										<p className="text-sm whitespace-pre-line mb-4">
											{argument.argument}
										</p>

										{/* Integrated judge section */}
										<div className="mt-3 pt-3 border-t border-gray-100">
											<p className="text-xs text-gray-500 mb-2">
												Judges who agreed:
											</p>
											<div className="flex flex-wrap gap-1">
												{judgeVotes
													.filter(
														(vote) =>
															vote.vote ===
															argument.side_id
													)
													.map((vote) => {
														const judge =
															judges?.find(
																(j) =>
																	j.player_id ===
																	vote.player_id
															);

														// Check if judge was swayed
														const wasSwayed =
															previousVotes[
																vote.player_id
															] &&
															previousVotes[
																vote.player_id
															] !== vote.vote;

														return (
															<span
																key={
																	vote.player_id
																}
																className={`inline-flex items-center px-2 py-1 rounded text-xs
																	${
																		wasSwayed
																			? "bg-yellow-50 border border-yellow-200 text-yellow-700"
																			: "bg-gray-50 text-gray-700"
																	}`}
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
																{wasSwayed &&
																	" ★"}
															</span>
														);
													})}
											</div>
										</div>
									</div>
								</div>
							);
						})}
					</div>
				</div>
			)}
		</div>
	);
};

export default DebateRound;
