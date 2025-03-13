import {
	HashRouter as Router,
	Routes,
	Route,
	Navigate,
	useNavigate,
	Link,
	Outlet,
	useLocation,
	useParams,
} from "react-router-dom";
import { ChevronDown, Info, Github, Home, Lock, Users } from "lucide-react";
import PrisonersDilemmaDashboard from "./PrisonersDilemmaDashboard/components/PrisonersDilemmaDashboard";

/**
 * Main ParlourBench Dashboard component
 * Houses the game selector and handles navigation between different game dashboards
 */
const ParlourBenchDashboard = () => {
	// Available games with descriptions
	const games = [
		{
			id: "prisoners_dilemma",
			name: "Prisoner's Dilemma",
			path: "/games/prisoners-dilemma",
			description: "A classic game of cooperation and betrayal",
			long_description: `
              For each of 5 rounds, players simultaneously choose to cooperate or
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
				{/* Header */}
				<header className="bg-white shadow-sm border-b">
					<div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center h-20 py-3">
						<div className="flex-1 text-left">
							<h1 className="text-2xl font-bold text-gray-900">
								ParlourBench
							</h1>
							<p className="text-sm text-gray-600">
								Evaluating LLMs through competitive gameplay
							</p>
						</div>
						<nav className="flex space-x-6">
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
					</div>
				</header>

				{/* Main Content */}
				<main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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

				{/* Common footer across all games */}
				<footer className="bg-white border-t border-gray-200 py-6 mt-12">
					<div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-gray-600 text-sm">
						<p>
							ParlourBench is an open-source project. View the
							code on
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
 * Game selector component with navigation
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
		<div className="mb-8 mt-6 flex justify-left items-center">
			<span className="mr-2 text-gray-700">Select Game:</span>
			<div className="relative inline-block">
				<select
					className="appearance-none bg-white border border-gray-300 text-gray-700 py-2 px-4 pr-8 rounded leading-tight focus:outline-none focus:bg-white focus:border-blue-500"
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
 * Game Info Card component
 */
const GameInfoCard = ({ games }) => {
	const location = useLocation();
	const currentGame =
		games.find((game) => {
			return location.pathname.includes(game.path.replace(/^\//, ""));
		}) || games[0];

	return (
		<div className="bg-indigo-50 rounded-lg shadow-sm overflow-hidden mb-6">
			<div className="flex items-left p-4">
				<div className="flex-shrink-0 mr-4 bg-indigo-100 rounded-full p-1 text-left w-16 h-16 flex items-center justify-center">
					<span className="text-3xl">{currentGame.icon}</span>
				</div>
				<div>
					<h2 className="text-2xl font-bold text-gray-900 text-left">
						{currentGame.name}
					</h2>
					<p className="text-gray-600">{currentGame.description}</p>
				</div>
			</div>

			{currentGame.long_description && (
				<div className="p-4 border-t border-indigo-100">
					<p className="text-gray-700 text-sm text-left">
						{currentGame.long_description}
					</p>
				</div>
			)}

			{currentGame.stats && (
				<div className="bg-indigo-100 px-6 py-3 flex justify-center items-center text-sm text-gray-500">
					<div className="flex items-center">
						<Users size={14} className="mr-1" />
						<span>
							{currentGame.stats.gameCount} games played between{" "}
							{currentGame.stats.modelCount} models • Last updated{" "}
							{currentGame.stats.lastUpdated}
						</span>
					</div>
				</div>
			)}
		</div>
	);
};

/**
 * Placeholder for games that are coming soon
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
