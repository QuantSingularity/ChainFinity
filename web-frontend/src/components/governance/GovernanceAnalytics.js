import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../components/ui/tabs";

const GovernanceAnalytics = ({ governanceData }) => {
  // Sample data for charts - in production this would come from the governanceData prop
  const participationData = [
    { month: "Jan", participation: 45 },
    { month: "Feb", participation: 52 },
    { month: "Mar", participation: 48 },
    { month: "Apr", participation: 61 },
    { month: "May", participation: 58 },
    { month: "Jun", participation: 65 },
  ];

  const proposalStatusData = [
    { name: "Passed", value: 24, color: "#10b981" },
    { name: "Failed", value: 8, color: "#ef4444" },
    { name: "Pending", value: 3, color: "#f59e0b" },
    { name: "Executed", value: 18, color: "#3b82f6" },
  ];

  const votingDistributionData = [
    { name: "Top 10 Holders", value: 42, color: "#8b5cf6" },
    { name: "Next 40 Holders", value: 28, color: "#6366f1" },
    { name: "Remaining Holders", value: 30, color: "#a78bfa" },
  ];

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Governance Analytics</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="participation" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="participation">Participation</TabsTrigger>
            <TabsTrigger value="proposals">Proposals</TabsTrigger>
            <TabsTrigger value="distribution">Distribution</TabsTrigger>
          </TabsList>

          <TabsContent value="participation" className="pt-4">
            <h3 className="text-sm font-medium mb-4">
              Monthly Voting Participation
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={participationData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis tickFormatter={(value) => `${value}%`} />
                  <Tooltip
                    formatter={(value) => [`${value}%`, "Participation"]}
                  />
                  <Bar dataKey="participation" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="text-xs text-gray-500 mt-4 text-center">
              Average participation rate: 54.8%
            </p>
          </TabsContent>

          <TabsContent value="proposals" className="pt-4">
            <h3 className="text-sm font-medium mb-4">Proposal Outcomes</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={proposalStatusData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) =>
                      `${name}: ${(percent * 100).toFixed(0)}%`
                    }
                  >
                    {proposalStatusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Legend />
                  <Tooltip formatter={(value) => [value, "Proposals"]} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <p className="text-xs text-gray-500 mt-4 text-center">
              Total proposals:{" "}
              {proposalStatusData.reduce((sum, item) => sum + item.value, 0)}
            </p>
          </TabsContent>

          <TabsContent value="distribution" className="pt-4">
            <h3 className="text-sm font-medium mb-4">
              Voting Power Distribution
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={votingDistributionData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) =>
                      `${name}: ${(percent * 100).toFixed(0)}%`
                    }
                  >
                    {votingDistributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Legend />
                  <Tooltip
                    formatter={(value) => [`${value}%`, "Voting Power"]}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <p className="text-xs text-gray-500 mt-4 text-center">
              Governance token holders: 1,245
            </p>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default GovernanceAnalytics;
