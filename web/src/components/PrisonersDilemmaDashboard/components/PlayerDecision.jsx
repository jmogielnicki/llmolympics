import React from "react";
import { Check, X } from "lucide-react";

export const PlayerDecision = ({ modelName, decision }) => {
	if (!decision) return null;

	const isCooperate = decision.decision === "cooperate";

	return (
		<div className="border border-gray-200 rounded-md overflow-hidden">
			<div className="flex items-center gap-2 p-3 border-b border-gray-200">
				<span
					className={`h-4 w-4 rounded-full ${
						isCooperate ? "bg-green-500" : "bg-red-500"
					}`}
				>
					{isCooperate ? (
						<Check className="h-4 w-4 text-white" />
					) : (
						<X className="h-4 w-4 text-white" />
					)}
				</span>
				<span className="font-medium">{modelName}</span>
				<span className="ml-auto text-sm">
					{isCooperate ? "Cooperated" : "Defected"}
				</span>
			</div>

			<div className="p-3 text-sm bg-gray-50">
				{decision.reasoning}
			</div>
		</div>
	);
};
