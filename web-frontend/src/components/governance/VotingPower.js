import { HowToVote as VoteIcon } from "@mui/icons-material";
import {
  Box,
  Card,
  CardContent,
  Divider,
  LinearProgress,
  Typography,
} from "@mui/material";
import { formatLargeNumber } from "../../utils/helpers";

const VotingPower = ({ userVotingPower, userTokenBalance, totalSupply }) => {
  const votingPct =
    totalSupply > 0
      ? (parseFloat(userVotingPower) / parseFloat(totalSupply)) * 100
      : 0;
  const delegatedPower =
    parseFloat(userVotingPower) - parseFloat(userTokenBalance);

  return (
    <Card
      sx={{
        height: "100%",
        border: (theme) => `1px solid ${theme.palette.divider}`,
        boxShadow: "none",
      }}
    >
      <CardContent>
        <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
          <VoteIcon color="primary" sx={{ mr: 1 }} />
          <Typography variant="h6" fontWeight={600}>
            Your Voting Power
          </Typography>
        </Box>
        <Divider sx={{ mb: 2 }} />

        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
            <Typography variant="body2" fontWeight={500}>
              Voting Power
            </Typography>
            <Typography variant="body2" fontWeight={600} color="primary">
              {formatLargeNumber(Number(userVotingPower))} CFG
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={Math.min(votingPct, 100)}
            sx={{ height: 8, borderRadius: 4 }}
          />
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ mt: 0.5, display: "block" }}
          >
            {votingPct.toFixed(4)}% of total supply
          </Typography>
        </Box>

        <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
          <Box sx={{ display: "flex", justifyContent: "space-between" }}>
            <Typography variant="body2" color="text.secondary">
              Token Balance
            </Typography>
            <Typography variant="body2" fontWeight={600}>
              {formatLargeNumber(Number(userTokenBalance))} CFG
            </Typography>
          </Box>
          <Box sx={{ display: "flex", justifyContent: "space-between" }}>
            <Typography variant="body2" color="text.secondary">
              Delegated Power
            </Typography>
            <Typography variant="body2" fontWeight={600}>
              {formatLargeNumber(Math.max(0, delegatedPower))} CFG
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default VotingPower;
