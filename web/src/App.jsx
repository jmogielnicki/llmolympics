import { useState } from 'react'
import './App.css'
import ParlourBenchDashboard from './components/ParlourBenchDashboard'

function App() {

  return (
		<>
			<div>
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
				<p className="mt-2">
				</p>
			</footer>
		</>
  );
}

export default App
