import { Badge } from "../../components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { formatNumber } from "../../utils/formatters";

const GovernanceStats = ({
  totalSupply,
  votingDelay,
  votingPeriod,
  proposalThreshold,
}) => {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Governance Statistics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-sm">Total Supply</span>
            <Badge variant="secondary">{formatNumber(totalSupply)} CFG</Badge>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-sm">Voting Delay</span>
            <Badge variant="outline">{votingDelay}</Badge>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-sm">Voting Period</span>
            <Badge variant="outline">{votingPeriod}</Badge>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-sm">Proposal Threshold</span>
            <Badge variant="outline">{proposalThreshold} CFG</Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default GovernanceStats;
