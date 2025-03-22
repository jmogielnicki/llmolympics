import React from "react";
import { Calendar, Trophy, Users } from "lucide-react";

const DebateSessionHeader = ({
	debateData,
	selectedSession,
	getSessionDate,
}) => {
	// Find winner among debaters
	const winnerPlayerId = debateData?.summary?.winner?.player_id;

	return (
		<div className="bg-indigo-50 rounded-lg p-4 mb-6">
			<div>
				<h3 className="font-semibold text-lg mb-3">
					{debateData.topic}
				</h3>

				<div className="mb-4">
					<div className="flex items-center mb-2">
						<Users size={16} className="mr-2 text-black-600" />
						<h4 className="text-sm text-black-800">Debaters:</h4>
					</div>

					<div className="grid grid-cols-1 md:grid-cols-2 gap-2 ml-8">
						{debateData.debaters.map((debater) => (
							<div
								key={debater.player_id}
								className="flex items-center"
							>
								<span className={`text-sm text-gray-700`}>
									{debater.model || debater.player_id}
								</span>

								{debater.player_id === winnerPlayerId && (
									<Trophy
										size={16}
										className="ml-2 text-amber-500 fill-amber-500"
									/>
								)}
							</div>
						))}
					</div>
				</div>

				<div className="mb-4">
					<div className="flex items-center mb-2">
						<Users size={16} className="mr-2 text-black-600" />
						<h4 className="text-sm text-black-800">Judges:</h4>
					</div>

					<div className="grid grid-cols-1 md:grid-cols-3 gap-1 ml-8">
						{debateData.judges.map((judge) => (
							<div
								key={judge.player_id}
								className="text-gray-700 text-sm"
							>
								{judge.model || judge.player_id}
							</div>
						))}
					</div>
				</div>
			</div>
		</div>
	);
};

export default DebateSessionHeader;
