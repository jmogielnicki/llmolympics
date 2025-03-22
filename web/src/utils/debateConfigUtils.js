/**
 * Creates a consistent configuration for debate visualization
 *
 * @param {Object} debateData - The debate data containing debaters info
 * @returns {Object} - Configuration object with mappings for colors, positions, etc.
 */
export const createDebateConfig = (debateData) => {
	if (!debateData?.debaters || debateData.debaters.length !== 2) {
		console.error("Invalid debate data for configuration");
		return null;
	}

	const debater1 = debateData.debaters[0];
	const debater2 = debateData.debaters[1];

	// Create the configuration object
	const config = {
		// Fixed assignments (never change)
		debaterPositions: {
			[debater1.player_id]: "left",
			[debater2.player_id]: "right",
		},

		debaterColors: {
			[debater1.player_id]: "purple",
			[debater2.player_id]: "amber",
		},

		// Map sides to positions and debaters
		sideMap: {
			pre: {
				// Map side IDs to debater player IDs
				[debater1.pre_swap_side]: debater1.player_id,
				[debater2.pre_swap_side]: debater2.player_id,
				// Map positions to side IDs
				positions: {
					left: debater1.pre_swap_side,
					right: debater2.pre_swap_side,
				},
			},
			post: {
				// Map side IDs to debater player IDs (swapped in post phase)
				[debater1.post_swap_side]: debater1.player_id,
				[debater2.post_swap_side]: debater2.player_id,
				// Map positions to side IDs (swapped in post phase)
				positions: {
					left: debater1.post_swap_side,
					right: debater2.post_swap_side,
				},
			},
		},

		// Helper methods
		getDebaterPosition: (playerId) =>
			config.debaterPositions[playerId] || "left",

		getDebaterColor: (playerId) =>
			config.debaterColors[playerId] || "purple",

		getSideColor: (sideId, isPostSwap) => {
			const phase = isPostSwap ? "post" : "pre";
			const debaterId = config.sideMap[phase][sideId];
			return config.debaterColors[debaterId] || "purple";
		},

		getPositionColor: (position) =>
			position === "left" ? "purple" : "amber",

		getSideDebater: (sideId, isPostSwap) => {
			const phase = isPostSwap ? "post" : "pre";
			return config.sideMap[phase][sideId];
		},

		getPositionSide: (position, isPostSwap) => {
			const phase = isPostSwap ? "post" : "pre";
			return config.sideMap[phase].positions[position];
		},

		// Get the CSS class for a given color
		getColorClass: (color, element = "text", intensity = "600") =>
			`${element}-${color}-${intensity}`,
	};

	return config;
};
