import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { useRouter } from "expo-router";
import { useFocusEffect } from "@react-navigation/native";
import { useState, useCallback } from "react";
import {
  Dimensions,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  useColorScheme,
  View,
  ActivityIndicator,
  RefreshControl,
} from "react-native";
import { LineChart } from "react-native-chart-kit";
import { useDashboard } from "../../contexts/DashboardContext";

const { width } = Dimensions.get("window");

export default function Home() {
  const colorScheme = useColorScheme();
  const router = useRouter();
  const isDark = colorScheme === "dark";
  const { dashboardData, loadingDashboard, refreshDashboard } = useDashboard();

  const [refreshing, setRefreshing] = useState(false);

  // Quick Actions (static)
  const QUICK_ACTIONS = [
    {
      id: 1,
      icon: "flag-outline",
      label: "Add Goal",
      route: "/goals/add",
    },
    {
      id: 2,
      icon: "receipt-outline",
      label: "Add Transaction",
      route: "/(tabs)/transactions",
    },
    {
      id: 3,
      icon: "wallet-outline",
      label: "View All",
      route: "/(tabs)/transactions",
    },
  ];

  // Refresh when tab comes into focus without flashing loader
  useFocusEffect(
    useCallback(() => {
      refreshDashboard({ silent: true }).catch(() => {});
    }, [refreshDashboard])
  );

  // Pull to refresh
  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshDashboard({ silent: true });
    } finally {
      setRefreshing(false);
    }
  };

  // Helper to get transaction icon
  const getTransactionIcon = (category) => {
    const iconMap = {
      'Food': 'restaurant-outline',
      'Bills': 'flash-outline',
      'Shopping': 'cart-outline',
      'Travel': 'airplane-outline',
      'Subscriptions': 'card-outline',
      'Salary': 'cash-outline',
      'Freelance': 'briefcase-outline',
      'Investment': 'trending-up-outline',
      'Others': 'ellipsis-horizontal-outline',
    };
    return iconMap[category] || 'ellipsis-horizontal-outline';
  };

  const theme = {
    background: isDark ? "#0a0a0a" : "#F8F9FA",
    card: isDark ? "#1a1a1a" : "#FFFFFF",
    text: isDark ? "#FFFFFF" : "#001F3F",
    textSecondary: isDark ? "#A0A0A0" : "#6B7280",
    border: isDark ? "#2a2a2a" : "#E5E7EB",
    primary: "#001F3F",
    alert: "#FFF3E0",
    alertBorder: "#FF9800",
    alertText: isDark ? "#FFFFFF" : "#001F3F",
  };

  const showInitialLoader = loadingDashboard && !dashboardData;

  if (showInitialLoader) {
    return (
      <View style={[styles.container, styles.centerContent, { backgroundColor: theme.background }]}>
        <ActivityIndicator size="large" color={theme.primary} />
        <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
          Loading dashboard...
        </Text>
      </View>
    );
  }

  // Get data with defaults
  const balance = dashboardData?.balance || 0;
  const recentTransactions = dashboardData?.recent_transactions || [];
  const spendingOverview = dashboardData?.spending_overview || { labels: ["Week 1", "Week 2", "Week 3", "Week 4"], data: [0, 0, 0, 0], total: 0 };
  const aiInsight = dashboardData?.ai_insight || null;

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.background }]}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* -----------------------------
          HEADER
      ------------------------------ */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={[styles.logoCircle, { backgroundColor: theme.primary }]}>
            <Ionicons name="analytics" size={24} color="#FFFFFF" />
          </View>
          <View style={styles.headerText}>
            <Text style={[styles.appName, { color: theme.text }]}>
              Finweave AI
            </Text>
            <Text style={[styles.tagline, { color: theme.textSecondary }]}>
              Your money, made simple.
            </Text>
          </View>
        </View>

        <View style={styles.headerRight}>
          <TouchableOpacity
            style={styles.iconButton}
            onPress={() => router.push("/notifications")}
          >
            <Ionicons
              name="notifications-outline"
              size={24}
              color={theme.text}
            />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.iconButton}
            onPress={() => router.push("/(tabs)/profile")}
          >
            <Ionicons
              name="person-circle-outline"
              size={28}
              color={theme.text}
            />
          </TouchableOpacity>
        </View>
      </View>

      {/* -----------------------------
          BALANCE CARD
      ------------------------------ */}
      <LinearGradient
        colors={isDark ? ["#1a1a1a", "#2a2a2a"] : ["#001F3F", "#003d7a"]}
        style={styles.balanceCard}
      >
        <Text style={styles.balanceLabel}>Available Balance</Text>
        <Text style={styles.balanceAmount}>₹{balance.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</Text>
      </LinearGradient>

      {/* -----------------------------
          AI INSIGHT ALERT
      ------------------------------ */}
      {aiInsight && (
        <View
          style={[
            styles.alertCard,
            { 
              backgroundColor: aiInsight.severity === 'urgent' ? theme.alert : isDark ? "#1a3a1a" : "#E8F5E9",
              borderColor: aiInsight.severity === 'urgent' ? theme.alertBorder : "#4CAF50"
            },
          ]}
        >
          <View style={styles.alertHeader}>
            <Ionicons 
              name={aiInsight.severity === 'urgent' ? "warning" : "checkmark-circle"} 
              size={20} 
              color={aiInsight.severity === 'urgent' ? theme.alertBorder : "#4CAF50"} 
            />
            <Text style={[styles.alertTitle, { color: theme.alertText }]}>
              {aiInsight.title}
            </Text>
          </View>

          <Text style={[styles.alertMessage, { color: theme.alertText }]}>
            {aiInsight.message}
          </Text>
        </View>
      )}

      {/* -----------------------------
          QUICK ACTIONS
      ------------------------------ */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.text }]}>
          Quick Actions
        </Text>

        <View style={styles.quickActions}>
          {QUICK_ACTIONS.map((action) => (
            <TouchableOpacity
              key={action.id}
              style={[
                styles.actionButton,
                { backgroundColor: theme.card, borderColor: theme.border },
              ]}
              onPress={() => router.push(action.route)}
              activeOpacity={0.7}
            >
              <Ionicons name={action.icon} size={24} color={theme.primary} />
              <Text style={[styles.actionLabel, { color: theme.text }]}>
                {action.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* -----------------------------
          SPENDING CHART
      ------------------------------ */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.text }]}>
          Spending Overview — Last 30 Days
        </Text>

        <View style={[styles.chartCard, { backgroundColor: theme.card }]}>
          <LineChart
            data={{
              labels: spendingOverview.labels,
              datasets: [{ data: spendingOverview.data.length > 0 ? spendingOverview.data : [0, 0, 0, 0] }],
            }}
            width={width - 64}
            height={200}
            chartConfig={{
              backgroundColor: theme.card,
              backgroundGradientFrom: theme.card,
              backgroundGradientTo: theme.card,
              decimalPlaces: 0,
              color: (opacity = 1) => `rgba(0, 31, 63, ${opacity})`,
              labelColor: (opacity = 1) =>
                isDark
                  ? `rgba(255,255,255,${opacity})`
                  : `rgba(0,31,63,${opacity})`,
              style: { borderRadius: 16 },
              propsForDots: {
                r: "4",
                strokeWidth: "2",
                stroke: "#001F3F",
              },
            }}
            bezier
            style={styles.chart}
          />

          <View style={styles.totalSpend}>
            <Text
              style={[styles.totalSpendLabel, { color: theme.textSecondary }]}
            >
              Total Spend
            </Text>
            <Text style={[styles.totalSpendAmount, { color: theme.text }]}>
              ₹{spendingOverview.total?.toLocaleString('en-IN', { maximumFractionDigits: 2 }) || '0'}
            </Text>
          </View>
        </View>
      </View>

      {/* -----------------------------
          RECENT ACTIVITY
      ------------------------------ */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>
            Recent Activity
          </Text>

          <TouchableOpacity onPress={() => router.push("/(tabs)/transactions") }>
            <Text style={[styles.seeAll, { color: theme.primary }]}>
              See All →
            </Text>
          </TouchableOpacity>
        </View>

        <View
          style={[styles.transactionsCard, { backgroundColor: theme.card }]}
        >
          {recentTransactions.length > 0 ? (
            recentTransactions.map((t, index) => (
              <View key={t.id || index}>
                <View style={styles.transactionItem}>
                  <View
                    style={[
                      styles.transactionIcon,
                      { backgroundColor: isDark ? "#2a2a2a" : "#F8F9FA" },
                    ]}
                  >
                    <Ionicons
                      name={getTransactionIcon(t.category)}
                      size={20}
                      color={t.type === 'income' ? "#4CAF50" : theme.primary}
                    />
                  </View>

                  <View style={styles.transactionDetails}>
                    <Text style={[styles.transactionName, { color: theme.text }]}>
                      {t.name}
                    </Text>
                    <Text
                      style={[
                        styles.transactionCategory,
                        { color: theme.textSecondary },
                      ]}
                    >
                      {t.category}
                    </Text>
                  </View>

                  <Text
                    style={[
                      styles.transactionAmount,
                      { color: t.type === 'income' ? "#4CAF50" : theme.text },
                    ]}
                  >
                    {t.type === 'income' ? "+" : "-"}₹
                    {Math.abs(t.amount).toLocaleString('en-IN')}
                  </Text>
                </View>

                {index < recentTransactions.length - 1 && (
                  <View
                    style={[styles.divider, { backgroundColor: theme.border }]}
                  />
                )}
              </View>
            ))
          ) : (
            <View style={styles.emptyState}>
              <Ionicons name="receipt-outline" size={48} color={theme.textSecondary} />
              <Text style={[styles.emptyStateText, { color: theme.textSecondary }]}>
                No transactions yet
              </Text>
              <Text style={[styles.emptyStateSubtext, { color: theme.textSecondary }]}>
                Add your first transaction to get started
              </Text>
            </View>
          )}
        </View>
      </View>

      <View style={styles.bottomPadding} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },

  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
  },

  headerLeft: { flexDirection: "row", alignItems: "center", flex: 1 },

  logoCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },

  headerText: { flex: 1 },

  appName: { fontSize: 18, fontWeight: "700", letterSpacing: -0.3 },

  tagline: { fontSize: 12, marginTop: 2 },

  headerRight: { flexDirection: "row", alignItems: "center" },

  iconButton: { marginLeft: 16 },

  balanceCard: {
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 24,
    borderRadius: 16,
  },

  balanceLabel: { fontSize: 14, color: "#FFF", opacity: 0.9, marginBottom: 8 },

  balanceAmount: { fontSize: 36, fontWeight: "700", color: "#FFF" },

  alertCard: {
    marginHorizontal: 20,
    marginBottom: 24,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderLeftWidth: 4,
  },

  alertHeader: { flexDirection: "row", alignItems: "center", marginBottom: 8 },

  alertTitle: { fontSize: 14, fontWeight: "600", marginLeft: 8 },

  alertMessage: { fontSize: 13, lineHeight: 20 },

  section: { marginBottom: 24, paddingHorizontal: 20 },

  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 16,
  },

  sectionTitle: { fontSize: 18, fontWeight: "600", marginBottom: 16 },

  seeAll: { fontSize: 14, fontWeight: "600" },

  quickActions: { flexDirection: "row", justifyContent: "space-between" },

  actionButton: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 20,
    paddingHorizontal: 12,
    borderRadius: 12,
    marginHorizontal: 4,
    borderWidth: 1,
  },

  actionLabel: { fontSize: 12, fontWeight: "500", marginTop: 8 },

  chartCard: {
    borderRadius: 16,
    padding: 16,
  },

  chart: { marginVertical: 8, borderRadius: 16 },

  totalSpend: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: "#E5E7EB",
  },

  totalSpendLabel: { fontSize: 14 },

  totalSpendAmount: { fontSize: 20, fontWeight: "700" },

  transactionsCard: {
    borderRadius: 16,
    padding: 16,
  },

  transactionItem: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 12,
  },

  transactionIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },

  transactionDetails: { flex: 1 },

  transactionName: { fontSize: 15, fontWeight: "600", marginBottom: 4 },

  transactionCategory: { fontSize: 13 },

  transactionAmount: { fontSize: 16, fontWeight: "600" },

  divider: { height: 1, marginVertical: 4 },

  bottomPadding: { height: 40 },

  // Loading and empty states
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },

  loadingText: {
    marginTop: 12,
    fontSize: 14,
  },

  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },

  emptyStateText: {
    fontSize: 16,
    fontWeight: '600',
    marginTop: 12,
  },

  emptyStateSubtext: {
    fontSize: 14,
    marginTop: 4,
  },
});
