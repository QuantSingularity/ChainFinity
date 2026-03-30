// src/app/dashboard/page.tsx
"use client";

import { motion } from "framer-motion";
import { AssetAllocator } from "@/components/AssetAllocator"; // Import the AssetAllocator component
import { CrossChainDashboard } from "@/components/CrossChainDashboard"; // Import the CrossChainDashboard component
import { WalletInfo } from "@/components/WalletInfo"; // Import the WalletInfo component

export default function DashboardPage() {
  return (
    <main className="container mx-auto px-4 py-8 flex flex-col items-center space-y-8">
      <motion.h1
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-3xl font-bold tracking-tight text-center bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-cyan-500 dark:from-indigo-400 dark:to-cyan-400"
      >
        Dashboard
      </motion.h1>

      {/* Wallet Information Card */}
      <div className="w-full max-w-md">
        <WalletInfo />
      </div>

      {/* Asset Allocator Component */}
      <div className="w-full max-w-md">
        <AssetAllocator />
      </div>

      {/* Cross-Chain Dashboard Component */}
      <div className="w-full max-w-4xl">
        <CrossChainDashboard />
      </div>

      {/* Placeholder for other dashboard components */}
      {/* <div className="text-center text-muted-foreground pt-4">
        <p>(User Profile/Settings component will be added here.)</p>
      </div> */}
    </main>
  );
}
