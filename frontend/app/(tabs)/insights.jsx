import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Dimensions,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  useColorScheme,
  View,
} from "react-native";
import { BarChart } from "react-native-chart-kit";
import { useAuth } from "../../contexts/AuthContext";

const { width } = Dimensions.get("window");
const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function Insights() {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";
  const { idToken } = useAuth();
  
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // New segregated data states
  const [quickStats, setQuickStats] = useState({ items: [] });
  const [spending, setSpending] = useState({ title: "", categories: [], total: "₹0" });
  const [goals, setGoals] = useState({ title: "", items: [], empty: "" });
  const [alerts, setAlerts] = useState([]);
  const [aiSummary, setAiSummary] = useState(null);
  const [aiInsights, setAiInsights] = useState([]);
  const [trendAnalysis, setTrendAnalysis] = useState(null);
  const [categoryBreakdown, setCategoryBreakdown] = useState([]);
  const [lastGeneratedAt, setLastGeneratedAt] = useState(null);
  const [fromCache, setFromCache] = useState(false);

  const theme = {
    background: isDark ? "#0a0a0a" : "#F8F9FA",
    card: isDark ? "#1a1a1a" : "#FFFFFF",
    text: isDark ? "#FFFFFF" : "#001F3F",
    textSecondary: isDark ? "#A0A0A0" : "#6B7280",
    border: isDark ? "#2a2a2a" : "#E5E7EB",
    primary: "#001F3F",
    warning: "#FF9800",
    success: "#4CAF50",
    danger: "#F44336",
    info: "#2196F3",
    accent: "#6366F1",
  };

  const applyDashboardData = useCallback((data) => {
    if (!data) return;

    setQuickStats(data.quick_stats || { items: [] });
    setSpending(data.spending || { title: "", categories: [], total: "₹0" });
    setGoals(data.goals || { title: "", items: [], empty: "" });
    setAlerts(data.alerts || []);
    setAiSummary(data.ai_summary || null);
    setAiInsights(data.ai_insights || []);
    setTrendAnalysis(data.trend_analysis || null);
    setCategoryBreakdown(data.category_breakdown || []);
    setLastGeneratedAt(data.generated_at ? new Date(data.generated_at) : null);
    setFromCache(Boolean(data.from_cache));
  }, []);

  const fetchInsights = useCallback(async (silent = false) => {
    if (!idToken) {
      setLoading(false);
      return;
    }

    try {
      if (!silent) setError(null);

      const response = await fetch(`${BACKEND_URL}/insights/ai/dashboard`, {
        headers: {
          Authorization: `Bearer ${idToken}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) throw new Error("Failed to fetch insights");

      const data = await response.json();
      applyDashboardData(data);
    } catch (err) {
      console.error("Error fetching insights:", err);
      if (!silent) setError(err.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [idToken, applyDashboardData]);

  useEffect(() => {
    fetchInsights();
  }, [fetchInsights]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchInsights(true);
  }, [fetchInsights]);

  const handleGenerateInsights = useCallback(async () => {
    if (!idToken) return;

    try {
      setError(null);
      setAiLoading(true);

      const response = await fetch(`${BACKEND_URL}/insights/ai/dashboard/regenerate`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${idToken}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) throw new Error("Failed to regenerate insights");

      const data = await response.json();
      applyDashboardData(data);
    } catch (err) {
      console.error("Error regenerating insights:", err);
      setError(err.message);
    } finally {
      setAiLoading(false);
      setLoading(false);
    }
  }, [idToken, applyDashboardData]);

  // Chart data from category breakdown - memoized to prevent recalculation
  const chartData = useMemo(() => ({
    labels: categoryBreakdown.length > 0 
      ? categoryBreakdown.map((c) => c.category?.substring(0, 6) || "Other")
      : ["No Data"],
    datasets: [{
      data: categoryBreakdown.length > 0 
        ? categoryBreakdown.map((c) => c.amount || 0)
        : [0],
    }],
  }), [categoryBreakdown]);

  // Get stat icon based on label
  const getStatIcon = (label) => {
    const lower = label?.toLowerCase() || "";
    if (lower.includes("aamdani") || lower.includes("income")) return "arrow-down-circle";
    if (lower.includes("kharcha") || lower.includes("expense")) return "arrow-up-circle";
    if (lower.includes("bachat") || lower.includes("saving")) return "wallet";
    if (lower.includes("health") || lower.includes("score")) return "heart";
    return "stats-chart";
  };

  // Get stat color based on label
  const getStatColor = (label) => {
    const lower = label?.toLowerCase() || "";
    if (lower.includes("aamdani") || lower.includes("income")) return theme.success;
    if (lower.includes("kharcha") || lower.includes("expense")) return theme.danger;
    if (lower.includes("bachat") || lower.includes("saving")) return theme.info;
    if (lower.includes("health") || lower.includes("score")) return theme.accent;
    return theme.primary;
  };

  // Get category icon
  const getCategoryIcon = (category) => {
    const icons = {
      Food: "restaurant",
      Bills: "document-text",
      Shopping: "cart",
      Travel: "airplane",
      Subscriptions: "refresh",
      Salary: "wallet",
      Freelance: "briefcase",
      Investment: "trending-up",
      Others: "ellipsis-horizontal",
    };
    return icons[category] || "ellipsis-horizontal";
  };

  if (loading) {
    return (
      <View style={[styles.container, styles.centered, { backgroundColor: theme.background }]}>
        <ActivityIndicator size="large" color={theme.primary} />
        <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
          Loading insights...
        </Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.background }]}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          tintColor={theme.primary}
          colors={[theme.primary]}
        />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={[styles.headerTitle, { color: theme.text }]}>
            Insights 💡
          </Text>
          <Text style={[styles.headerSubtitle, { color: theme.textSecondary }]}>
            {fromCache ? "Cached snapshot" : "Fresh analysis"}
          </Text>
        </View>
        <TouchableOpacity
          style={[styles.generateButton, aiLoading && styles.generateButtonDisabled]}
          onPress={handleGenerateInsights}
          disabled={aiLoading}
        >
          {aiLoading ? (
            <>
              <ActivityIndicator size="small" color="#FFFFFF" />
              <Text style={styles.generateButtonText}>AI soch raha...</Text>
            </>
          ) : (
            <>
              <Ionicons name="sparkles" size={18} color="#FFFFFF" />
              <Text style={styles.generateButtonText}>Naya Generate</Text>
            </>
          )}
        </TouchableOpacity>
      </View>

      {lastGeneratedAt && (
        <Text style={[styles.lastUpdatedText, { color: theme.textSecondary }]}>
          {lastGeneratedAt.toLocaleString()} {fromCache ? "• Cached" : ""}
        </Text>
      )}

      {error && (
        <View style={[styles.errorContainer, { backgroundColor: "#FFEBEE" }]}>
          <Ionicons name="warning" size={20} color="#F44336" />
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {/* AI Summary Card */}
      {aiSummary && (
        <View style={styles.section}>
          <LinearGradient
            colors={isDark ? ["#1a1a2e", "#16213e"] : ["#E8F5E9", "#C8E6C9"]}
            style={styles.summaryCard}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            <Text style={styles.summaryEmoji}>{aiSummary.emoji || "💡"}</Text>
            <Text style={[styles.summaryText, { color: theme.text }]}>
              {aiSummary.text}
            </Text>
            {aiSummary.ai && (
              <View style={styles.aiTag}>
                <Ionicons name="sparkles" size={12} color={theme.accent} />
                <Text style={[styles.aiTagText, { color: theme.accent }]}>AI</Text>
              </View>
            )}
          </LinearGradient>
        </View>
      )}

      {/* Quick Stats Grid */}
      {quickStats.items?.length > 0 && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>
            Quick Stats 📊
          </Text>
          <View style={styles.statsGrid}>
            {quickStats.items.map((stat, index) => (
              <View
                key={index}
                style={[styles.statCard, { backgroundColor: theme.card, borderColor: theme.border }]}
              >
                <View style={[styles.statIcon, { backgroundColor: `${getStatColor(stat.label)}20` }]}>
                  <Ionicons
                    name={getStatIcon(stat.label)}
                    size={20}
                    color={getStatColor(stat.label)}
                  />
                </View>
                <Text style={[styles.statLabel, { color: theme.textSecondary }]}>
                  {stat.label}
                </Text>
                <Text style={[styles.statValue, { color: theme.text }]}>
                  {stat.value}
                </Text>
                {stat.sub && (
                  <Text style={[styles.statSub, { color: theme.textSecondary }]}>
                    {stat.sub}
                  </Text>
                )}
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Spending Breakdown */}
      {spending.categories?.length > 0 && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>
              {spending.title || "Kahan Gaya Paisa? 💸"}
            </Text>
            <Text style={[styles.sectionTotal, { color: theme.danger }]}>
              {spending.total}
            </Text>
          </View>
          <View style={[styles.spendingCard, { backgroundColor: theme.card }]}>
            {spending.categories.map((cat, index) => (
              <View key={index} style={styles.spendingRow}>
                <View style={styles.spendingLeft}>
                  <View style={[styles.spendingIcon, { backgroundColor: isDark ? "#2a2a2a" : "#F5F5F5" }]}>
                    <Ionicons
                      name={getCategoryIcon(cat.name)}
                      size={18}
                      color={theme.primary}
                    />
                  </View>
                  <Text style={[styles.spendingName, { color: theme.text }]}>
                    {cat.name}
                  </Text>
                </View>
                <View style={styles.spendingRight}>
                  <Text style={[styles.spendingAmount, { color: theme.text }]}>
                    {cat.amount}
                  </Text>
                  <Text style={[styles.spendingPercent, { color: theme.textSecondary }]}>
                    {cat.percent}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Goals Progress */}
      {(goals.items?.length > 0 || goals.empty) && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>
            {goals.title || "Goals Progress 🎯"}
          </Text>
          {goals.items?.length > 0 ? (
            <View style={[styles.goalsCard, { backgroundColor: theme.card }]}>
              {goals.items.map((goal, index) => (
                <View key={index} style={styles.goalItem}>
                  <View style={styles.goalHeader}>
                    <Text style={[styles.goalName, { color: theme.text }]}>
                      {goal.title || goal.name}
                    </Text>
                    <Text style={[styles.goalProgress, { color: theme.accent }]}>
                      {goal.progress}
                    </Text>
                  </View>
                  <View style={[styles.progressBarBg, { backgroundColor: isDark ? "#2a2a2a" : "#E5E7EB" }]}>
                    <View
                      style={[
                        styles.progressBarFill,
                        { width: `${goal.progress}%`, backgroundColor: theme.accent }
                      ]}
                    />
                  </View>
                  <Text style={[styles.goalStatus, { color: theme.textSecondary }]}>
                    {goal.status}
                  </Text>
                </View>
              ))}
            </View>
          ) : (
            <View style={[styles.emptyCard, { backgroundColor: theme.card }]}>
              <Ionicons name="flag-outline" size={40} color={theme.textSecondary} />
              <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
                {goals.empty || "Koi goal nahi hai. Goals tab mein banao!"}
              </Text>
            </View>
          )}
        </View>
      )}

      {/* Smart Alerts */}
      {alerts?.length > 0 && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>
            Smart Alerts ⚡
          </Text>
          {alerts.map((alert, index) => (
            <View
              key={index}
              style={[
                styles.alertCard,
                { backgroundColor: alert.type === "warning" ? "#FFF3E0" : "#E8F5E9" }
              ]}
            >
              <Text style={styles.alertEmoji}>{alert.emoji || "⚠️"}</Text>
              <Text style={[
                styles.alertText,
                { color: alert.type === "warning" ? "#E65100" : "#2E7D32" }
              ]}>
                {alert.text}
              </Text>
            </View>
          ))}
        </View>
      )}

      {/* AI Insights */}
      {aiInsights?.length > 0 && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>
            AI Tips 🤖
          </Text>
          {aiInsights.map((insight, index) => (
            <View key={index} style={styles.insightWrapper}>
              <LinearGradient
                colors={isDark ? ["#1a1a2e", "#16213e"] : ["#E3F2FD", "#BBDEFB"]}
                style={styles.insightCard}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <Text style={styles.insightEmoji}>{insight.emoji || "💡"}</Text>
                <View style={styles.insightContent}>
                  <Text style={[styles.insightTitle, { color: theme.text }]}>
                    {insight.title}
                  </Text>
                  <Text style={[styles.insightDesc, { color: theme.textSecondary }]}>
                    {insight.text}
                  </Text>
                </View>
              </LinearGradient>
            </View>
          ))}
        </View>
      )}

      {/* Trend Analysis */}
      {trendAnalysis && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>
            Trend Analysis 📈
          </Text>
          <View style={[styles.trendCard, { backgroundColor: theme.card }]}>
            <View style={styles.trendHeader}>
              <Text style={styles.trendEmoji}>{trendAnalysis.emoji || "📈"}</Text>
              <View style={styles.trendInfo}>
                <Text style={[styles.trendTitle, { color: theme.text }]}>
                  {trendAnalysis.title || "Trend"}
                </Text>
                <Text style={[styles.trendDesc, { color: theme.textSecondary }]}>
                  {trendAnalysis.text}
                </Text>
              </View>
            </View>
          </View>
        </View>
      )}

      {/* Category Chart */}
      {categoryBreakdown.length > 0 && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>
            Category Breakdown 📊
          </Text>
          <View style={[styles.chartCard, { backgroundColor: theme.card }]}>
            <BarChart
              data={chartData}
              width={width - 64}
              height={200}
              yAxisLabel="₹"
              chartConfig={{
                backgroundColor: theme.card,
                backgroundGradientFrom: theme.card,
                backgroundGradientTo: theme.card,
                decimalPlaces: 0,
                color: (opacity = 1) => `rgba(99, 102, 241, ${opacity})`,
                labelColor: (opacity = 1) =>
                  isDark
                    ? `rgba(255, 255, 255, ${opacity})`
                    : `rgba(0, 31, 63, ${opacity})`,
                style: { borderRadius: 16 },
                barPercentage: 0.6,
              }}
              style={styles.chart}
              showValuesOnTopOfBars
              fromZero
            />
          </View>
        </View>
      )}

      {/* Empty State */}
      {quickStats.items?.length === 0 && spending.categories?.length === 0 && !aiSummary && (
        <View style={styles.section}>
          <View style={[styles.emptyCard, { backgroundColor: theme.card }]}>
            <Ionicons name="analytics-outline" size={48} color={theme.textSecondary} />
            <Text style={[styles.emptyTitle, { color: theme.text }]}>
              Koi data nahi hai
            </Text>
            <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
              Pehle transactions add karo, phir &ldquo;Naya Generate&rdquo; daba ke AI insights lo!
            </Text>
          </View>
        </View>
      )}

      <View style={styles.bottomPadding} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  centered: {
    justifyContent: "center",
    alignItems: "center",
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 12,
  },
  headerLeft: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: "700",
    letterSpacing: -0.5,
  },
  headerSubtitle: {
    fontSize: 13,
    marginTop: 2,
  },
  generateButton: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#001F3F",
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 20,
    gap: 6,
  },
  generateButtonDisabled: {
    opacity: 0.6,
  },
  generateButtonText: {
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: "600",
  },
  lastUpdatedText: {
    fontSize: 11,
    paddingHorizontal: 20,
    marginBottom: 16,
  },
  errorContainer: {
    flexDirection: "row",
    alignItems: "center",
    padding: 12,
    marginHorizontal: 20,
    marginBottom: 16,
    borderRadius: 8,
    gap: 8,
  },
  errorText: {
    color: "#F44336",
    fontSize: 13,
    flex: 1,
  },
  section: {
    paddingHorizontal: 20,
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: "600",
    marginBottom: 12,
  },
  sectionTotal: {
    fontSize: 17,
    fontWeight: "700",
  },
  // Summary Card
  summaryCard: {
    borderRadius: 16,
    padding: 20,
    alignItems: "center",
  },
  summaryEmoji: {
    fontSize: 32,
    marginBottom: 8,
  },
  summaryText: {
    fontSize: 15,
    textAlign: "center",
    lineHeight: 22,
  },
  aiTag: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 10,
    gap: 4,
  },
  aiTagText: {
    fontSize: 11,
    fontWeight: "600",
  },
  // Stats Grid
  statsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
  statCard: {
    width: (width - 56) / 2,
    padding: 14,
    borderRadius: 14,
    borderWidth: 1,
    marginBottom: 12,
  },
  statIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 8,
  },
  statLabel: {
    fontSize: 12,
    marginBottom: 4,
  },
  statValue: {
    fontSize: 20,
    fontWeight: "700",
  },
  statSub: {
    fontSize: 11,
    marginTop: 2,
  },
  // Spending Card
  spendingCard: {
    borderRadius: 14,
    padding: 16,
  },
  spendingRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: 0.5,
    borderBottomColor: "#E5E7EB",
  },
  spendingLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  spendingIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
  },
  spendingName: {
    fontSize: 14,
    fontWeight: "500",
  },
  spendingRight: {
    alignItems: "flex-end",
  },
  spendingAmount: {
    fontSize: 14,
    fontWeight: "600",
  },
  spendingPercent: {
    fontSize: 11,
    marginTop: 2,
  },
  // Goals Card
  goalsCard: {
    borderRadius: 14,
    padding: 16,
  },
  goalItem: {
    marginBottom: 16,
  },
  goalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  goalName: {
    fontSize: 14,
    fontWeight: "500",
  },
  goalProgress: {
    fontSize: 13,
    fontWeight: "600",
  },
  progressBarBg: {
    height: 8,
    borderRadius: 4,
    overflow: "hidden",
  },
  progressBarFill: {
    height: "100%",
    borderRadius: 4,
  },
  goalStatus: {
    fontSize: 12,
    marginTop: 6,
  },
  // Alert Card
  alertCard: {
    flexDirection: "row",
    alignItems: "center",
    padding: 14,
    borderRadius: 12,
    marginBottom: 10,
    gap: 10,
  },
  alertEmoji: {
    fontSize: 20,
  },
  alertText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 18,
  },
  // Insight Card
  insightWrapper: {
    marginBottom: 12,
  },
  insightCard: {
    flexDirection: "row",
    padding: 16,
    borderRadius: 14,
    alignItems: "flex-start",
    gap: 12,
  },
  insightEmoji: {
    fontSize: 24,
  },
  insightContent: {
    flex: 1,
  },
  insightTitle: {
    fontSize: 14,
    fontWeight: "600",
    marginBottom: 4,
  },
  insightDesc: {
    fontSize: 13,
    lineHeight: 18,
  },
  // Trend Card
  trendCard: {
    borderRadius: 14,
    padding: 16,
  },
  trendHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  trendEmoji: {
    fontSize: 32,
  },
  trendInfo: {
    flex: 1,
  },
  trendTitle: {
    fontSize: 15,
    fontWeight: "600",
    marginBottom: 4,
  },
  trendDesc: {
    fontSize: 13,
    lineHeight: 18,
  },
  // Chart Card
  chartCard: {
    borderRadius: 14,
    padding: 12,
    alignItems: "center",
  },
  chart: {
    borderRadius: 14,
  },
  // Empty State
  emptyCard: {
    padding: 32,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: "600",
  },
  emptyText: {
    fontSize: 13,
    textAlign: "center",
    lineHeight: 18,
  },
  bottomPadding: {
    height: 40,
  },
});
