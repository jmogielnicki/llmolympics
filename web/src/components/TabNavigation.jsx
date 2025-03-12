import React from "react";

/**
 * Reusable tab navigation component
 * @param {Object} props
 * @param {string} props.activeTab - Current active tab ID
 * @param {Array} props.tabs - Array of tab objects with {id, label}
 * @param {Function} props.onTabChange - Function to call when tab is changed
 */
const TabNavigation = ({ activeTab, tabs, onTabChange }) => {
	return (
		<div className="mb-8">
			<div className="flex border-b border-gray-200">
				{tabs.map((tab) => (
					<button
						key={tab.id}
						className={`px-4 py-2 font-medium text-sm ${
							activeTab === tab.id
								? "border-b-2 border-blue-500 text-blue-600"
								: "text-gray-500 hover:text-gray-700"
						}`}
						onClick={() => onTabChange(tab.id)}
					>
						{tab.label}
					</button>
				))}
			</div>
		</div>
	);
};

export default TabNavigation;
