// src/components/AssetAllocator.tsx
"use client";

import { motion } from "framer-motion";
import { DollarSign, PieChart as PieChartIcon } from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts"; // Using recharts, already in dependencies
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";

// Mock data for demonstration
const mockAssetData = [
  { name: "Bitcoin (BTC)", value: 40000, fill: "hsl(var(--chart-1))" },
  { name: "Ethereum (ETH)", value: 30000, fill: "hsl(var(--chart-2))" },
  { name: "Polygon (MATIC)", value: 15000, fill: "hsl(var(--chart-3))" },
  { name: "Solana (SOL)", value: 10000, fill: "hsl(var(--chart-4))" },
  { name: "Stablecoins (USDC)", value: 5000, fill: "hsl(var(--chart-5))" },
];

const totalValue = mockAssetData.reduce((acc, curr) => acc + curr.value, 0);

export function AssetAllocator() {
  // In a real application, fetch asset data based on connected wallet
  const data = mockAssetData;

  const chartConfig = {
    value: {
      label: "Value (USD)",
      icon: DollarSign,
    },
    btc: { label: "Bitcoin", color: "hsl(var(--chart-1))" },
    eth: { label: "Ethereum", color: "hsl(var(--chart-2))" },
    matic: { label: "Polygon", color: "hsl(var(--chart-3))" },
    sol: { label: "Solana", color: "hsl(var(--chart-4))" },
    usdc: { label: "Stablecoins", color: "hsl(var(--chart-5))" },
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.4 }}
      className="w-full"
    >
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center">
            <PieChartIcon className="h-5 w-5 mr-2 text-purple-500" /> Asset
            Allocation
          </CardTitle>
          <CardDescription>
            Distribution of assets across your portfolio.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {data.length > 0 ? (
            <ChartContainer
              config={chartConfig}
              className="mx-auto aspect-square h-[250px]"
            >
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <ChartTooltip
                    cursor={false}
                    content={<ChartTooltipContent hideLabel nameKey="name" />}
                  />
                  <Pie
                    data={data}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    innerRadius={50} // Make it a donut chart
                    labelLine={false}
                    // label={({ cx, cy, midAngle, innerRadius, outerRadius, percent, index }) => {
                    //   const RADIAN = Math.PI / 180;
                    //   const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
                    //   const x = cx + radius * Math.cos(-midAngle * RADIAN);
                    //   const y = cy + radius * Math.sin(-midAngle * RADIAN);
                    //   return (
                    //     <text x={x} y={y} fill="white" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central">
                    //       {`${(percent * 100).toFixed(0)}%`}
                    //     </text>
                    //   );
                    // }}
                  >
                    {data.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <ChartLegend
                    content={
                      <ChartLegendContent nameKey="name" className="text-xs" />
                    }
                    verticalAlign="bottom"
                    align="center"
                    wrapperStyle={{ marginTop: "20px" }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </ChartContainer>
          ) : (
            <div className="text-center text-muted-foreground py-4">
              No asset data available.
            </div>
          )}
          <div className="text-center mt-4 text-lg font-semibold">
            Total Value: ${totalValue.toLocaleString()}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
