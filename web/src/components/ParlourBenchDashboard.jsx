import React, { useState } from "react";
import {
	BrowserRouter as Router,
	Routes,
	Route,
	Navigate,
	useNavigate,
} from "react-router-dom";
import { ChevronDown } from "lucide-react";
import PrisonersDilemmaDashboard from "./PrisonersDilemmaDashboard";

/**
 * Main ParlourBench Dashboard component
 * Houses the game selector and handles navigation between different game dashboards
 */
const ParlourBenchDashboard = () => {
	// Available games
	const games = [
		{
			id: "prisoners_dilemma",
			name: "Prisoner's Dilemma",
			path: "/games/prisoners-dilemma",
		},
		{ id: "ghost", name: "Ghost", path: "/games/ghost", comingSoon: true },
		{
			id: "diplomacy",
			name: "Diplomacy",
			path: "/games/diplomacy",
			comingSoon: true,
		},
		{
			id: "ultimatum_game",
			name: "Ultimatum Game",
			path: "/games/ultimatum-game",
			comingSoon: true,
		},
		{
			id: "rock_paper_scissors",
			name: "Rock Paper Scissors",
			path: "/games/rock-paper-scissors",
			comingSoon: true,
		},
	];

	return (
		<Router>
			<div className="container mx-auto p-4 max-w-6xl">
				<header className="mb-4 text-center">
					<h1 className="text-3xl font-bold mt-4 mb-2">
						ParlourBench Dashboard
					</h1>
					<p className="text-lg text-gray-600 mb-6">
						An open-source benchmark that pits LLMs against one
						another in parlour games
					</p>

					{/* Game Selector - Now rendered at the ParlourBench level */}
					<GameSelector games={games} />
				</header>

				<Routes>
					<Route
						path="/games/prisoners-dilemma"
						element={<PrisonersDilemmaDashboard />}
					/>
					<Route
						path="/games/:gameId"
						element={<ComingSoonGame games={games} />}
					/>
					<Route
						path="/"
						element={
							<Navigate replace to="/games/prisoners-dilemma" />
						}
					/>
				</Routes>
			</div>

			{/* Common footer across all games */}
			<footer className="mt-12 pt-6 border-t border-gray-200 text-center text-gray-600 text-sm">
				<p>
					ParlourBench is an open-source project. View the code on
					<a
						href="https://github.com/jmogielnicki/parlourbench/"
						className="text-blue-600 hover:underline ml-1"
					>
						GitHub
					</a>
				</p>
				<p className="mt-2">© 2025 John Mogielnicki</p>
			</footer>
		</Router>
	);
};

/**
 * Game selector component with navigation
 */
const GameSelector = ({ games }) => {
	const navigate = useNavigate();

	const handleGameChange = (e) => {
		const selectedGame = games.find((game) => game.id === e.target.value);
		if (selectedGame) {
			navigate(selectedGame.path);
		}
	};

	// Find the current game based on the URL path
	const currentPath = window.location.pathname;
	const currentGame =
		games.find((game) => game.path === currentPath) || games[0];

	return (
		<div className="flex justify-center mb-6">
			<div className="inline-block relative">
				<select
					className="block appearance-none w-64 bg-white border border-gray-300 text-gray-700 py-2 px-4 pr-8 rounded leading-tight focus:outline-none focus:bg-white focus:border-blue-500"
					value={currentGame.id}
					onChange={handleGameChange}
				>
					{games.map((game) => (
						<option key={game.id} value={game.id}>
							{game.name}
							{game.comingSoon ? " (Coming Soon)" : ""}
						</option>
					))}
				</select>
				<div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
					<ChevronDown size={16} />
				</div>
			</div>
		</div>
	);
};

/**
 * Placeholder for games that are coming soon
 */
const ComingSoonGame = ({ games }) => {
	const currentPath = window.location.pathname;
	const currentGame = games.find((game) => game.path === currentPath) || {
		name: "Game",
	};

	return (
		<div className="bg-white rounded-lg shadow-md overflow-hidden">
			<div className="px-6 py-12 text-center">
				<h2 className="text-xl font-semibold text-gray-700 mb-4">
					{currentGame.name} Coming Soon
				</h2>
				<p className="text-gray-500 mb-6">
					We're currently collecting data for this game type. Check
					back soon!
				</p>
			</div>
		</div>
	);
};

export default ParlourBenchDashboard;
