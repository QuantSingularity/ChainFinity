import { useState } from "react";
import { Alert, AlertDescription } from "../../components/ui/alert";
import { Button } from "../../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Textarea } from "../../components/ui/textarea";
import { useWeb3Context } from "../../context/Web3Context";

const CreateProposal = ({ onSubmit }) => {
  const { account } = useWeb3Context();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    actions: [{ target: "", value: "0", signature: "", calldata: "" }],
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleActionChange = (index, field, value) => {
    const newActions = [...formData.actions];
    newActions[index] = {
      ...newActions[index],
      [field]: value,
    };
    setFormData((prev) => ({
      ...prev,
      actions: newActions,
    }));
  };

  const addAction = () => {
    setFormData((prev) => ({
      ...prev,
      actions: [
        ...prev.actions,
        { target: "", value: "0", signature: "", calldata: "" },
      ],
    }));
  };

  const removeAction = (index) => {
    const newActions = [...formData.actions];
    newActions.splice(index, 1);
    setFormData((prev) => ({
      ...prev,
      actions: newActions,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess(false);

    try {
      // Validate form
      if (!formData.title.trim()) {
        throw new Error("Title is required");
      }
      if (!formData.description.trim()) {
        throw new Error("Description is required");
      }

      // Validate actions
      for (const [index, action] of formData.actions.entries()) {
        if (!action.target || !ethers.utils.isAddress(action.target)) {
          throw new Error(`Invalid target address in action ${index + 1}`);
        }
        if (action.signature.trim() === "") {
          throw new Error(
            `Function signature is required in action ${index + 1}`,
          );
        }
      }

      const result = await onSubmit(formData);
      if (result) {
        setSuccess(true);
        setFormData({
          title: "",
          description: "",
          actions: [{ target: "", value: "0", signature: "", calldata: "" }],
        });
      }
    } catch (err) {
      setError(err.message || "Failed to create proposal");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create New Proposal</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {success && (
            <Alert>
              <AlertDescription>
                Proposal created successfully!
              </AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <label htmlFor="title" className="text-sm font-medium">
              Title
            </label>
            <Input
              id="title"
              name="title"
              value={formData.title}
              onChange={handleChange}
              placeholder="Proposal Title"
              required
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="description" className="text-sm font-medium">
              Description
            </label>
            <Textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Describe your proposal in detail..."
              rows={6}
              required
            />
            <p className="text-xs text-gray-500">
              Markdown formatting is supported
            </p>
          </div>

          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-medium">Actions</h3>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={addAction}
              >
                Add Action
              </Button>
            </div>

            {formData.actions.map((action, index) => (
              <div key={index} className="p-4 border rounded-md space-y-4">
                <div className="flex justify-between items-center">
                  <h4 className="text-sm font-medium">Action {index + 1}</h4>
                  {formData.actions.length > 1 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeAction(index)}
                    >
                      Remove
                    </Button>
                  )}
                </div>

                <div className="space-y-2">
                  <label className="text-xs">Target Contract</label>
                  <Input
                    value={action.target}
                    onChange={(e) =>
                      handleActionChange(index, "target", e.target.value)
                    }
                    placeholder="0x..."
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs">Value (ETH)</label>
                  <Input
                    type="number"
                    min="0"
                    step="0.0001"
                    value={action.value}
                    onChange={(e) =>
                      handleActionChange(index, "value", e.target.value)
                    }
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs">Function Signature</label>
                  <Input
                    value={action.signature}
                    onChange={(e) =>
                      handleActionChange(index, "signature", e.target.value)
                    }
                    placeholder="transfer(address,uint256)"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs">Calldata (hex)</label>
                  <Input
                    value={action.calldata}
                    onChange={(e) =>
                      handleActionChange(index, "calldata", e.target.value)
                    }
                    placeholder="0x..."
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="pt-4">
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Creating..." : "Create Proposal"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default CreateProposal;
