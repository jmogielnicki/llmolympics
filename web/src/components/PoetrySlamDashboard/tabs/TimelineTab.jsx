import React, { useState, useEffect } from "react";
import { useGameData } from "../../../context/GameDataContext";
import PoemDisplay from "../components/PoemDisplay";
import { Calendar, MessageSquare, Trophy } from "lucide-react";
import { shortenModelName } from "../../../utils/commonUtils";
import ReactMarkdown from "react-markdown";

/**
 * Timeline tab for displaying poetry slam sessions
 */
const TimelineTab = () => {
	const { gameSessions, loadGameDetail } = useGameData();
	const [selectedSession, setSelectedSession] = useState(null);
	const [gameDetail, setGameDetail] = useState(null);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState(null);

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

	// Format poems with voting information
	const formatPoems = () => {
		if (!gameDetail || !gameDetail.poems) return [];

		const playerVotes = {};

		// Map player_id to model names for votes
		if (gameDetail.timeline) {
			gameDetail.timeline
				.filter((event) => event.type === "player_vote")
				.forEach((vote) => {
					if (!playerVotes[vote.voted_for]) {
						playerVotes[vote.voted_for] = [];
					}
					playerVotes[vote.voted_for].push(vote.model_name);
				});
		}

		const poemsWithVotes = gameDetail.poems.map((poem) => ({
			...poem,
			votedBy: playerVotes[poem.id] || [],
			voteCount: (playerVotes[poem.id] || []).length,
		}));

		// Sort poems by vote count (most votes first)
		return poemsWithVotes.sort((a, b) => b.voteCount - a.voteCount);
	};

	const poems = formatPoems();
	const prompt = gameDetail?.prompt;

	const formatTimestamp = (timestamp) => {
		if (!timestamp) return "";

		try {
			// Extract date from format like "2025-03-14 21:48:41"
			const date = new Date(timestamp);
			return (
				date.toLocaleDateString() +
				" " +
				date.toLocaleTimeString([], {
					hour: "2-digit",
					minute: "2-digit",
				})
			);
		} catch (e) {
			console.error("Error formatting timestamp:", e);
			return timestamp;
		}
	};

	const getSessionDate = (sessionId) => {
		if (!sessionId) return "";

		try {
			// Extract timestamp from session ID like "poetry_slam_20250314_214841"
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

		return ""; // Return empty string instead of sessionId to avoid showing "Invalid Date"
	};

	// For timeline events
	const getGameTimeline = () => {
		if (!gameDetail?.timeline)
			return { promptCreation: null, votingEvents: [] };

		const promptCreation = gameDetail.timeline.find(
			(event) => event.type === "prompt_creation"
		);
		const votingEvents = gameDetail.timeline.filter(
			(event) => event.type === "player_vote"
		);

		return { promptCreation, votingEvents };
	};

	const { promptCreation } = getGameTimeline();

	// Format final scores for better readability
	const formatFinalScores = () => {
		if (!gameDetail?.game?.summary?.final_scores_display) return "";

		try {
			// Parse the scores string format: "DeepSeek Chat: 0, OpenAI GPT-4o: 1, Anthropic Claude 3.5: 0, xAI Grok-2: 0, Mistral Mistral Large: 2, Anthropic Claude 3.7: 3"
			const scoresText = gameDetail.game.summary.final_scores_display;
			const scoreEntries = scoresText.split(", ").map((entry) => {
				const [model, scoreStr] = entry.split(": ");
				const score = parseInt(scoreStr, 10);
				return { model, score };
			});

			// Sort by score, highest first
			scoreEntries.sort((a, b) => b.score - a.score);

			return scoreEntries;
		} catch (e) {
			console.error("Error parsing scores:", e);
			return gameDetail.game.summary.final_scores_display;
		}
	};

	const finalScores = formatFinalScores();
	const winningModel = gameDetail?.game?.summary?.winning_model_name;

	return (
		<div className="w-full max-w-4xl mx-auto">
			<div className="mb-8">
				<h2 className="text-2xl font-bold text-center mb-1">
					Poetry Session Details
				</h2>
				<p className="text-center text-gray-600 mb-6">
					View prompts, poems, and voting results from poetry slam
					sessions
				</p>

				{/* Session selector */}
				<div className="mb-6">
					<label
						htmlFor="session-select"
						className="block text-sm font-medium text-gray-700 mb-1"
					>
						Select Poetry Session:
					</label>
					<select
						id="session-select"
						className="w-full border border-gray-300 rounded-md p-2"
						value={selectedSession || ""}
						onChange={(e) => setSelectedSession(e.target.value)}
					>
						{gameSessions?.map((session) => {
							const sessionDate = getSessionDate(session.id);
							return (
								<option key={session.id} value={session.id}>
									{session.title}
									{sessionDate ? ` - ${sessionDate}` : ""}
								</option>
							);
						})}
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
								Loading session details...
							</p>
						</div>
					</div>
				) : (
					gameDetail && (
						<div className="space-y-6">
							{/* Session metadata */}
							<div className="bg-indigo-50 rounded-lg p-4">
								<div className="mb-2">
									<h3 className="text-lg font-semibold flex items-center">
										{winningModel ? (
											<>
												<Trophy
													size={18}
													className="mr-2 text-yellow-500"
												/>
												{shortenModelName(winningModel)}{" "}
												won!
											</>
										) : (
											"Poetry Slam Session"
										)}
									</h3>
									<p className="text-sm text-gray-600 flex items-center">
										<Calendar size={14} className="mr-1" />
										{promptCreation
											? formatTimestamp(
													promptCreation.timestamp
											  )
											: getSessionDate(selectedSession)}
									</p>
								</div>
								<div className="mt-3">
									<p className="font-medium mb-1">
										Final scores:
									</p>
									<div className="space-y-1 pl-2">
										{Array.isArray(finalScores) ? (
											finalScores.map((score, index) => (
												<p
													key={index}
													className="text-sm flex items-center"
												>
													{index === 0 &&
														score.score > 0 && (
															<Trophy
																size={14}
																className="mr-1 text-yellow-500"
															/>
														)}
													{score.model}: {score.score}
												</p>
											))
										) : (
											<p className="text-sm">
												{finalScores}
											</p>
										)}
									</div>
									<p className="text-sm text-gray-600 mt-2">
										{gameDetail.game?.players?.length || 0}{" "}
										participants
									</p>
								</div>
							</div>

							{/* Prompt */}
							{prompt && (
								<div className="bg-white rounded-lg shadow-md overflow-hidden">
									<div className="px-6 py-4 border-b border-gray-200 flex items-center">
										<MessageSquare
											size={18}
											className="mr-2 text-gray-600"
										/>
										<h3 className="text-lg font-semibold">
											Poetry Prompt
										</h3>
										{prompt.author && (
											<span className="ml-2 text-sm text-gray-500">
												by{" "}
												{shortenModelName(
													prompt.author
												)}
											</span>
										)}
									</div>
									<div className="p-6 prose prose-sm max-w-none">
										<div className="whitespace-normal bg-yellow-50 p-4 rounded border border-yellow-100">
											<ReactMarkdown>
												{prompt.text.replace(
													/\n\n/g,
													"\n\n&nbsp;\n\n"
												)}
											</ReactMarkdown>
										</div>
									</div>
								</div>
							)}

							{/* Poems with Voting Results */}
							<div className="bg-white rounded-lg shadow-md overflow-hidden">
								<div className="px-6 py-4 border-b border-gray-200">
									<h3 className="text-lg font-semibold">
										Poems & Voting Results
									</h3>
									<p className="text-gray-600 text-sm">
										{poems.length} poems submitted in this
										session
									</p>
								</div>
								<div className="p-6">
									<div className="grid grid-cols-1 gap-8">
										{poems.map((poem, index) => (
											<PoemDisplay
												key={index}
												poem={poem}
											/>
										))}
									</div>
								</div>
							</div>
						</div>
					)
				)}
			</div>
		</div>
	);
};

export default TimelineTab;
