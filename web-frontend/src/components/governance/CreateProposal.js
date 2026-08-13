import SendIcon from "@mui/icons-material/Send";
import {
  Autocomplete,
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { blockchainAPI } from "../../services/api";
import { isValidAddress } from "../../utils/helpers";

const CreateProposal = ({ onSubmit }) => {
  const [form, setForm] = useState({
    title: "",
    description: "",
    calldata: "",
    targetAddress: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState({});
  // ChainFinity's own deployed contracts (AssetVault, CrossChainManager,
  // etc.), fetched so the target-address field can offer them by name
  // instead of requiring the proposer to know/paste a raw address. This is
  // a convenience only - free text (any valid address) is still accepted,
  // and an empty list here (e.g. backend unreachable) just leaves the
  // field behaving like a plain text input.
  const [knownContracts, setKnownContracts] = useState([]);

  useEffect(() => {
    let cancelled = false;
    blockchainAPI
      .getDeployedContracts()
      .then((response) => {
        if (!cancelled) setKnownContracts(response.data.contracts || []);
      })
      .catch(() => {
        // Backend/RPC unreachable - the field just falls back to free text.
        if (!cancelled) setKnownContracts([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const validate = () => {
    const e = {};
    if (!form.title.trim()) e.title = "Title is required";
    if (!form.description.trim()) e.description = "Description is required";
    if (form.title.length > 200) e.title = "Title must be under 200 characters";
    // Target address is optional, but when provided it must be a valid
    // Ethereum address; previously any string was accepted and submitted.
    if (
      form.targetAddress.trim() &&
      !isValidAddress(form.targetAddress.trim())
    ) {
      e.targetAddress = "Enter a valid Ethereum address (0x + 40 hex chars)";
    }
    return e;
  };

  const handleChange = (field) => (e) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: undefined }));
  };

  const setTargetAddress = (value) => {
    setForm((prev) => ({ ...prev, targetAddress: value || "" }));
    if (errors.targetAddress) {
      setErrors((prev) => ({ ...prev, targetAddress: undefined }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }
    setSubmitting(true);
    try {
      if (onSubmit) {
        await onSubmit(form);
      }
      setForm({ title: "", description: "", calldata: "", targetAddress: "" });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card
      sx={{
        border: (theme) => `1px solid ${theme.palette.divider}`,
        boxShadow: "none",
      }}
    >
      <CardContent>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Create New Proposal
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Submit a governance proposal for the ChainFinity community to vote on.
        </Typography>
        <Divider sx={{ mb: 3 }} />

        <Box component="form" onSubmit={handleSubmit} noValidate>
          <TextField
            fullWidth
            label="Proposal Title"
            required
            value={form.title}
            onChange={handleChange("title")}
            error={Boolean(errors.title)}
            helperText={errors.title || `${form.title.length}/200`}
            sx={{ mb: 3 }}
          />

          <TextField
            fullWidth
            label="Description"
            required
            multiline
            rows={5}
            value={form.description}
            onChange={handleChange("description")}
            error={Boolean(errors.description)}
            helperText={
              errors.description ||
              "Explain what this proposal does and why it should be approved."
            }
            sx={{ mb: 3 }}
          />

          <Autocomplete
            freeSolo
            fullWidth
            options={knownContracts}
            getOptionLabel={(option) =>
              typeof option === "string" ? option : option.address
            }
            filterOptions={(options, state) => {
              const input = state.inputValue.trim().toLowerCase();
              if (!input) return options;
              return options.filter(
                (o) =>
                  o.name.toLowerCase().includes(input) ||
                  o.address.toLowerCase().includes(input),
              );
            }}
            inputValue={form.targetAddress}
            onInputChange={(_e, value) => setTargetAddress(value)}
            onChange={(_e, option) =>
              setTargetAddress(
                option && typeof option !== "string" ? option.address : option,
              )
            }
            renderOption={(props, option) => (
              <Box component="li" {...props} key={option.address}>
                <Box>
                  <Typography variant="body2">{option.name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {option.address}
                  </Typography>
                </Box>
              </Box>
            )}
            renderInput={(params) => (
              <TextField
                {...params}
                label="Target Contract Address (Optional)"
                placeholder="0x... or select a ChainFinity contract"
                error={Boolean(errors.targetAddress)}
                helperText={
                  errors.targetAddress ||
                  "The contract address this proposal will interact with"
                }
              />
            )}
            sx={{ mb: 3 }}
          />

          <TextField
            fullWidth
            label="Calldata (Optional)"
            placeholder="0x..."
            value={form.calldata}
            onChange={handleChange("calldata")}
            helperText="Encoded function call data for on-chain execution"
            sx={{ mb: 3 }}
          />

          <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
            <Button
              type="submit"
              variant="contained"
              size="large"
              startIcon={<SendIcon />}
              disabled={submitting}
              sx={{ minWidth: 180 }}
            >
              {submitting ? "Submitting..." : "Submit Proposal"}
            </Button>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default CreateProposal;
