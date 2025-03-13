import React from "react";
import { Link, useLocation } from "react-router-dom";

/**
 * Reusable tab navigation component with React Router integration
 * @param {Object} props
 * @param {Array} props.tabs - Array of tab objects with {id, label, path}
 * @param {string} props.basePath - Base path for the tabs
 */
const TabNavigation = ({ tabs, basePath }) => {
	const location = useLocation();
	const currentPath = location.pathname;

	return (
		<div className="mb-8">
			{/* Scrollable tab bar on small screens */}
			<div className="overflow-x-auto pb-1">
				<div className="flex border-b border-gray-200 min-w-max justify-center">
					{tabs.map((tab) => {
						const isActive =
							currentPath === `${basePath}/${tab.id}` ||
							(tab.id === "leaderboard" &&
								currentPath === basePath);

						return (
							<Link
								key={tab.id}
								to={
									tab.id === "leaderboard"
										? basePath
										: `${basePath}/${tab.id}`
								}
								className={`px-2 sm:px-4 py-2 text-xs sm:text-sm whitespace-nowrap ${
									isActive
										? "border-b-2 border-sky-500 text-sky-500 font-bold"
										: "text-gray-500 hover:text-gray-700 font-medium "
								}`}
							>
								{tab.label}
							</Link>
						);
					})}
				</div>
			</div>
		</div>
	);
};

export default TabNavigation;
