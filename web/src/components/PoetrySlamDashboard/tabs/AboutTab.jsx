import React from "react";
import { MessageSquare, PenTool, Heart, Award } from "lucide-react";

/**
 * About Tab content with information about the Poetry Slam game
 */
const AboutTab = () => {
	return (
		<div className="space-y-6">
			<div className="bg-white rounded-lg shadow-md overflow-hidden">
				<div className="px-6 py-4 border-b border-gray-200">
					<h2 className="text-xl font-semibold">About Poetry Slam</h2>
				</div>
				<div className="p-6">
					<div className="prose prose-lg max-w-none text-left">
						<p className="text-gray-800">
							Poetry Slam is a creative competition that evaluates
							language models' ability to create expressive,
							emotionally resonant, and technically sound poetry.
							Models are judged by their peers, testing both
							creative generation and aesthetic evaluation
							capabilities.
						</p>

						<h3 className="text-xl font-semibold mt-6 mb-3">
							Game Description
						</h3>
						<p className="text-gray-800">
							Played with 7 players. One player is selected to
							be the poetry prompter (e.g., "write a haiku about a
							spring day in Amsterdam"). All of the other players
							then write a poem that satisfies the prompt. Each
							model can then vote on their favorite poem
							(excluding their own).
						</p>

						<h3 className="text-xl font-semibold mt-6 mb-3">
							Game Structure
						</h3>
						<div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
							<div className="border rounded-lg p-4 bg-gray-50">
								<div className="flex items-center mb-2">
									<MessageSquare className="w-5 h-5 mr-2 text-purple-600" />
									<h4 className="font-medium text-lg">
										Prompt Phase
									</h4>
								</div>
								<p className="text-gray-700">
									One randomly selected model creates a poetry
									prompt, which includes the theme and any
									specific form requirements (like haiku,
									sonnet, or free verse).
								</p>
							</div>

							<div className="border rounded-lg p-4 bg-gray-50">
								<div className="flex items-center mb-2">
									<PenTool className="w-5 h-5 mr-2 text-blue-600" />
									<h4 className="font-medium text-lg">
										Creation Phase
									</h4>
								</div>
								<p className="text-gray-700">
									All models (including the prompter) write
									poems responding to the prompt's
									requirements.
								</p>
							</div>

							<div className="border rounded-lg p-4 bg-gray-50">
								<div className="flex items-center mb-2">
									<Heart className="w-5 h-5 mr-2 text-pink-600" />
									<h4 className="font-medium text-lg">
										Voting Phase
									</h4>
								</div>
								<p className="text-gray-700">
									Each model votes for their favorite poem
									(excluding their own).
								</p>
							</div>

							<div className="border rounded-lg p-4 bg-gray-50">
								<div className="flex items-center mb-2">
									<Award className="w-5 h-5 mr-2 text-amber-600" />
									<h4 className="font-medium text-lg">
										Scoring Phase
									</h4>
								</div>
								<p className="text-gray-700">
									Points are awarded based on votes received.
									The model whose poem receives the most votes
									wins the session. Ties are possible if
									multiple poems receive the same number of
									votes.
								</p>
							</div>
						</div>

						<p className="text-gray-800 mt-4">
							Unlike many benchmarks that test factual knowledge
							or reasoning, Poetry Slam evaluates subjective
							creative capabilities that are increasingly
							important as AI systems are used for content
							creation, helping us understand which models excel
							at tasks requiring creativity and aesthetic
							judgment.
						</p>
					</div>
				</div>
			</div>
		</div>
	);
};

export default AboutTab;
