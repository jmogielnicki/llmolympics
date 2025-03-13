import React from "react";

/**
 * Component for selecting a matchup from available options
 *
 * @param {Object} props
 * @param {Array} props.matchups - Array of matchup objects
 * @param {string} props.selectedMatchup - ID of the currently selected matchup
 * @param {Function} props.onSelectMatchup - Callback when a matchup is selected
 */
const MatchupSelector = ({ matchups, selectedMatchup, onSelectMatchup }) => {
	return (
		<div className="flex flex-wrap gap-2 mb-6">
			{matchups.map((matchup) => (
				<button
					key={matchup.id}
					className={`px-4 py-2 text-sm rounded-full ${
						selectedMatchup === matchup.id
							? "bg-blue-500 text-white"
							: "bg-gray-200 text-gray-700 hover:bg-gray-300"
					}`}
					onClick={() => onSelectMatchup(matchup.id)}
				>
					{matchup.title}
				</button>
			))}
		</div>
	);
};

export default MatchupSelector;
