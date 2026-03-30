"use client";
import { formatDistanceToNow } from "date-fns";
import { AnimatePresence, motion } from "framer-motion";
import { Clock, Plus } from "lucide-react";
import { useEffect, useOptimistic, useState, useTransition } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { getStats, incrementAndLog } from "./counter"; // Assuming this file exists and works

export default function Home() {
  const [stats, setStats] = useState<{
    count: number;
    recentAccess: { accessed_at: string }[];
  }>({
    count: 0,
    recentAccess: [],
  });
  const [optimisticStats, setOptimisticStats] = useOptimistic(stats);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    // Initial fetch - consider adding error handling
    getStats().then(setStats).catch(console.error);
  }, []);

  const handleClick = async () => {
    startTransition(async () => {
      // Optimistic update
      setOptimisticStats((currentStats) => ({
        count: currentStats.count + 1,
        recentAccess: [
          { accessed_at: new Date().toISOString() },
          ...currentStats.recentAccess.slice(0, 4),
        ],
      }));
      try {
        // Actual update
        const newStats = await incrementAndLog();
        setStats(newStats);
      } catch (error) {
        console.error("Failed to increment count:", error);
        // Optionally revert optimistic update or show error to user
        setStats(stats); // Revert to last known good state
      }
    });
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 sm:p-8 bg-gradient-to-br from-indigo-50 via-white to-cyan-50 dark:from-slate-900 dark:via-black dark:to-slate-800">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
      >
        <Card className="w-full max-w-md shadow-xl dark:bg-gray-900/80 backdrop-blur-sm border-gray-200 dark:border-gray-700/50">
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-cyan-500 dark:from-indigo-400 dark:to-cyan-400">
              ChainFinity Stats
            </CardTitle>
            <CardDescription className="text-gray-600 dark:text-gray-400 pt-1">
              Live view counter
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col items-center gap-6 p-6">
            <motion.div
              key={optimisticStats.count} // Animate when count changes
              initial={{ y: -10, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ type: "spring", stiffness: 300, damping: 15 }}
              className="text-6xl font-extrabold text-gray-800 dark:text-gray-100"
            >
              {optimisticStats.count}
            </motion.div>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Button
                onClick={handleClick}
                disabled={isPending}
                size="lg"
                className="w-full bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-700 hover:to-cyan-700 text-white font-semibold shadow-lg transition-all duration-300 ease-in-out transform hover:-translate-y-1 dark:text-gray-900"
              >
                <Plus className="h-5 w-5 mr-2" />
                {isPending ? "Incrementing..." : "Increment View"}
              </Button>
            </motion.div>
            <div className="w-full pt-4">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 text-center">
                Recent Activity
              </h3>
              <ScrollArea className="h-[120px] w-full rounded-md border border-gray-200 dark:border-gray-700/50 p-3 bg-gray-50/50 dark:bg-gray-800/30">
                <AnimatePresence initial={false}>
                  {optimisticStats.recentAccess.length > 0 ? (
                    optimisticStats.recentAccess.map((log, _i) => (
                      <motion.div
                        key={log.accessed_at} // Use timestamp as key for stability
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3 }}
                        className="flex items-center justify-center text-xs text-gray-500 dark:text-gray-400 py-1"
                      >
                        <Clock className="h-3 w-3 mr-1.5 flex-shrink-0" />
                        {formatDistanceToNow(new Date(log.accessed_at), {
                          addSuffix: true,
                        })}
                      </motion.div>
                    ))
                  ) : (
                    <div className="text-xs text-gray-400 dark:text-gray-500 text-center py-4">
                      No recent activity
                    </div>
                  )}
                </AnimatePresence>
              </ScrollArea>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </main>
  );
}
