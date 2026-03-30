import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Progress } from "../../components/ui/progress";
import { formatNumber } from "../../utils/formatters";

const VotingPower = ({ userVotingPower, userTokenBalance, totalSupply }) => {
  // Calculate percentage of total supply
  const votingPowerPercentage =
    (parseFloat(userVotingPower) / parseFloat(totalSupply)) * 100;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Your Voting Power</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-sm font-medium">Voting Power</span>
              <span className="text-sm font-medium">
                {formatNumber(userVotingPower)} CFG
              </span>
            </div>
            <Progress value={votingPowerPercentage} className="h-2" />
            <p className="text-xs text-gray-500 mt-1">
              {votingPowerPercentage.toFixed(4)}% of total supply
            </p>
          </div>

          <div className="pt-2">
            <div className="flex justify-between text-sm">
              <span>Token Balance:</span>
              <span className="font-medium">
                {formatNumber(userTokenBalance)} CFG
              </span>
            </div>

            <div className="flex justify-between text-sm mt-2">
              <span>Delegated Power:</span>
              <span className="font-medium">
                {formatNumber(
                  parseFloat(userVotingPower) - parseFloat(userTokenBalance),
                )}{" "}
                CFG
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default VotingPower;
