import React from "react";
import {
	Lock, // Prisoner's Dilemma
	BookOpen, // Ghost
	Users, // Diplomacy
	DollarSign, // Ultimatum Game
	Hand, // Rock Paper Scissors
} from "lucide-react";

/**
 * Reusable game hero section component with game icon, title, and information
 * @param {Object} props
 * @param {string} props.gameId - ID of the current game
 * @param {string} props.title - Title of the current game
 * @param {string} props.description - Brief description of the game
 * @param {string} props.longDescription - Longer description of the game
 * @param {Object} props.stats - Game statistics object
 * @param {number} props.stats.gameCount - Number of games played
 * @param {number} props.stats.modelCount - Number of models
 * @param {string} props.stats.lastUpdated - Last updated date
 */
const GameHeroSection = ({ gameId, title, description, longDescription, stats }) => {
	// Map of game IDs to icons
	const gameIcons = {
		prisoners_dilemma: <Lock className="w-6 h-6" />,
		ghost: <BookOpen className="w-6 h-6" />,
		diplomacy: <Users className="w-6 h-6" />,
		ultimatum_game: <DollarSign className="w-6 h-6" />,
		rock_paper_scissors: <Hand className="w-6 h-6" />,
	};

	// Get the icon based on gameId or use a default
	const icon = gameIcons[gameId] || null;

	return (
		<div className="mb-6 max-w-4xl mx-auto">
			<div className="flex flex-col items-center justify-center mb-10">
				<div className="flex items-center mb-2">
					{icon && <div className="mr-3 text-gray-700">{icon}</div>}
					<h2 className="text-2xl font-semibold">{title}</h2>
				</div>

				{description && (
					<div className="mb-2">
						<p className="text-gray-600 text-lg text-center mb-2">
							{description}
						</p>
					</div>
				)}

				{longDescription && (
					<div className="mb-2">
						<p className="text-gray-600 text-sm text-center mb-2">
							{longDescription}
						</p>
					</div>
				)}

				{stats && (
					<p className="text-sm text-gray-500 text-center">
						{stats.gameCount > 0
							? `${stats.gameCount} games played between ${stats.modelCount} models • Last updated ${stats.lastUpdated}`
							: "No games played yet"}
					</p>
				)}
			</div>
		</div>
	);
};

export default GameHeroSection;
