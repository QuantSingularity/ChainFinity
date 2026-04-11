import {
  CheckCircle as ForIcon,
  Cancel as AgainstIcon,
  RemoveCircle as AbstainIcon,
} from "@mui/icons-material";
import {
  Box,
  Button,
  ButtonGroup,
  Card,
  CardContent,
  Chip,
  Divider,
  LinearProgress,
  Typography,
} from "@mui/material";
import { formatLargeNumber } from "../../utils/helpers";

const statusColor = (status) => {
  switch (status) {
    case "active": return "success";
    case "pending": return "warning";
    case "executed": return "info";
    case "defeated": return "error";
    default: return "default";
  }
};

const ProposalCard = ({ proposal, onVote }) => {
  const totalVotes =
    parseFloat(proposal.forVotes) +
    parseFloat(proposal.againstVotes) +
    parseFloat(proposal.abstainVotes);
  const forPct = totalVotes > 0 ? (parseFloat(proposal.forVotes) / totalVotes) * 100 : 0;
  const againstPct = totalVotes > 0 ? (parseFloat(proposal.againstVotes) / totalVotes) * 100 : 0;

  const daysLeft = Math.max(
    0,
    Math.ceil((proposal.eta - Date.now()) / (1000 * 60 * 60 * 24))
  );

  return (
    <Card sx={{ mb: 2, border: (theme) => `1px solid ${theme.palette.divider}`, boxShadow: "none" }}>
      <CardContent>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", mb: 1 }}>
          <Typography variant="subtitle1" fontWeight={700}>
            #{proposal.id} {proposal.title}
          </Typography>
          <Chip
            label={proposal.status.toUpperCase()}
            color={statusColor(proposal.status)}
            size="small"
            sx={{ ml: 1, flexShrink: 0 }}
          />
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {proposal.description}
        </Typography>

        <Typography variant="caption" color="text.secondary" gutterBottom display="block">
          Proposed by {proposal.proposer} · {daysLeft}d remaining
        </Typography>

        {totalVotes > 0 && (
          <Box sx={{ my: 2 }}>
            <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
              <Typography variant="caption" color="success.main">For: {forPct.toFixed(1)}%</Typography>
              <Typography variant="caption" color="error.main">Against: {againstPct.toFixed(1)}%</Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={forPct}
              color="success"
              sx={{ height: 8, borderRadius: 4, mb: 0.5 }}
            />
            <Box sx={{ display: "flex", justifyContent: "space-between" }}>
              <Typography variant="caption" color="text.secondary">
                {formatLargeNumber(Number(proposal.forVotes))} CFG for
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {formatLargeNumber(Number(proposal.againstVotes))} CFG against
              </Typography>
            </Box>
          </Box>
        )}

        {proposal.status === "active" && (
          <>
            <Divider sx={{ my: 1.5 }} />
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <Typography variant="body2" fontWeight={600} sx={{ mr: 1 }}>
                Cast Vote:
              </Typography>
              <ButtonGroup size="small" variant="outlined">
                <Button
                  color="success"
                  startIcon={<ForIcon />}
                  onClick={() => onVote(proposal.id, 1)}
                >
                  For
                </Button>
                <Button
                  color="error"
                  startIcon={<AgainstIcon />}
                  onClick={() => onVote(proposal.id, 0)}
                >
                  Against
                </Button>
                <Button
                  color="warning"
                  startIcon={<AbstainIcon />}
                  onClick={() => onVote(proposal.id, 2)}
                >
                  Abstain
                </Button>
              </ButtonGroup>
            </Box>
          </>
        )}
      </CardContent>
    </Card>
  );
};

const ProposalList = ({ proposals, onVote }) => {
  if (!proposals || proposals.length === 0) {
    return (
      <Box sx={{ textAlign: "center", py: 6 }}>
        <Typography color="text.secondary">No proposals found.</Typography>
      </Box>
    );
  }

  return (
    <Box>
      {proposals.map((proposal) => (
        <ProposalCard key={proposal.id} proposal={proposal} onVote={onVote} />
      ))}
    </Box>
  );
};

export default ProposalList;
