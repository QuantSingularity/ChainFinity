import { useState } from "react";
import { Button } from "../../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { useWeb3Context } from "../../context/Web3Context";
import { formatAddress } from "../../utils/formatters";

const DelegationManager = ({ delegatedTo, delegatedFrom, onDelegate }) => {
  const { account } = useWeb3Context();
  const [delegateAddress, setDelegateAddress] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleDelegate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess(false);

    try {
      // Validate address
      if (!delegateAddress || !ethers.utils.isAddress(delegateAddress)) {
        throw new Error("Invalid address");
      }

      const result = await onDelegate(delegateAddress);
      if (result) {
        setSuccess(true);
        setDelegateAddress("");
      }
    } catch (err) {
      setError(err.message || "Failed to delegate");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Delegation</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {delegatedTo ? (
            <div className="p-3 bg-gray-100 dark:bg-gray-800 rounded-md">
              <p className="text-sm font-medium mb-1">
                Currently delegated to:
              </p>
              <div className="flex items-center justify-between">
                <span className="text-sm">{formatAddress(delegatedTo)}</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onDelegate(account)}
                  disabled={loading}
                >
                  Undelegate
                </Button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleDelegate} className="space-y-3">
              <div className="space-y-2">
                <label
                  htmlFor="delegateAddress"
                  className="text-sm font-medium"
                >
                  Delegate your voting power
                </label>
                <div className="flex space-x-2">
                  <Input
                    id="delegateAddress"
                    value={delegateAddress}
                    onChange={(e) => setDelegateAddress(e.target.value)}
                    placeholder="0x..."
                    disabled={loading}
                  />
                  <Button type="submit" disabled={loading}>
                    {loading ? "Delegating..." : "Delegate"}
                  </Button>
                </div>
                {error && <p className="text-xs text-red-500">{error}</p>}
                {success && (
                  <p className="text-xs text-green-500">
                    Successfully delegated!
                  </p>
                )}
              </div>
            </form>
          )}

          {delegatedFrom.length > 0 && (
            <div className="pt-2">
              <p className="text-sm font-medium mb-2">Delegated from:</p>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {delegatedFrom.map((delegation, index) => (
                  <div
                    key={index}
                    className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-800 rounded"
                  >
                    <span className="text-xs">
                      {formatAddress(delegation.address)}
                    </span>
                    <span className="text-xs font-medium">
                      {formatNumber(delegation.amount)} CFG
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default DelegationManager;
