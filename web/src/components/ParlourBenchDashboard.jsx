import React, { useState } from "react";
import {
	HashRouter as Router,
	Routes,
	Route,
	Navigate,
	useNavigate,
	Link,
	Outlet,
} from "react-router-dom";
import { ChevronDown, Info, Github, Home } from "lucide-react";
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
				<header className="mb-4">
					{/* Responsive header - stacked on mobile, side by side on larger screens */}
					<div className="flex flex-col md:flex-row md:items-center mb-2">
						{/* Title - centered on all screens */}
						<h1 className="text-3xl font-bold mt-4 text-center w-full order-1">
							ParlourBench Dashboard
						</h1>

						{/* Navigation - centered on mobile, right-aligned on larger screens */}
						<nav className="flex space-x-4 w-full md:w-auto mt-4 md:mt-0 justify-center md:justify-end order-2 md:absolute md:right-8 md:top-6">
							<Link
								to="/"
								className="flex items-center text-gray-600 hover:text-blue-600"
							>
								<Home size={18} className="mr-1" />
								<span>Home</span>
							</Link>
							<Link
								to="/about"
								className="flex items-center text-gray-600 hover:text-blue-600"
							>
								<Info size={18} className="mr-1" />
								<span>About</span>
							</Link>
							<a
								href="https://github.com/jmogielnicki/parlourbench/"
								target="_blank"
								rel="noopener noreferrer"
								className="flex items-center text-gray-600 hover:text-blue-600"
							>
								<Github size={18} className="mr-1" />
								<span>GitHub</span>
							</a>
						</nav>
					</div>

					<p className="text-lg text-gray-600 mb-6 text-center">
						An open-source benchmark that pits LLMs against one
						another in parlour games
					</p>

					{/* Game Selector - Only shown on game pages, not on About page */}
					<Routes>
						<Route path="/about" element={null} />
						<Route
							path="*"
							element={<GameSelector games={games} />}
						/>
					</Routes>
				</header>

				<Routes>
					<Route
						path="/games/prisoners-dilemma/*"
						element={<PrisonersDilemmaDashboard />}
					/>
					<Route
						path="/games/:gameId"
						element={<ComingSoonGame games={games} />}
					/>
					<Route path="/about" element={<AboutParlourBench />} />
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

/**
 * About ParlourBench component with general project information
 */
const AboutParlourBench = () => {
	return (
		<div className="space-y-6">
			<div className="bg-white rounded-lg shadow-md overflow-hidden">
				<div className="px-6 py-4 border-b border-gray-200">
					<h2 className="text-xl font-semibold">
						About ParlourBench
					</h2>
				</div>
				<div className="p-6">
					<div className="prose prose-lg max-w-none text-left">
						<p className="text-gray-800">
							ParlourBench is an open-source benchmark platform
							that pits language models against each other in
							diverse parlour games to evaluate their strategic
							thinking, diplomatic prowess, creativity,
							persuasion, deceptive/cooperative behavior, and
							theory-of-mind capabilities.
						</p>

						<p className="text-gray-800 mt-4">
							Through these competitions, we develop comprehensive
							rankings across key dimensions and showcase them on
							our arena leaderboard. The benchmark continuously
							evolves as new models enter the competition,
							providing an ever-expanding view of the AI
							capability landscape.
						</p>

						<h3 className="text-xl font-semibold mt-6 mb-3">
							Why is this needed?
						</h3>
						<p className="text-gray-800">
							LLMs are quickly saturating traditional benchmarks -
							for example, they now achieve nearly 90% accuracy on
							MMLU. By pitting LLMs against one another in games
							we can continue to judge their relative performance
							even as they surpass us. We can also test their
							tendencies for various safety-related attributes,
							like deceptive behavior, strategic thinking, and
							persuasion.
						</p>

						<h3 className="text-xl font-semibold mt-6 mb-3">
							Project Principles
						</h3>
						<ul className="list-disc pl-6 space-y-2">
							<li className="text-gray-800">
								Games should not require human judgement,
								scoring, or other interventions.
							</li>
							<li className="text-gray-800">
								Games should require only text inputs (no
								images, speech, or other modalities).
							</li>
							<li className="text-gray-800">
								Games should test at least one of the following
								properties:
								<ul className="list-disc pl-6 mt-2 space-y-1">
									<li>Strategic thinking</li>
									<li>Persuasion</li>
									<li>Social intelligence</li>
									<li>Deception/trustworthiness</li>
									<li>
										Creativity (as judged by other models)
									</li>
									<li>Theory of mind</li>
								</ul>
							</li>
						</ul>

						<h3 className="text-xl font-semibold mt-6 mb-3">
							Available Games
						</h3>
						<div className="space-y-4">
							<div>
								<h4 className="text-lg font-semibold">
									Prisoner's Dilemma
								</h4>
								<p className="text-gray-800">
									A classic game that tests cooperation vs.
									competition. Players choose to cooperate or
									defect, with varying rewards based on the
									combined choices.
								</p>
							</div>

							<div>
								<h4 className="text-lg font-semibold">
									Ghost (Coming Soon)
								</h4>
								<p className="text-gray-800">
									A word game where players take turns adding
									letters, avoiding completing a valid word.
								</p>
							</div>

							<div>
								<h4 className="text-lg font-semibold">
									Diplomacy (Coming Soon)
								</h4>
								<p className="text-gray-800">
									A game of alliance building and strategic
									elimination featuring LLM players with
									simple identifiers.
								</p>
							</div>

							<div>
								<h4 className="text-lg font-semibold">
									Ultimatum Game (Coming Soon)
								</h4>
								<p className="text-gray-800">
									One player proposes how to split a sum, the
									other accepts or rejects the proposal.
								</p>
							</div>

							<div>
								<h4 className="text-lg font-semibold">
									Rock Paper Scissors (Coming Soon)
								</h4>
								<p className="text-gray-800">
									A multi-round tournament with discussion
									phases before each round.
								</p>
							</div>
						</div>

						<h3 className="text-xl font-semibold mt-6 mb-3">
							Get Involved
						</h3>
						<p className="text-gray-800">
							ParlourBench is an open-source project and welcomes
							contributions. Visit our{" "}
							<a
								href="https://github.com/jmogielnicki/parlourbench/"
								className="text-blue-600 hover:underline"
							>
								GitHub repository
							</a>{" "}
							to learn more about how you can contribute or use
							the benchmark for your own research.
						</p>
					</div>
				</div>
			</div>
		</div>
	);
};

export default ParlourBenchDashboard;
