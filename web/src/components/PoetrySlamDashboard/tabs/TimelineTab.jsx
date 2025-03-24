import React, { useState, useEffect } from "react";
import { useGameData } from "../../../context/GameDataContext";
import PoemDisplay from "../components/PoemDisplay";
import { Calendar, MessageSquare, Trophy } from "lucide-react";
import {
	shortenModelName,
	convertStarsToBold,
} from "../../../utils/commonUtils";
import { useParams, useNavigate, useLocation } from "react-router-dom";

/**
 * Timeline tab for displaying poetry slam sessions
 */
const TimelineTab = () => {
	const { gameSessions, loadGameDetail } = useGameData();
	const [gameDetail, setGameDetail] = useState(null);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState(null);

	// Get sessionId from URL params
	const { sessionId } = useParams();
	const navigate = useNavigate();
	const location = useLocation();

	// Handle session initialization and URL updates
	useEffect(() => {
		if (!gameSessions || gameSessions.length === 0) {
			return; // Wait for sessions to load
		}

		// If we're on the base timeline path without a session ID
		if (location.pathname === "/games/poetry-slam/timeline") {
			// Navigate to the first session
			navigate(`/games/poetry-slam/timeline/${gameSessions[0].id}`, {
				replace: true,
			});
			return;
		}

		// If we have a session ID in the URL
		if (sessionId) {
			// Check if it's a valid session ID
			const isValidSession = gameSessions.some(
				(session) => session.id === sessionId
			);

			if (isValidSession) {
				// Load this session
				loadSessionDetails(sessionId);
			} else {
				// Invalid session ID - redirect to first session with error message
				setError(
					`Invalid session ID: ${sessionId}. Redirecting to a valid session.`
				);
				navigate(`/games/poetry-slam/timeline/${gameSessions[0].id}`, {
					replace: true,
				});
			}
		}
	}, [gameSessions, sessionId, navigate, location.pathname]);

	// Function to load session details
	const loadSessionDetails = async (id) => {
		if (!id) return;

		setLoading(true);
		setError(null);

		try {
			const detail = await loadGameDetail(id);
			setGameDetail(detail);
		} catch (err) {
			console.error("Error loading game detail:", err);
			setError("Failed to load game details. Please try again.");
		} finally {
			setLoading(false);
		}
	};

	// Handle session selection change
	const handleSessionChange = (newSessionId) => {
		navigate(`/games/poetry-slam/timeline/${newSessionId}`);
	};

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
			<div className="mb-8 mt-4">
				<h2 className="text-xl font-bold text-center mb-1">
					Poetry Session Details
				</h2>
				<p className="text-sm text-center text-gray-600 mb-6">
					View prompts, poems, and voting results from poetry slam
					sessions
				</p>

				{/* Session selector - updated to use URL params */}
				<div className="mb-6 flex items-center align-start">
					<div className="align-start">
						<label
							htmlFor="session-select"
							className="block text-sm font-small text-gray-700 mb-1 mr-3 "
						>
							Select Session:
						</label>
					</div>
					<select
						id="session-select"
						className="w-50 border border-gray-300 rounded-md p-2"
						value={sessionId || ""}
						onChange={(e) => handleSessionChange(e.target.value)}
					>
						{gameSessions?.map((session, index) => {
							return (
								<option key={session.id} value={session.id}>
									Session {index + 1}
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
								<div className="mb-2 flex items-center gap-4">
									<p className="text-sm text-gray-600 flex items-center">
										{gameDetail.game?.players?.length || 0}{" "}
										participants
									</p>
									<p className="text-sm text-gray-600 flex items-center">
										<Calendar size={14} className="mr-1" />
										{promptCreation
											? formatTimestamp(
													promptCreation.timestamp
											  )
											: getSessionDate(sessionId)}
									</p>
								</div>
								<div className="mt-3">
									<p className="font-medium mb-1 flex">
										Final scores:
									</p>
									<ol
										className={`list-none pl-5 columns-1 sm:columns-3 gap-8`}
									>
										{Array.isArray(finalScores) ? (
											finalScores.map((score, index) => {
												const highestScore = Math.max(
													...finalScores.map(
														(s) => s.score
													)
												);
												const isHighestScore =
													score.score ===
														highestScore &&
													score.score > 0;
												return (
													<li className="break-inside-avoid">
														<div
															key={index}
															className="text-sm flex items-center"
														>
															{isHighestScore && (
																<Trophy
																	size={14}
																	className="mr-1 text-yellow-500"
																/>
															)}
															{shortenModelName(
																score.model
															)}
															: {score.score}
														</div>
													</li>
												);
											})
										) : (
											<div className="text-sm">
												{finalScores}
											</div>
										)}
									</ol>
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
									<div className="p-6 max-w-none">
										<div
											className="bg-lime-50 text-lime-800 p-4 rounded border border-lime-100 whitespace-pre-line"
											dangerouslySetInnerHTML={{
												__html: convertStarsToBold(
													prompt.text
												),
											}}
										></div>
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
