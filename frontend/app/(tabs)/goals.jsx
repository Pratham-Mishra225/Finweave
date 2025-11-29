import { Ionicons } from "@expo/vector-icons";
import { useRouter, useFocusEffect } from "expo-router";
import { useState, useCallback } from "react";
import {
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  useColorScheme,
  View,
  ActivityIndicator,
  RefreshControl,
  Alert,
  Modal,
  TextInput,
} from "react-native";
import { useAuth } from "../../contexts/AuthContext";

const API_BASE_URL = process.env.EXPO_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function Goals() {
  const colorScheme = useColorScheme();
  const router = useRouter();
  const { idToken } = useAuth();
  const isDark = colorScheme === "dark";

  // State
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);
  
  // Add to goal modal state
  const [addAmountModalVisible, setAddAmountModalVisible] = useState(false);
  const [selectedGoal, setSelectedGoal] = useState(null);
  const [addAmount, setAddAmount] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const theme = {
    background: isDark ? "#0a0a0a" : "#F8F9FA",
    card: isDark ? "#1a1a1a" : "#FFFFFF",
    text: isDark ? "#FFFFFF" : "#001F3F",
    textSecondary: isDark ? "#A0A0A0" : "#6B7280",
    border: isDark ? "#2a2a2a" : "#E5E7EB",
    primary: "#001F3F",
    progressBg: isDark ? "#2a2a2a" : "#E5E7EB",
    success: "#4CAF50",
    danger: "#EF4444",
    warning: "#FF9800",
    inputBg: isDark ? "#2a2a2a" : "#F3F4F6",
    modalBg: isDark ? "#1a1a1a" : "#FFFFFF",
  };

  const formatAmount = (amount) => `₹${Number(amount).toLocaleString("en-IN")}`;
  
  const getCategoryIcon = (category) => {
    const iconMap = {
      'Savings': 'wallet-outline',
      'Investment': 'trending-up-outline',
      'Purchase': 'cart-outline',
      'Travel': 'airplane-outline',
      'Education': 'school-outline',
      'Emergency': 'shield-checkmark-outline',
      'Debt': 'card-outline',
      'Other': 'ellipsis-horizontal-outline',
    };
    return iconMap[category] || 'flag-outline';
  };

  const getCategoryColor = (category) => {
    const colorMap = {
      'Savings': '#4CAF50',
      'Investment': '#2196F3',
      'Purchase': '#FF9800',
      'Travel': '#00BCD4',
      'Education': '#9C27B0',
      'Emergency': '#F44336',
      'Debt': '#795548',
      'Other': '#607D8B',
    };
    return colorMap[category] || theme.primary;
  };

  // Fetch goals from backend
  const fetchGoals = useCallback(async (isRefresh = false) => {
    if (!idToken) {
      setLoading(false);
      return;
    }

    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);

      // Fetch goals and summary in parallel
      const [goalsRes, summaryRes] = await Promise.all([
        fetch(`${API_BASE_URL}/goals`, {
          headers: {
            'Authorization': `Bearer ${idToken}`,
            'Content-Type': 'application/json',
          },
        }),
        fetch(`${API_BASE_URL}/goals/summary`, {
          headers: {
            'Authorization': `Bearer ${idToken}`,
            'Content-Type': 'application/json',
          },
        }),
      ]);

      if (!goalsRes.ok) {
        throw new Error('Failed to fetch goals');
      }

      const goalsData = await goalsRes.json();
      setGoals(goalsData);

      if (summaryRes.ok) {
        const summaryData = await summaryRes.json();
        setSummary(summaryData);
      }
    } catch (err) {
      console.error('Error fetching goals:', err);
      setError(err.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [idToken]);

  // Refetch on screen focus
  useFocusEffect(
    useCallback(() => {
      fetchGoals();
    }, [fetchGoals])
  );

  // Pull to refresh
  const onRefresh = () => {
    fetchGoals(true);
  };

  // Add amount to goal
  const handleAddAmount = async () => {
    if (!selectedGoal || !addAmount || isNaN(Number(addAmount))) {
      Alert.alert('Error', 'Please enter a valid amount');
      return;
    }

    try {
      setSubmitting(true);
      const response = await fetch(
        `${API_BASE_URL}/goals/${selectedGoal.id}/add?amount=${Number(addAmount)}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${idToken}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to add amount');
      }

      Alert.alert('Success', `Added ${formatAmount(addAmount)} to ${selectedGoal.title}`);
      setAddAmountModalVisible(false);
      setSelectedGoal(null);
      setAddAmount("");
      fetchGoals(true);
    } catch (err) {
      Alert.alert('Error', err.message);
    } finally {
      setSubmitting(false);
    }
  };

  // Delete goal
  const handleDeleteGoal = (goal) => {
    Alert.alert(
      'Delete Goal',
      `Are you sure you want to delete "${goal.title}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              const response = await fetch(`${API_BASE_URL}/goals/${goal.id}`, {
                method: 'DELETE',
                headers: {
                  'Authorization': `Bearer ${idToken}`,
                },
              });

              if (!response.ok) {
                throw new Error('Failed to delete goal');
              }

              fetchGoals(true);
            } catch (err) {
              Alert.alert('Error', err.message);
            }
          },
        },
      ]
    );
  };

  // Open add amount modal
  const openAddAmountModal = (goal) => {
    setSelectedGoal(goal);
    setAddAmount("");
    setAddAmountModalVisible(true);
  };

  // Render loading state
  if (loading) {
    return (
      <View style={[styles.container, styles.centerContent, { backgroundColor: theme.background }]}>
        <ActivityIndicator size="large" color={theme.primary} />
        <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
          Loading goals...
        </Text>
      </View>
    );
  }

  // Render error state
  if (error && goals.length === 0) {
    return (
      <View style={[styles.container, styles.centerContent, { backgroundColor: theme.background }]}>
        <Ionicons name="alert-circle-outline" size={48} color={theme.danger} />
        <Text style={[styles.errorText, { color: theme.text }]}>
          Failed to load goals
        </Text>
        <TouchableOpacity
          style={[styles.retryButton, { backgroundColor: theme.primary }]}
          onPress={() => fetchGoals()}
        >
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      {/* HEADER */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={[styles.headerTitle, { color: theme.text }]}>
            Your Goals
          </Text>
          <Text style={[styles.headerSubtitle, { color: theme.textSecondary }]}>
            Track your progress and stay motivated
          </Text>
        </View>

        <View
          style={[
            styles.headerIcon,
            { backgroundColor: isDark ? "#2a2a2a" : "#F0F1F3" },
          ]}
        >
          <Ionicons name="flag-outline" size={24} color={theme.primary} />
        </View>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={theme.primary}
          />
        }
      >
        {/* SUMMARY CARD */}
        {summary && (
          <View style={[styles.summaryCard, { backgroundColor: theme.card, borderColor: theme.border }]}>
            <View style={styles.summaryRow}>
              <View style={styles.summaryItem}>
                <Text style={[styles.summaryValue, { color: theme.primary }]}>
                  {summary.active_goals}
                </Text>
                <Text style={[styles.summaryLabel, { color: theme.textSecondary }]}>
                  Active
                </Text>
              </View>
              <View style={[styles.summaryDivider, { backgroundColor: theme.border }]} />
              <View style={styles.summaryItem}>
                <Text style={[styles.summaryValue, { color: theme.success }]}>
                  {summary.completed_goals}
                </Text>
                <Text style={[styles.summaryLabel, { color: theme.textSecondary }]}>
                  Completed
                </Text>
              </View>
              <View style={[styles.summaryDivider, { backgroundColor: theme.border }]} />
              <View style={styles.summaryItem}>
                <Text style={[styles.summaryValue, { color: theme.text }]}>
                  {summary.overall_progress}%
                </Text>
                <Text style={[styles.summaryLabel, { color: theme.textSecondary }]}>
                  Progress
                </Text>
              </View>
            </View>
            {summary.at_risk_count > 0 && (
              <View style={[styles.atRiskBanner, { backgroundColor: `${theme.warning}15` }]}>
                <Ionicons name="warning-outline" size={16} color={theme.warning} />
                <Text style={[styles.atRiskText, { color: theme.warning }]}>
                  {summary.at_risk_count} goal{summary.at_risk_count > 1 ? 's' : ''} at risk
                </Text>
              </View>
            )}
          </View>
        )}

        {/* EMPTY STATE */}
        {goals.length === 0 && (
          <View style={styles.emptyState}>
            <Ionicons
              name="flag-outline"
              size={46}
              color={theme.textSecondary}
            />
            <Text style={[styles.emptyTitle, { color: theme.text }]}>
              No goals yet
            </Text>
            <Text style={[styles.emptySubtitle, { color: theme.textSecondary }]}>
              Start by adding your first goal!
            </Text>
          </View>
        )}

        {/* GOAL CARDS */}
        <View style={styles.goalsContainer}>
          {goals.map((goal) => {
            const categoryColor = getCategoryColor(goal.category);
            const isOverdue = goal.is_overdue;
            const isCompleted = goal.status === 'completed';

            return (
              <View
                key={goal.id}
                style={[
                  styles.goalCard,
                  { 
                    backgroundColor: theme.card, 
                    borderColor: isOverdue ? theme.danger : theme.border,
                    opacity: isCompleted ? 0.8 : 1,
                  },
                ]}
              >
                {/* STATUS BADGE */}
                {(isOverdue || isCompleted) && (
                  <View 
                    style={[
                      styles.statusBadge, 
                      { backgroundColor: isCompleted ? theme.success : theme.danger }
                    ]}
                  >
                    <Text style={styles.statusBadgeText}>
                      {isCompleted ? 'COMPLETED' : 'OVERDUE'}
                    </Text>
                  </View>
                )}

                {/* HEADER */}
                <View style={styles.goalHeader}>
                  <View
                    style={[
                      styles.goalIconContainer,
                      { backgroundColor: `${categoryColor}15` },
                    ]}
                  >
                    <Ionicons
                      name={getCategoryIcon(goal.category)}
                      size={24}
                      color={categoryColor}
                    />
                  </View>

                  <View style={styles.goalInfo}>
                    <Text style={[styles.goalName, { color: theme.text }]}>
                      {goal.title}
                    </Text>
                    <Text style={[styles.goalTarget, { color: theme.textSecondary }]}>
                      Target: {formatAmount(goal.target_amount)}
                    </Text>
                    {goal.deadline && (
                      <Text style={[styles.goalTarget, { color: isOverdue ? theme.danger : theme.textSecondary }]}>
                        {isOverdue 
                          ? `Overdue by ${Math.abs(goal.days_remaining)} days`
                          : goal.days_remaining !== null 
                            ? `${goal.days_remaining} days remaining`
                            : `Deadline: ${goal.deadline}`
                        }
                      </Text>
                    )}
                  </View>

                  <View style={[styles.percentageBadge, { backgroundColor: `${categoryColor}15` }]}>
                    <Text style={[styles.percentageText, { color: categoryColor }]}>
                      {goal.progress_percentage}%
                    </Text>
                  </View>
                </View>

                {/* PROGRESS */}
                <View style={styles.goalProgress}>
                  <View style={styles.progressInfo}>
                    <Text style={[styles.savedLabel, { color: theme.textSecondary }]}>
                      Saved
                    </Text>
                    <Text style={[styles.savedAmount, { color: theme.text }]}>
                      {formatAmount(goal.saved_amount)}
                    </Text>
                  </View>

                  <View style={[styles.progressBarContainer, { backgroundColor: theme.progressBg }]}>
                    <View
                      style={[
                        styles.progressBarFill,
                        {
                          width: `${goal.progress_percentage}%`,
                          backgroundColor: categoryColor,
                        },
                      ]}
                    />
                  </View>

                  <Text style={[styles.remainingAmount, { color: theme.textSecondary }]}>
                    {formatAmount(goal.remaining_amount)} remaining
                  </Text>
                </View>

                {/* ACTION BUTTONS */}
                {!isCompleted && (
                  <View style={styles.actionButtons}>
                    <TouchableOpacity
                      style={[styles.actionButton, { backgroundColor: `${theme.success}15` }]}
                      onPress={() => openAddAmountModal(goal)}
                    >
                      <Ionicons name="add-circle-outline" size={18} color={theme.success} />
                      <Text style={[styles.actionButtonText, { color: theme.success }]}>
                        Add Savings
                      </Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                      style={[styles.actionButton, { backgroundColor: `${theme.danger}15` }]}
                      onPress={() => handleDeleteGoal(goal)}
                    >
                      <Ionicons name="trash-outline" size={18} color={theme.danger} />
                    </TouchableOpacity>
                  </View>
                )}
              </View>
            );
          })}
        </View>

        {/* ADD GOAL BUTTON */}
        <TouchableOpacity
          style={[styles.addButton, { backgroundColor: theme.primary }]}
          onPress={() => router.push("/goals/add")}
        >
          <Ionicons name="add-circle-outline" size={24} color="#fff" />
          <Text style={styles.addButtonText}>Add New Goal</Text>
        </TouchableOpacity>

        <View style={styles.bottomPadding} />
      </ScrollView>

      {/* ADD AMOUNT MODAL */}
      <Modal
        visible={addAmountModalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setAddAmountModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { backgroundColor: theme.modalBg }]}>
            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: theme.text }]}>
                Add to {selectedGoal?.title}
              </Text>
              <TouchableOpacity onPress={() => setAddAmountModalVisible(false)}>
                <Ionicons name="close" size={24} color={theme.text} />
              </TouchableOpacity>
            </View>

            {selectedGoal && (
              <View style={styles.modalGoalInfo}>
                <Text style={[styles.modalGoalText, { color: theme.textSecondary }]}>
                  Current: {formatAmount(selectedGoal.saved_amount)} / {formatAmount(selectedGoal.target_amount)}
                </Text>
                <View style={[styles.progressBarContainer, { backgroundColor: theme.progressBg, marginTop: 8 }]}>
                  <View
                    style={[
                      styles.progressBarFill,
                      {
                        width: `${selectedGoal.progress_percentage}%`,
                        backgroundColor: theme.primary,
                      },
                    ]}
                  />
                </View>
              </View>
            )}

            <View style={styles.amountInputContainer}>
              <Text style={[styles.currencySymbol, { color: theme.text }]}>₹</Text>
              <TextInput
                style={[styles.amountInput, { backgroundColor: theme.inputBg, color: theme.text }]}
                placeholder="Enter amount"
                placeholderTextColor={theme.textSecondary}
                keyboardType="numeric"
                value={addAmount}
                onChangeText={setAddAmount}
                autoFocus
              />
            </View>

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, { backgroundColor: theme.border }]}
                onPress={() => setAddAmountModalVisible(false)}
              >
                <Text style={[styles.modalButtonText, { color: theme.text }]}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, { backgroundColor: theme.primary }]}
                onPress={handleAddAmount}
                disabled={submitting}
              >
                {submitting ? (
                  <ActivityIndicator size="small" color="#fff" />
                ) : (
                  <Text style={[styles.modalButtonText, { color: "#fff" }]}>Add</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  centerContent: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
  },
  errorText: {
    marginTop: 12,
    fontSize: 18,
    fontWeight: '600',
  },
  retryButton: {
    marginTop: 16,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
  },
  headerLeft: { flex: 1 },
  headerTitle: { fontSize: 28, fontWeight: "700" },
  headerSubtitle: { fontSize: 14, marginTop: 2 },
  headerIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: "center",
    justifyContent: "center",
  },
  scrollView: { flex: 1 },
  scrollContent: { paddingHorizontal: 20 },
  
  // Summary Card
  summaryCard: {
    padding: 16,
    borderRadius: 16,
    borderWidth: 1,
    marginBottom: 20,
  },
  summaryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
  },
  summaryItem: {
    alignItems: 'center',
    flex: 1,
  },
  summaryValue: {
    fontSize: 24,
    fontWeight: '700',
  },
  summaryLabel: {
    fontSize: 12,
    marginTop: 4,
  },
  summaryDivider: {
    width: 1,
    height: 40,
  },
  atRiskBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  atRiskText: {
    marginLeft: 6,
    fontSize: 13,
    fontWeight: '500',
  },
  
  // Empty State
  emptyState: {
    padding: 40,
    alignItems: 'center',
  },
  emptyTitle: {
    marginTop: 16,
    fontSize: 18,
    fontWeight: '600',
  },
  emptySubtitle: {
    marginTop: 8,
  },
  
  // Goal Cards
  goalsContainer: { marginBottom: 24 },
  goalCard: {
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    marginBottom: 16,
    position: 'relative',
  },
  statusBadge: {
    position: 'absolute',
    top: 12,
    right: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  statusBadgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '700',
  },
  goalHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 16,
  },
  goalIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },
  goalInfo: { flex: 1 },
  goalName: { fontSize: 16, fontWeight: "600", marginBottom: 4 },
  goalTarget: { fontSize: 13 },
  percentageBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  percentageText: { fontSize: 14, fontWeight: "700" },
  goalProgress: { marginTop: 8 },
  progressInfo: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  savedLabel: { fontSize: 13 },
  savedAmount: { fontSize: 16, fontWeight: "700" },
  progressBarContainer: {
    height: 8,
    borderRadius: 4,
    overflow: "hidden",
    marginBottom: 8,
  },
  progressBarFill: { height: "100%" },
  remainingAmount: { fontSize: 12, textAlign: "right" },
  
  // Action Buttons
  actionButtons: {
    flexDirection: 'row',
    marginTop: 16,
    gap: 8,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  actionButtonText: {
    marginLeft: 6,
    fontSize: 13,
    fontWeight: '600',
  },
  
  // Add Button
  addButton: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    paddingVertical: 16,
    borderRadius: 12,
  },
  addButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
    marginLeft: 8,
  },
  bottomPadding: { height: 40 },
  
  // Modal
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
  },
  modalGoalInfo: {
    marginBottom: 20,
  },
  modalGoalText: {
    fontSize: 14,
  },
  amountInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
  },
  currencySymbol: {
    fontSize: 24,
    fontWeight: '600',
    marginRight: 8,
  },
  amountInput: {
    flex: 1,
    height: 56,
    borderRadius: 12,
    paddingHorizontal: 16,
    fontSize: 18,
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  modalButton: {
    flex: 1,
    height: 48,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
});
