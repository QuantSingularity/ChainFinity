import { Assessment as AssessmentIcon } from "@mui/icons-material";
import {
  Box,
  Card,
  CardContent,
  Chip,
  Divider,
  Typography,
} from "@mui/material";
import { formatLargeNumber } from "../../utils/helpers";

const GovernanceStats = ({
  totalSupply,
  votingDelay,
  votingPeriod,
  proposalThreshold,
}) => {
  const stats = [
    {
      label: "Total Supply",
      value: `${formatLargeNumber(Number(totalSupply))} CFG`,
      color: "primary",
    },
    { label: "Voting Delay", value: votingDelay, color: "default" },
    { label: "Voting Period", value: votingPeriod, color: "default" },
    {
      label: "Proposal Threshold",
      value: `${proposalThreshold} CFG`,
      color: "default",
    },
  ];

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
          <AssessmentIcon color="primary" sx={{ mr: 1 }} />
          <Typography variant="h6" fontWeight={600}>
            Governance Statistics
          </Typography>
        </Box>
        <Divider sx={{ mb: 2 }} />
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {stats.map(({ label, value, color }) => (
            <Box
              key={label}
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <Typography variant="body2" color="text.secondary">
                {label}
              </Typography>
              <Chip
                label={value}
                size="small"
                color={color}
                variant={color === "primary" ? "filled" : "outlined"}
              />
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

export default GovernanceStats;
