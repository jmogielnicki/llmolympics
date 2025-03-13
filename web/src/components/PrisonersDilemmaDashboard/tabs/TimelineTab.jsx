import React, { useState, useEffect } from "react";
import { useGameData } from "../context/GameDataContext";

// Import components
import MatchupSelector from "../components/MatchupSelector";
import GameDetailView from "../components/GameDetailView";

/**
 * Timeline Tab content
 * Shows detailed game progression and decisions
 */
const TimelineTab = () => {
	const { matchups, loadGameDetail } = useGameData();
	const [selectedMatchup, setSelectedMatchup] = useState("");
	const [gameDetail, setGameDetail] = useState(null);
	const [isLoadingDetail, setIsLoadingDetail] = useState(false);

	// Get the selected matchup data
	const getSelectedMatchupData = () => {
		return (
			matchups.find((m) => m.id === selectedMatchup) ||
			(matchups.length > 0 ? matchups[0] : null)
		);
	};

	// Set initial matchup on component mount
	useEffect(() => {
		if (matchups.length > 0 && !selectedMatchup) {
			setSelectedMatchup(matchups[0].id);
		}
	}, [matchups]);

	// Load game detail when a matchup is selected
	useEffect(() => {
		const fetchGameDetail = async () => {
			const matchup = getSelectedMatchupData();
			if (matchup && matchup.session_id) {
				setIsLoadingDetail(true);
				const detail = await loadGameDetail(matchup.session_id);
				setGameDetail(detail);
				setIsLoadingDetail(false);
			} else {
				setGameDetail(null);
			}
		};

		fetchGameDetail();
	}, [selectedMatchup, loadGameDetail]);

	const handleSelectMatchup = (matchupId) => {
		setSelectedMatchup(matchupId);
	};

	const selectedMatchupData = getSelectedMatchupData();

	return (
		<div className="space-y-6">
			<div className="bg-white rounded-lg shadow-md overflow-hidden">
				<div className="px-6 py-4 border-b border-gray-200">
					<h2 className="text-xl font-semibold">
						Game Timeline View
					</h2>
					<p className="text-gray-600 text-sm">
						Detailed progression of individual matchups with
						decisions and reasoning
					</p>
				</div>
				<div className="p-6">
					<MatchupSelector
						matchups={matchups}
						selectedMatchup={selectedMatchup}
						onSelectMatchup={handleSelectMatchup}
					/>

					<GameDetailView
						matchup={selectedMatchupData}
						gameDetail={gameDetail}
						isLoading={isLoadingDetail}
					/>
				</div>
			</div>
		</div>
	);
};

export default TimelineTab;
