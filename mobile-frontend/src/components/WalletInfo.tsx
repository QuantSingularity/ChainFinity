// src/components/WalletInfo.tsx
"use client";

import { motion } from "framer-motion";
import { Check, Copy, Network, Wallet } from "lucide-react";
import React from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useApp } from "@/context/AppContext";
import { formatAddress } from "@/utils/helpers"; // Assuming this helper exists

export function WalletInfo() {
  const { wallet, actions, loading } = useApp();
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    if (wallet.address) {
      navigator.clipboard.writeText(wallet.address);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500); // Reset icon after 1.5 seconds
    }
  };

  if (loading) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <Skeleton className="h-6 w-3/4" />
          <Skeleton className="h-4 w-1/2 mt-1" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-10 w-full mt-2" />
        </CardContent>
      </Card>
    );
  }

  if (!wallet.isConnected) {
    return (
      <Card className="w-full max-w-md text-center">
        <CardHeader>
          <CardTitle className="flex items-center justify-center">
            <Wallet className="h-5 w-5 mr-2" /> Wallet Not Connected
          </CardTitle>
          <CardDescription>
            Connect your wallet to view details.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={actions.connectWallet} className="w-full">
            <Wallet className="h-4 w-4 mr-2" /> Connect Wallet
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Wallet className="h-5 w-5 mr-2 text-green-500" /> Wallet Connected
          </CardTitle>
          <CardDescription>Your connected wallet details.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Status:</span>
            <span className="font-medium text-green-600 dark:text-green-400">
              Connected
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Network:</span>
            <span className="font-medium flex items-center">
              <Network className="h-4 w-4 mr-1.5 text-blue-500" />
              {wallet.network || "N/A"}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Address:</span>
            <div className="flex items-center font-mono">
              {wallet.address ? formatAddress(wallet.address) : "N/A"}
              {wallet.address && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 ml-1"
                  onClick={handleCopy}
                >
                  {copied ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                  <span className="sr-only">Copy address</span>
                </Button>
              )}
            </div>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Balance:</span>
            <span className="font-medium">{wallet.balance || "N/A"}</span>
          </div>
          <Button
            variant="outline"
            onClick={actions.disconnectWallet}
            className="w-full mt-4"
          >
            Disconnect Wallet
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  );
}
