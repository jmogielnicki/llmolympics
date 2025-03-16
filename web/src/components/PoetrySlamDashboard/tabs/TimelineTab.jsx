import React, { useState, useEffect } from "react";
import { useGameData } from "../../../context/GameDataContext";
import PoemDisplay from "../components/PoemDisplay";
import { Calendar, MessageSquare } from "lucide-react";
import { shortenModelName } from "../../../utils/commonUtils";

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

		return gameDetail.poems.map((poem) => ({
			...poem,
			votedBy: playerVotes[poem.id] || [],
		}));
	};

	const poems = formatPoems();
	const prompt = gameDetail?.prompt;

	const formatTimestamp = (timestamp) => {
		if (!timestamp) return "";

		// Extract date from format like "2025-03-14 21:48:41"
		const parts = timestamp.split(" ");
		if (parts.length === 2) {
			const datePart = parts[0];
			const dateParts = datePart.split("-");
			if (dateParts.length === 3) {
				return `${dateParts[1]}/${dateParts[2]}/${dateParts[0]}`;
			}
		}
		return timestamp;
	};

	const getSessionDate = (sessionId) => {
		if (!sessionId) return "";

		// Extract timestamp from session ID like "poetry_slam_20250314_214841"
		const match = sessionId.match(/\d{8}_\d{6}/);
		if (match) {
			const timestamp = match[0];
			const year = timestamp.substring(0, 4);
			const month = timestamp.substring(4, 6);
			const day = timestamp.substring(6, 8);
			const hour = timestamp.substring(9, 11);
			const minute = timestamp.substring(11, 13);

			return `${month}/${day}/${year} ${hour}:${minute}`;
		}

		return sessionId;
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
						{gameSessions?.map((session) => (
							<option key={session.id} value={session.id}>
								{session.title} - {getSessionDate(session.id)}
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
								Loading session details...
							</p>
						</div>
					</div>
				) : (
					gameDetail && (
						<div className="space-y-6">
							{/* Session metadata */}
							<div className="bg-indigo-50 rounded-lg p-4 flex flex-col sm:flex-row justify-between">
								<div>
									<h3 className="text-lg font-semibold">
										{gameDetail.game?.summary
											?.winning_model_name
											? `${shortenModelName(
													gameDetail.game.summary
														.winning_model_name
											  )} won!`
											: "Poetry Slam Session"}
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
								<div className="mt-2 sm:mt-0">
									<p className="text-sm text-gray-600">
										Final scores:{" "}
										{gameDetail.game?.summary
											?.final_scores_display || ""}
									</p>
									<p className="text-sm text-gray-600">
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
										<div className="whitespace-pre-line bg-yellow-50 p-4 rounded border border-yellow-100">
											{prompt.text}
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
									<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
