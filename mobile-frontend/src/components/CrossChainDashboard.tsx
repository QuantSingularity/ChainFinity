// src/components/CrossChainDashboard.tsx
"use client";

import { motion } from "framer-motion";
import { ArrowRightLeft } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

// Mock data for demonstration
const mockCrossChainData = [
  {
    id: "txn1",
    fromChain: "Ethereum",
    toChain: "Polygon",
    asset: "USDC",
    amount: "1,000",
    status: "Completed",
    timestamp: "2024-04-30T10:00:00Z",
  },
  {
    id: "txn2",
    fromChain: "Arbitrum",
    toChain: "Optimism",
    asset: "ETH",
    amount: "0.5",
    status: "Pending",
    timestamp: "2024-04-30T10:05:00Z",
  },
  {
    id: "txn3",
    fromChain: "Polygon",
    toChain: "Ethereum",
    asset: "MATIC",
    amount: "500",
    status: "Failed",
    timestamp: "2024-04-30T09:55:00Z",
  },
];

// Helper to get status badge variant
const getStatusVariant = (
  status: string,
): "default" | "secondary" | "destructive" | "outline" => {
  switch (status.toLowerCase()) {
    case "completed":
      return "default"; // Use default (often green or blue)
    case "pending":
      return "secondary"; // Use secondary (often yellow or gray)
    case "failed":
      return "destructive"; // Use destructive (often red)
    default:
      return "outline";
  }
};

export function CrossChainDashboard() {
  // In a real application, you would fetch this data from an API
  const data = mockCrossChainData;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="w-full"
    >
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center">
            <ArrowRightLeft className="h-5 w-5 mr-2 text-blue-500" />{" "}
            Cross-Chain Activity
          </CardTitle>
          <CardDescription>
            Overview of recent cross-chain transactions and bridging activity.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {data.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Asset</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>From</TableHead>
                  <TableHead>To</TableHead>
                  <TableHead className="text-right">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((txn) => (
                  <TableRow key={txn.id}>
                    <TableCell className="font-medium">{txn.asset}</TableCell>
                    <TableCell>{txn.amount}</TableCell>
                    <TableCell>{txn.fromChain}</TableCell>
                    <TableCell>{txn.toChain}</TableCell>
                    <TableCell className="text-right">
                      <Badge variant={getStatusVariant(txn.status)}>
                        {txn.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center text-muted-foreground py-4">
              No recent cross-chain activity found.
            </div>
          )}
          {/* Placeholder for charts or further details */}
          {/* <div className="mt-6 text-center text-sm text-muted-foreground">
            <TrendingUp className="inline h-4 w-4 mr-1" /> More analytics coming soon...
          </div> */}
        </CardContent>
      </Card>
    </motion.div>
  );
}
