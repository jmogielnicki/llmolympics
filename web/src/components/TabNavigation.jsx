import React from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { BarChart, TrendingUp, PlaySquare, Info, Vote, Sword } from "lucide-react";

/**
 * Reusable tab navigation component with React Router integration
 * @param {Object} props
 * @param {Array} props.tabs - Array of tab objects with {id, label, path}
 * @param {string} props.basePath - Base path for the tabs
 */
const TabNavigation = ({ tabs, basePath }) => {
	const location = useLocation();
	const currentPath = location.pathname;
	const { sessionId } = useParams(); // Get the sessionId from URL params if available

	// Get icon based on tab ID
	const getTabIcon = (tabId) => {
		switch (tabId) {
			case "leaderboard":
				return <BarChart size={16} />;
			case "voting-patterns":
				return <Vote size={16} />;
			case "timeline": // We'll replace this with "matches" in actual usage
			case "matches": // Support both old and new ID until fully migrated
				return <PlaySquare size={16} />;
			case "about":
				return <Info size={16} />;
			case "game-stats":
				return <TrendingUp size={16} />;
			case "matchups":
				return <Sword size={16} />;
			default:
				return null;
		}
	};

	return (
		<div>
			{/* Scrollable tab bar on small screens */}
			<div className="overflow-x-auto">
				<div className="flex border-b border-gray-200 min-w-max">
					{tabs.map((tab) => {
						// For the matches/timeline tab, check if we should include the session ID
						// Support both timeline and matches IDs until fully migrated
						const isTimelineOrMatches =
							tab.id === "timeline" || tab.id === "matches";

						const tabPath =
							isTimelineOrMatches && sessionId
								? `${basePath}/${tab.id}/${sessionId}`
								: tab.id === "leaderboard"
								? basePath
								: `${basePath}/${tab.id}`;

						// Determine if this tab is active using a simplified logic
						let isActive;

						if (isTimelineOrMatches) {
							// Check if the current path contains "/timeline" or "/matches" anywhere in it
							isActive =
								currentPath.includes("/timeline") ||
								currentPath.includes("/matches");
						} else if (tab.id === "leaderboard") {
							// Leaderboard is active if we're at the base path or the leaderboard path
							isActive =
								currentPath === basePath ||
								currentPath === `${basePath}/leaderboard`;
						} else {
							// For any other tab, check for an exact path match
							isActive = currentPath === `${basePath}/${tab.id}`;
						}

						const icon = getTabIcon(tab.id);

						return (
							<Link
								key={tab.id}
								to={tabPath}
								className={`
									flex items-center px-2 sm:px-4 py-2 sm:py-3 
									text-xs sm:text-sm font-medium transition-all duration-200
									relative mr-1 rounded-t-lg whitespace-nowrap
									${
										isActive
											? "text-orange-600 border-b-2 border-orange-600 bg-orange-50 font-bold"
											: "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
									}
								`}
							>
								{icon && <span className="sm:mr-2 mr-1">{icon}</span>}
								{tab.label}
								{isActive && (
									<div className="absolute bottom-0 left-0 w-full h-0.5 bg-orange-600"></div>
								)}
							</Link>
						);
					})}
				</div>
			</div>
		</div>
	);
};

export default TabNavigation;
