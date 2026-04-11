"use client";
import { motion } from "framer-motion";
import { ArrowDownLeft, ArrowUpRight, Clock, RefreshCw } from "lucide-react";
import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useTransactionHistory } from "../../hooks/useProtocolData";

const mockTransactions = [
  {
    id: 1,
    type: "Deposit",
    amount: 500,
    date: "2024-10-01",
    status: "Completed",
  },
  {
    id: 2,
    type: "Loan Repayment",
    amount: 150,
    date: "2024-10-05",
    status: "Completed",
  },
  {
    id: 3,
    type: "Withdrawal",
    amount: 200,
    date: "2024-10-10",
    status: "Pending",
  },
  {
    id: 4,
    type: "Transfer",
    amount: 75,
    date: "2024-10-12",
    status: "Completed",
  },
  { id: 5, type: "Bridge", amount: 1000, date: "2024-10-14", status: "Failed" },
];

const statusVariant: Record<
  string,
  "default" | "secondary" | "destructive" | "outline"
> = {
  Completed: "default",
  Pending: "secondary",
  Failed: "destructive",
};

const TransactionsPage = () => {
  const { transactions, loading, error, refreshTransactions } =
    useTransactionHistory();

  const displayTransactions = (
    transactions?.length ? transactions : mockTransactions
  ) as typeof mockTransactions;

  return (
    <div className="container mx-auto max-w-2xl px-4 py-10 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-cyan-500 dark:from-indigo-400 dark:to-cyan-400">
            Transactions
          </h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Your full activity history.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refreshTransactions()}
          disabled={loading}
          className="flex items-center gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <div className="rounded-md bg-destructive/10 border border-destructive/30 px-4 py-3 text-sm text-destructive">
          {typeof error === "string"
            ? error
            : ((error as any)?.message ?? "An error occurred")}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent Activity</CardTitle>
          <CardDescription>
            {displayTransactions.length} transaction(s) found
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="divide-y divide-border">
              {Array.from({ length: 4 }).map((_, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between px-6 py-4"
                >
                  <div className="space-y-1.5">
                    <Skeleton className="h-4 w-28" />
                    <Skeleton className="h-3 w-40" />
                  </div>
                  <Skeleton className="h-6 w-16 rounded-full" />
                </div>
              ))}
            </div>
          ) : displayTransactions.length === 0 ? (
            <div className="text-center text-muted-foreground py-12 text-sm">
              No transactions found.
            </div>
          ) : (
            <div className="divide-y divide-border">
              {displayTransactions.map((tx, index) => (
                <motion.div
                  key={tx.id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.04 }}
                  className="flex items-center justify-between px-6 py-4 hover:bg-muted/40 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`flex h-9 w-9 items-center justify-center rounded-full text-white ${
                        tx.type === "Deposit"
                          ? "bg-green-500/15 text-green-600 dark:text-green-400"
                          : tx.type === "Withdrawal"
                            ? "bg-red-500/15 text-red-500"
                            : "bg-blue-500/15 text-blue-500"
                      }`}
                    >
                      {tx.type === "Deposit" ? (
                        <ArrowDownLeft className="h-4 w-4" />
                      ) : tx.type === "Withdrawal" ? (
                        <ArrowUpRight className="h-4 w-4" />
                      ) : (
                        <Clock className="h-4 w-4" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-medium leading-none">
                        {tx.type}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {tx.date}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-semibold">
                      {tx.type === "Withdrawal" ? "-" : "+"}$
                      {tx.amount.toLocaleString()}
                    </span>
                    <Badge variant={statusVariant[tx.status] ?? "outline"}>
                      {tx.status}
                    </Badge>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default TransactionsPage;
