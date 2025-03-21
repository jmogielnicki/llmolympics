import React, { useState, useEffect } from "react";
import { useGameData } from "../../../context/GameDataContext";
import DebateRound from "../components/DebateRound";
import { Calendar } from "lucide-react";

/**
 * Timeline tab for displaying debate slam sessions
 */
const TimelineTab = () => {
	const { gameSessions, loadGameDetail } = useGameData();
	const [selectedSession, setSelectedSession] = useState(null);
	const [gameDetail, setGameDetail] = useState(null);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState(null);
	const [expandedRound, setExpandedRound] = useState(null);

	// Initialize selected session when gameSessions are loaded
	useEffect(() => {
		if (gameSessions?.length > 0 && !selectedSession) {
			setSelectedSession(gameSessions[0].id);
		}
	}, [gameSessions, selectedSession]);

	// Load game detail when session changes
	useEffect(() => {
		const fetchGameDetail = async () => {
			if (!selectedSession) return;

			setLoading(true);
			setError(null);

			try {
				const detail = await loadGameDetail(selectedSession);
				setGameDetail(detail);
			} catch (err) {
				console.error("Error loading game detail:", err);
				setError("Failed to load game details. Please try again.");
			} finally {
				setLoading(false);
			}
		};

		fetchGameDetail();
	}, [selectedSession, loadGameDetail]);

	// Get session date from session ID
	const getSessionDate = (sessionId) => {
		if (!sessionId) return "";

		try {
			const match = sessionId.match(
				/(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/
			);
			if (match) {
				const [_, year, month, day, hour, minute] = match;
				return `${month}/${day}/${year} ${hour}:${minute}`;
			}
		} catch (e) {
			console.error("Error parsing session date:", e);
		}

		return "";
	};

	// Handle round expansion/collapse
	const toggleRound = (roundKey) => {
		if (expandedRound === roundKey) {
			setExpandedRound(null);
		} else {
			setExpandedRound(roundKey);
		}
	};

	// Find debater info by player ID
	const getDebaterInfo = (playerId) => {
		if (!gameDetail?.debate_data?.players?.debaters) return null;

		return gameDetail.debate_data.players.debaters.find(
			(debater) => debater.player_id === playerId
		);
	};

	// Get debater model name
	const getDebaterName = (playerId) => {
		const debater = getDebaterInfo(playerId);
		return debater ? debater.model : playerId;
	};

	// Extract debate data for rendering
	const getDebateData = () => {
        console.log(gameDetail);
		if (!gameDetail) return null;

		return {
			topic: gameDetail.metadata.topic,
			debaters: gameDetail.players.debaters,
			judges: gameDetail.players.judges,
			preSwapRounds: gameDetail.pre_swap.rounds || [],
			postSwapRounds: gameDetail.post_swap.rounds || [],
			summary: gameDetail.summary,
		};
	};

	const debateData = getDebateData();

	return (
		<div className="w-full max-w-4xl mx-auto">
			<div className="mb-8 mt-4">
				<h2 className="text-xl font-bold text-center mb-1">
					Debate Session Details
				</h2>
				<p className="text-sm text-center text-gray-600 mb-6">
					View debate rounds, arguments, and judge decisions
				</p>

				{/* Session selector */}
				<div className="mb-6">
					<label
						htmlFor="session-select"
						className="block text-sm font-medium text-gray-700 mb-1"
					>
						Select Debate Session:
					</label>
					<select
						id="session-select"
						className="w-full border border-gray-300 rounded-md p-2"
						value={selectedSession || ""}
						onChange={(e) => setSelectedSession(e.target.value)}
					>
						{gameSessions?.map((session) => (
							<option key={session.id} value={session.id}>
								{session.id}
							</option>
						))}
					</select>
				</div>

				{error && <p className="text-center text-red-500">{error}</p>}

				{loading ? (
					<div className="flex items-center justify-center p-12">
						<div className="text-center">
							<div
								className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]"
								role="status"
							>
								<span className="!absolute !-m-px !h-px !w-px !overflow-hidden !whitespace-nowrap !border-0 !p-0 ![clip:rect(0,0,0,0)]">
									Loading...
								</span>
							</div>
							<p className="mt-2 text-gray-600">
								Loading debate details...
							</p>
						</div>
					</div>
				) : (
					debateData && (
						<div className="space-y-6">
							{/* Debate metadata */}
							<div className="bg-indigo-50 rounded-lg p-4">
								<div className="mb-2">
									<h3 className="font-semibold text-lg mb-2">
										{debateData.topic}
									</h3>
									<p className="text-sm text-gray-600 mb-2 flex items-center">
										{debateData.judges.length} judges,{" "}
										{debateData.debaters.length} debaters
									</p>
									<p className="text-sm text-gray-600 flex items-center">
										<Calendar size={14} className="mr-1" />
										{getSessionDate(selectedSession)}
									</p>
								</div>
							</div>

							{/* Pre-swap rounds */}
							<div className="bg-white rounded-lg shadow-md overflow-hidden">
								<div className="px-6 py-4 border-b border-gray-200">
									<h3 className="text-lg font-semibold">
										Debate Rounds
									</h3>
								</div>

								{/* Debater header */}
								<div className="flex border-b border-gray-200">
									<div className="w-1/4"></div>
									<div className="w-3/4 flex">
										{debateData.debaters.map(
											(debater, index) => {
												const side =
													debater.pre_swap_side ||
													"TBD";
												const colorClass =
													index === 0
														? "bg-purple-100"
														: "bg-orange-100";
												return (
													<div
														key={debater.player_id}
														className={`w-1/2 p-4 ${colorClass} text-center`}
													>
														<div className="font-medium">
															{
																debater.model
															}
														</div>
														<div className="text-sm">
															{side.replace(
																/-/g,
																" "
															)}
														</div>
													</div>
												);
											}
										)}
									</div>
								</div>

								{/* Preswap rounds */}
								{debateData.preSwapRounds.map(
									(round, index) => (
										<DebateRound
											key={`pre_${index}`}
											roundKey={`pre_${index}`}
											roundNumber={round.round_number}
											debaters={debateData.debaters}
											arguments={round.debater_arguments}
											judges={debateData.judges}
											judgeVotes={round.judge_votes || []}
											isExpanded={
												expandedRound === `pre_${index}`
											}
											toggleRound={() =>
												toggleRound(`pre_${index}`)
											}
											phase="preswap"
											previousRoundVotes={
												index > 0
													? debateData.preSwapRounds[
															index - 1
													  ].judge_votes || []
													: []
											}
										/>
									)
								)}

								{/* Side swap indicator */}
								<div className="bg-gray-200 py-3 text-center font-semibold">
									Side Swap
								</div>

								{/* Debater header post-swap */}
								<div className="flex border-b border-gray-200">
									<div className="w-1/4"></div>
									<div className="w-3/4 flex">
										{debateData.debaters.map(
											(debater, index) => {
												const side =
													debater.post_swap_side ||
													"TBD";
												const colorClass =
													index === 0
														? "bg-purple-100"
														: "bg-orange-100";
												return (
													<div
														key={debater.player_id}
														className={`w-1/2 p-4 ${colorClass} text-center`}
													>
														<div className="font-medium">
															{debater.model}
														</div>
														<div className="text-sm">
															{side.replace(
																/-/g,
																" "
															)}
														</div>
													</div>
												);
											}
										)}
									</div>
								</div>

								{/* Post-swap rounds */}
								{debateData.postSwapRounds.map(
									(round, index) => (
										<DebateRound
											key={`post_${index}`}
											roundKey={`post_${index}`}
											roundNumber={round.round_number}
											debaters={debateData.debaters}
											arguments={round.debater_arguments}
											judges={debateData.judges}
											judgeVotes={round.judge_votes || []}
											isExpanded={
												expandedRound ===
												`post_${index}`
											}
											toggleRound={() =>
												toggleRound(`post_${index}`)
											}
											phase="post-swap"
											previousRoundVotes={
												index > 0
													? debateData.postSwapRounds[
															index - 1
													  ].judge_votes || []
													: []
											}
										/>
									)
								)}
							</div>

							{/* Winner info */}
							{debateData.summary &&
								debateData.summary.winner && (
									<div className="bg-yellow-50 p-4 border border-yellow-200 rounded-lg text-center">
										<h3 className="font-semibold text-lg">
											Overall Winner:{" "}
											{getDebaterName(
												debateData.summary.winner
													.player_id
											)}
										</h3>
										<p className="text-sm">
											Total Score:{" "}
											{
												debateData.summary.winner.total_score
											}
										</p>
									</div>
								)}
						</div>
					)
				)}
			</div>
		</div>
	);
};

export default TimelineTab;