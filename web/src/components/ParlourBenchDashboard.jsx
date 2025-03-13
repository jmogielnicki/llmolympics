import {
	HashRouter as Router,
	Routes,
	Route,
	Navigate,
	useNavigate,
	Link,
	useLocation,
	useParams,
} from "react-router-dom";
import { ChevronDown, Info, Github, Menu, X, Users } from "lucide-react";
import { useState } from "react";
import PrisonersDilemmaDashboard from "./PrisonersDilemmaDashboard/components/PrisonersDilemmaDashboard";
import AboutParlourBench from "./AboutParlourBench";

/**
 * Main ParlourBench Dashboard component
 * Houses the game selector and handles navigation between different game dashboards
 */
const ParlourBenchDashboard = () => {
	const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

	// Available games with descriptions
	const games = [
		{
			id: "prisoners_dilemma",
			name: "Prisoner's Dilemma",
			path: "/games/prisoners-dilemma",
			description: "A classic game of cooperation and betrayal",
			long_description: `
              For 5 rounds, players choose to cooperate or
              defect. Mutual cooperation yields moderate rewards
              for both (3,3), mutual defection yields low rewards
              (1,1), while unilateral defection yields high reward
              for the defector (5,0).
      `,
			icon: "🔒", // Lock icon as emoji alternative
			stats: {
				gameCount: 21,
				modelCount: 7,
				lastUpdated: "2025-03-12",
			},
		},
		{
			id: "ghost",
			name: "Ghost",
			path: "/games/ghost",
			comingSoon: true,
			icon: "👻", // Ghost emoji
			description: "A word game where players avoid completing words",
		},
		{
			id: "diplomacy",
			name: "Diplomacy",
			path: "/games/diplomacy",
			comingSoon: true,
			icon: "🤝", // Handshake emoji
			description:
				"A game of alliance building and strategic elimination",
		},
		{
			id: "ultimatum_game",
			name: "Ultimatum Game",
			path: "/games/ultimatum-game",
			comingSoon: true,
			icon: "💰", // Money bag emoji
			description: "A negotiation game testing fairness and strategy",
		},
		{
			id: "rock_paper_scissors",
			name: "Rock Paper Scissors",
			path: "/games/rock-paper-scissors",
			comingSoon: true,
			icon: "✂️", // Scissors emoji
			description: "A multi-round tournament with strategic deception",
		},
	];

	return (
		<Router>
			<div className="min-h-screen bg-gray-50">
				{/* Header - Improved for mobile */}
				<header className="bg-white shadow-sm border-b">
					<div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
						<div className="flex justify-between items-center h-16">
							{/* Logo and Tagline */}
							<div className="flex-1 text-left">
								<h1 className="text-xl sm:text-2xl font-bold text-gray-900">
									ParlourBench
								</h1>
								<p className="text-xs sm:text-sm text-gray-600">
									Evaluating LLMs through gameplay
								</p>
							</div>

							{/* Desktop Navigation */}
							<nav className="hidden md:flex space-x-6">
								<Link
									to="/"
									className="text-gray-600 hover:text-gray-900"
								>
									Home
								</Link>
								<Link
									to="/about"
									className="text-gray-600 hover:text-gray-900"
								>
									About
								</Link>
								<a
									href="https://github.com/jmogielnicki/parlourbench/"
									target="_blank"
									rel="noopener noreferrer"
									className="text-gray-600 hover:text-gray-900"
								>
									GitHub
								</a>
							</nav>

							{/* Mobile Menu Button */}
							<div className="md:hidden">
								<button
									type="button"
									className="text-gray-500 hover:text-gray-700 focus:outline-none"
									onClick={() =>
										setMobileMenuOpen(!mobileMenuOpen)
									}
								>
									{mobileMenuOpen ? (
										<X size={24} />
									) : (
										<Menu size={24} />
									)}
								</button>
							</div>
						</div>

						{/* Mobile Navigation */}
						{mobileMenuOpen && (
							<div className="md:hidden py-3 space-y-2 border-t border-gray-200">
								<Link
									to="/"
									className="block px-2 py-1 text-gray-600 hover:text-gray-900"
									onClick={() => setMobileMenuOpen(false)}
								>
									Home
								</Link>
								<Link
									to="/about"
									className="block px-2 py-1 text-gray-600 hover:text-gray-900"
									onClick={() => setMobileMenuOpen(false)}
								>
									About
								</Link>
								<a
									href="https://github.com/jmogielnicki/parlourbench/"
									target="_blank"
									rel="noopener noreferrer"
									className="block px-2 py-1 text-gray-600 hover:text-gray-900"
									onClick={() => setMobileMenuOpen(false)}
								>
									GitHub
								</a>
							</div>
						)}
					</div>
				</header>

				{/* Main Content - Improved padding for mobile */}
				<main className="max-w-6xl mx-auto px-3 sm:px-6 lg:px-8 py-4 sm:py-8">
					{/* Game Selector - Only shown on game pages, not on About page */}
					<Routes>
						<Route path="/about" element={null} />
						<Route
							path="*"
							element={<GameSelector games={games} />}
						/>
					</Routes>

					{/* Current Game Info - Only shown on game pages, not on About page */}
					<Routes>
						<Route path="/about" element={null} />
						<Route
							path="*"
							element={<GameInfoCard games={games} />}
						/>
					</Routes>
					{/* Main Content Routes */}
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
								<Navigate
									replace
									to="/games/prisoners-dilemma/leaderboard"
								/>
							}
						/>
					</Routes>
				</main>

				{/* Common footer across all games - Improved for mobile */}
				<footer className="bg-white border-t border-gray-200 py-4 sm:py-6 mt-8 sm:mt-12">
					<div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-gray-600 text-xs sm:text-sm">
						<p>
							ParlourBench is an open-source project. View on
							<a
								href="https://github.com/jmogielnicki/parlourbench/"
								className="text-blue-600 hover:underline ml-1"
							>
								GitHub
							</a>
						</p>
						<p className="mt-2">© 2025 John Mogielnicki</p>
					</div>
				</footer>
			</div>
		</Router>
	);
};

/**
 * Game selector component with navigation - Improved for mobile
 */
const GameSelector = ({ games }) => {
	const navigate = useNavigate();
	const location = useLocation();

	// Find the current game based on the current route path
	const currentGame =
		games.find((game) => {
			return location.pathname.includes(game.path.replace(/^\//, ""));
		}) || games[0];

	const handleGameChange = (e) => {
		const selectedGame = games.find((game) => game.id === e.target.value);
		if (selectedGame) {
			navigate(selectedGame.path);
		}
	};

	return (
		<div className="mb-6 sm:mb-8 mt-4 sm:mt-2">
			<div className="flex flex-col sm:flex-row sm:items-center">
				<span className="text-sm sm:text-base text-gray-700 mb-2 sm:mb-0 sm:mr-2">
					Select Game:
				</span>
				<div className="relative w-full sm:w-auto">
					<select
						className="appearance-none w-full sm:w-auto bg-white border border-gray-300 text-gray-700 py-2 px-3 pr-8 rounded leading-tight focus:outline-none focus:bg-white focus:border-blue-500"
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
		</div>
	);
};

/**
 * Game Info Card component - Improved for mobile
 */
const GameInfoCard = ({ games }) => {
	const location = useLocation();
	const currentGame =
		games.find((game) => {
			return location.pathname.includes(game.path.replace(/^\//, ""));
		}) || games[0];

	return (
		<div className="bg-indigo-50 rounded-lg shadow-sm overflow-hidden mb-4 sm:mb-6">
			<div className="flex flex-col sm:flex-row items-center sm:items-start p-3 sm:p-4">
				<div className="flex-shrink-0 mb-3 sm:mb-0 sm:mr-4 bg-indigo-100 rounded-full p-1 w-14 h-14 sm:w-16 sm:h-16 flex items-center justify-center">
					<span className="text-2xl sm:text-3xl">
						{currentGame.icon}
					</span>
				</div>
				<div className="text-center sm:text-left">
					<h2 className="text-xl sm:text-2xl font-bold text-gray-900">
						{currentGame.name}
					</h2>
					<p className="text-sm sm:text-base text-gray-600">
						{currentGame.description}
					</p>
				</div>
			</div>

			{currentGame.long_description && (
				<div className="p-3 sm:p-4 border-t border-indigo-100">
					<p className="text-xs sm:text-sm text-gray-700 text-left">
						{currentGame.long_description}
					</p>
				</div>
			)}

			{currentGame.stats && (
				<div className="bg-indigo-100 px-3 sm:px-6 py-2 sm:py-3 flex justify-left items-center text-xs sm:text-sm text-gray-500">
					<div className="flex flex-col sm:flex-row items-center text-left sm:text-left">
						<Users size={12} className="mb-1 sm:mb-0 sm:mr-1" />
						<span>
							<span className="hidden sm:inline">
								{currentGame.stats.gameCount} games played
								between {currentGame.stats.modelCount} models
							</span>
							<span className="sm:hidden">
								{currentGame.stats.gameCount} games •{" "}
								{currentGame.stats.modelCount} models
							</span>
							<span className="sm:inline">
								{" "}
								• Last updated {currentGame.stats.lastUpdated}
							</span>
						</span>
					</div>
				</div>
			)}
		</div>
	);
};

/**
 * Placeholder for games that are coming soon - Improved for mobile
 */
const ComingSoonGame = ({ games }) => {
	const location = useLocation();
	const currentGame = games.find((game) =>
		location.pathname.includes(game.path)
	) || {
		name: "Game",
	};

	return (
		<div className="bg-white rounded-lg shadow-md overflow-hidden">
			<div className="px-4 sm:px-6 py-8 sm:py-12 text-center">
				<h2 className="text-lg sm:text-xl font-semibold text-gray-700 mb-3 sm:mb-4">
					{currentGame.name} Coming Soon
				</h2>
				<p className="text-sm sm:text-base text-gray-500 mb-4 sm:mb-6">
					We're currently collecting data for this game type. Check
					back soon!
				</p>
			</div>
		</div>
	);
};

export default ParlourBenchDashboard;
