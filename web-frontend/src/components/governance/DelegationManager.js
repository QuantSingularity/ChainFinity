import { People as PeopleIcon } from "@mui/icons-material";
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { formatAddress } from "../../utils/helpers";

const DelegationManager = ({ delegatedTo, delegatedFrom, onDelegate }) => {
  const [delegateAddress, setDelegateAddress] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleDelegate = async () => {
    if (!delegateAddress.trim()) return;
    setSubmitting(true);
    try {
      await onDelegate(delegateAddress.trim());
      setDelegateAddress("");
    } finally {
      setSubmitting(false);
    }
  };

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
          <PeopleIcon color="primary" sx={{ mr: 1 }} />
          <Typography variant="h6" fontWeight={600}>
            Delegation
          </Typography>
        </Box>
        <Divider sx={{ mb: 2 }} />

        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Currently delegating to
          </Typography>
          <Chip
            label={
              delegatedTo ? formatAddress(delegatedTo) : "Self (not delegated)"
            }
            color={delegatedTo ? "primary" : "default"}
            size="small"
            variant="outlined"
          />
        </Box>

        {delegatedFrom.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Delegated from ({delegatedFrom.length})
            </Typography>
            {delegatedFrom.map((d, i) => (
              <Box
                key={i}
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  mb: 0.5,
                }}
              >
                <Typography variant="caption">{d.address}</Typography>
                <Typography variant="caption" fontWeight={600}>
                  {Number(d.amount).toLocaleString()} CFG
                </Typography>
              </Box>
            ))}
          </Box>
        )}

        <Divider sx={{ my: 2 }} />

        <Typography variant="body2" fontWeight={600} gutterBottom>
          Delegate Voting Power
        </Typography>
        <TextField
          fullWidth
          size="small"
          placeholder="0x... wallet address"
          value={delegateAddress}
          onChange={(e) => setDelegateAddress(e.target.value)}
          sx={{ mb: 1.5 }}
        />
        <Button
          fullWidth
          variant="contained"
          size="small"
          onClick={handleDelegate}
          disabled={submitting || !delegateAddress.trim()}
        >
          {submitting ? "Delegating..." : "Delegate"}
        </Button>
      </CardContent>
    </Card>
  );
};

export default DelegationManager;
