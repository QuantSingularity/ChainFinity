import { Send as SendIcon } from "@mui/icons-material";
import {
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";

const CreateProposal = ({ onSubmit }) => {
  const [form, setForm] = useState({
    title: "",
    description: "",
    calldata: "",
    targetAddress: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState({});

  const validate = () => {
    const e = {};
    if (!form.title.trim()) e.title = "Title is required";
    if (!form.description.trim()) e.description = "Description is required";
    if (form.title.length > 200) e.title = "Title must be under 200 characters";
    return e;
  };

  const handleChange = (field) => (e) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: undefined }));
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
      await onSubmit(form);
      setForm({ title: "", description: "", calldata: "", targetAddress: "" });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card sx={{ border: (theme) => `1px solid ${theme.palette.divider}`, boxShadow: "none" }}>
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
            helperText={errors.description || "Explain what this proposal does and why it should be approved."}
            sx={{ mb: 3 }}
          />

          <TextField
            fullWidth
            label="Target Contract Address (Optional)"
            placeholder="0x..."
            value={form.targetAddress}
            onChange={handleChange("targetAddress")}
            helperText="The contract address this proposal will interact with"
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
