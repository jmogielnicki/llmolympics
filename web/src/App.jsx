import './App.css'
import ParlourBenchDashboard from './components/ParlourBenchDashboard'

function App() {

  return (
		<>
			<div>
				<header className="mb-4 text-center">
					<h1 className="text-3xl font-bold mt-4 mb-6">
						ParlourBench Dashboard
					</h1>
					<p className="text-lg text-gray-600 mb-2">
						An open-source benchmark that pits LLMs against one
						another in parlour games
					</p>
					<p className="text-sm text-gray-600 mb-6">
						View the code on
						<a
							href="https://github.com/jmogielnicki/parlourbench/"
							className="text-blue-600 hover:underline ml-1"
						>
							GitHub
						</a>
					</p>
				</header>
			</div>
			<ParlourBenchDashboard />

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
				<p className="mt-2"></p>
			</footer>
		</>
  );
}

export default App
